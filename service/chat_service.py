import requests
from datetime import datetime
from enum import Enum
import copy
from utils.config import config
from utils.log import  get_logger
from utils.utils import format_time

logger = get_logger(config['log']['log_file'])

class ChatStatus(Enum):
    Init = 'init',
    NormalChat = 'normal_chat',
    NeedContact = 'need_contact',
    HasContact = 'has_contact',
    NeedEnsure = 'need_ensure',
    FinishSuc = 'finish_suc',
    FinishFail = 'finish_fail',
    Dangerous = 'dangerous',
    AlgoAbnormal = 'algo_abnormal',
    Unknown = 100

    @staticmethod
    def from_str(str_status):
        for item in ChatStatus:
            if item.value[0]==str_status:
                return item
        return ChatStatus.Unknown
    @staticmethod
    def response_str(status):
        if status==ChatStatus.HasContact:
            return 'normal_chat'
        elif status==ChatStatus.FinishSuc or status==ChatStatus.FinishFail or status==ChatStatus.Dangerous:
            return 'finish'
        return status.value[0]


class ChatRobot(object):
    def __init__(self, robot_api, sess_id, page_history_msg, db_history_msg=None, source=None):
        self._sess_id = sess_id
        # self._status = ChatStatus.from_str(last_status)
        # self._merge_history(page_history_msg, db_history_msg)
        self._source = source
        self._preset_reply_dict = config['chat']['preset_reply']
        self._trivial_intent = config['chat']['trivial_intent']
        self._refuse_intent = config['chat']['refuse_intent']
        self._robot_api = robot_api
        self._init_and_contact(page_history_msg, db_history_msg)
            
    @property
    def msg_list(self):
        return self._msg_list

    @property
    def next_step(self):
        return ChatStatus.response_str(self._status)

    @property
    def next_msg(self):
        return self._next_msg

    @property
    def status(self):
        return self._status.value[0]

    @property
    def source(self):
        return self._source


    def _init_and_contact(self, page_history_msg, db_history_msg):
        ## merge db history with page history. fetch latest msg. and judge:
        ### if user ask
        ### if first user say hello
        ### if has system msg
        ### if user send useless msg(expression)
        ### calc chat round
        is_first_msg, has_system_msg, user_msg_useless, user_ask, chat_round, has_contact = self._preprocess(page_history_msg, db_history_msg)
        need_contact = (not has_contact) and (is_first_msg if user_ask else chat_round==1)
        need_use_model = not user_msg_useless
        self._status = ChatStatus.NormalChat

        ### user ask and say hello, just reply and need contact
        model_response = None
        contact_res = None
        model_judge_intent = None
        is_trivial_intent = False
        is_refuse_intent = False
        is_no_prompt = False

        if need_use_model:
            contact_res = self._chat_request()
        if contact_res:
            model_response, model_judge_intent = contact_res
            is_trivial_intent = model_judge_intent in self._trivial_intent
            is_refuse_intent = model_judge_intent in self._refuse_intent
            is_no_prompt = self._is_no_prompt_case(model_response)

        to_cover_response = user_msg_useless or is_trivial_intent or is_refuse_intent or is_no_prompt

        strategy_response = None
        if need_contact:
            self._status= ChatStatus.NeedContact
            if is_refuse_intent:
                strategy_response = self._manual_response('need_contact_on_refuse')
            else:
                strategy_response = self._manual_response('need_contact_normal')
        else:
            if has_system_msg:
                strategy_response = self._manual_response('got_contact')
            elif is_trivial_intent or is_refuse_intent or user_msg_useless:
                strategy_response = self._manual_response('trivial_case')
            elif is_no_prompt:
                strategy_response = self._manual_response('no_prompt_case')
        if need_use_model and contact_res is None:
            self._status = ChatStatus.AlgoAbnormal
            model_judge_intent = 'algo_abnormal'

        self._next_msg = model_response if model_response is not None else ''
        if to_cover_response:
            self._next_msg = strategy_response if strategy_response is not None else ''
        else:
            if len(self._next_msg)>0:
                self._next_msg+= '\n'
            self._next_msg += strategy_response if strategy_response is not None else ''

        logger.info(f'chat log {self._sess_id}: info: robot_api: {self._robot_api}, source: {self._source}; \
            tmp: system_msgs: {self._last_system_msgs}, user msgs: {self._last_user_msg}, user msg useless: {user_msg_useless}, \
            is_first: {is_first_msg}, user ask: {user_ask}, chat round: {chat_round}, has contact: {has_contact}, \
                need contact: {need_contact}, need user algo: {need_use_model}, algo intent: {model_judge_intent},  \
                    is no prompt: {is_no_prompt}, is trivial: {is_trivial_intent}, is refuse: {is_refuse_intent}, to cover: {to_cover_response}, \
                        model response: {model_response}, strategy response: {strategy_response}; \
                            finally: {self._status}, {self._next_msg}')

        self._msg_list.append({
            'speaker':'robot', 'msg': self._next_msg, 'algo_judge_intent': model_judge_intent, 'time': format_time(datetime.now())
        })

    def _preprocess(self, page_history_msg, db_history_msg):
        assert page_history_msg and page_history_msg[-1]['speaker']!='robot', f'page_history_msg empty or last speaker not user: {page_history_msg}'
        merge_user_msg = ''
        last_user_time = None
        ## find last user msg and system msg
        system_msgs = []
        until_idx = len(page_history_msg)-1
        while until_idx>=0:
            cur_item = page_history_msg[until_idx]
            until_idx-=1
            if cur_item['speaker']=='robot':
                break
            if cur_item['speaker']=='system':
                system_msgs.append(copy.deepcopy(cur_item))
                continue
            if last_user_time is None and 'time' in cur_item:
                last_user_time = format_time(datetime.fromtimestamp(cur_item['time']/1000))
            merge_user_msg = self._filter_useless(cur_item.get('msg', '')) +'。'+ merge_user_msg
        if last_user_time is None:
            last_user_time = format_time(datetime.now())
        self._last_user_msg = merge_user_msg
        ## ensure time for system msgs
        for item in system_msgs:
            if 'time' in item:
                item['time'] = format_time(datetime.fromtimestamp(item['time']/1000))
            else:
                item['time'] = last_user_time
        self._last_system_msgs = system_msgs
        ## ensure time for whole page msgs
        for item in page_history_msg:
            if 'time' in item:
                # logger.info(f".......................page item: {item}, time: {item['time']}")
                item['time'] = format_time(datetime.fromtimestamp(item['time']/1000))
            else:
                item['time'] = format_time(datetime.now())

        if db_history_msg is None:
            self._msg_list = page_history_msg
        else:
            self._msg_list = db_history_msg
            # append_msgs = self._get_append_msgs(page_history_msg, db_history_msg)
            # logger.info(f'chat log {self._sess_id}: echo append msgs: {append_msgs}')
            # self._msg_list += append_msgs
            self._msg_list.append({
                'speaker': 'user',
                'msg': merge_user_msg,
                'time': last_user_time
            })
            self._msg_list+= self._last_system_msgs

        ## analysis msgs
        # hello_msg = False
        # if len(self._msg_list)==0:
        #     hello_msg = True
        is_first_msg = db_history_msg is None
        has_system_msg = len(self._last_system_msgs) > 0
        user_msg_useless = len(self._last_user_msg) ==0
        if self._source is None:
            first_msg = self._msg_list[0]
            self._source = 'search'
            if first_msg['speaker']!='robot':
                self._source = 'user_ask'
        user_ask = self._source=='user_ask'

        has_contact = False
        chat_round = 0
        for cur in self._msg_list:
            if cur['speaker']=='user':
                chat_round += 1
            if cur['speaker']=='system':
                has_contact = True
        return is_first_msg, has_system_msg, user_msg_useless, user_ask, chat_round, has_contact

    def _get_append_msgs(self, page_history_msg, db_history_msg):
        assert db_history_msg is not None and len(db_history_msg) >0 and page_history_msg and len(page_history_msg)>0
        win_size = 3 
        if len(db_history_msg) < win_size or len(page_history_msg) < win_size:
            win_size = min(len(db_history_msg), len(page_history_msg))

        until_idx = len(page_history_msg)
        find_match = False
        while until_idx >=win_size:
            is_match = True
            for idx in range(-1, -1-win_size, -1):
                # logger.info(f'page len {len(page_history_msg)}, until {until_idx}, cur iter {idx}, db len {len(db_history_msg)}')
                if page_history_msg[until_idx+idx]['speaker']==db_history_msg[idx]['speaker'] and\
                    page_history_msg[until_idx+idx].get('msg', None)== db_history_msg[idx].get('msg',None):
                    continue
                is_match = False
                break
            if is_match:
                find_match = True
                break
            until_idx-=1
        assert find_match, f"page {page_history_msg} no match to db {db_history_msg}, pleask check"
        return page_history_msg[until_idx:]


    def _is_no_prompt_case(self, model_response):
        return 'NB' in model_response

    def _manual_response(self, response_key):
        import random
        if response_key not in self._preset_reply_dict:
            return None
        cur_list = self._preset_reply_dict[response_key]
        rand_idx = random.randint(0,len(cur_list)-1)
        return cur_list[rand_idx]

    def _filter_useless(self, msg):
        ## TODO if system msg in user msg
        if msg.find('[')<0 or msg.find(']')<0:
            return msg
        return msg[:msg.find('[')]+msg[msg.find(']')+1:]

    def _chat_request(self):
        data = {
            "conversation_id": self._sess_id, # 对话id
            "message": self._last_user_msg, # 消息内容
            "message_time": format_time(datetime.now())
        }
        url = config['chat']['chat_url']
        url += self._robot_api
        response = requests.post(url=url, json=data, timeout=30)
        if response.status_code!=200 or response.json()['status']!=1:
            logger.info(f"request chat algo {url} failed, data: {data}, return {response.status_code} {response.text}")
            return None
        
        logger.info(f"session {self._sess_id} request {self._last_user_msg} got response: {response.json()['data']}")
        return response.json()['data']['message'], response.json()['data']['last_message_intent']
