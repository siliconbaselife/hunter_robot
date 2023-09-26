from utils.config import config
from utils.log import  get_logger
from utils.utils import format_time

import requests
from datetime import datetime
from enum import Enum
import copy

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

class BaseChatRobot(object):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        self._sess_id = f'{account_id}_{job_id}_{candidate_id}'
        self._source = source
        self._robot_api = robot_api

        self._trivial_intent = config['chat']['trivial_intent']
        self._refuse_intent = config['chat']['refuse_intent']
        self._useless_msgs = [
            '对方想发送加密附件简历给您',
            '的微信号',
            '<copy>'
        ]
        self._preset_reply_dict = {
            'need_contact_on_refuse': [
                # '方便给我留一个联系方式么，我这里也有其他岗位可以推荐给您',
                # '您方便留下您的联系方式么？我这里还有其他岗位机会，可能会适合您。',
                '我做这个行业已经十几年了。可否留个联系方式，方便我向您推荐？',
                '如果您方便，能否留个联系方式？我可以经常给您同步下最新的招聘内容',
                # '能留下联系方式吗？我会帮您探索其他职位的机会，看看是否有合适的岗位适合您。',
                '您看是否方便留个联系方式, 我这边有很多top公司的资源，相信一定能帮助到您找到满意的岗位'
            ],
            'need_contact_normal': [
                # '咱能不能留个简历和联系方式呢',
                "方便加个微信或者告知联系方式，咱们细聊",
                "您方便留个联系方式么，我们可以详细沟通一下",
                # "您能否告诉我一个可以与您详细沟通的联系方式呢？",
                # "希望跟您进一步沟通一下，能否留下您的联系方式？",
                "可否告知一下您的联系方式，以便我们进行后续沟通？"
                # "我们想要邀请您参与进一步的面试流程，您方便留下联系方式？",
                # "为了更好地安排后续的步骤，您能否提供一个可以联系到您的方式？",
                # "您是否可以留下一个可以联系到您的号码？",
                # "您是否能够提供一个有效的联系方式，以便我们能够进一步交流？",
                # "您能将您的联系方式留一下么，我们好安排后续的面试流程。"
            ],
            'trivial_case': ['咱微信或者电话详聊吧'],
            'no_prompt_case': [
                "更具体的信息咱们电话详聊"
            ],
            'got_contact': [
                "好的，请问您什么时间方便",
                "好的，我加您细聊",
                "好,咱微信或者电话详聊吧",
                "好,我加您"
                # '我们这边hr稍后会跟您详细沟通', 
                # '好的，hr会跟您进一步沟通',
                # '谢谢。HR会尽快与您沟通，安排下一步的流程',
                # '我们hr会尽快跟您联系',
                # 'HR会尽快与您联络，来安排后续流程'
            ]
        }

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

    def contact(self, page_history_msg, db_history_msg):
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

        logger.info(f'base chat log {self._sess_id}: info: robot_api: {self._robot_api}, source: {self._source}; \
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
        self._init_msgs(page_history_msg, db_history_msg)

        ## analysis msgs
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
        chat_round = self._calc_chat_round()
        for cur in self._msg_list:
            if cur['speaker']=='system':
                has_contact = True
        return is_first_msg, has_system_msg, user_msg_useless, user_ask, chat_round, has_contact

    def _init_msgs(self, page_history_msg, db_history_msg):
        assert page_history_msg, f'page_history_msg empty {page_history_msg}'
        if page_history_msg[-1]['speaker']!='robot':
            logger.info(f"WARNING: _init_msgs got page history msg last speaker not user or system: {page_history_msg}")
        merge_user_msg = ''
        has_user_msg = False
        last_user_time = None
        ## find last user msg and system msg and parse results from msg
        parse_dict_list = []
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
            has_user_msg = True
            if last_user_time is None and 'time' in cur_item:
                last_user_time = format_time(datetime.fromtimestamp(cur_item['time']/1000))
            filter_msg, parse_dict = self._msg_filter(cur_item.get('msg', ''))
            parse_dict_list.append(parse_dict)
            merge_user_msg = filter_msg +'。'+ merge_user_msg
        if last_user_time is None:
            last_user_time = format_time(datetime.now())
        self._last_user_msg = merge_user_msg
        self._last_parse_list = parse_dict_list
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
            if has_user_msg:
                self._msg_list.append({
                    'speaker': 'user',
                    'msg': merge_user_msg,
                    'time': last_user_time
                })
            self._msg_list+= self._last_system_msgs

    def _calc_chat_round(self):
        chat_round = 0
        idx = 0
        while idx < len(self._msg_list):
            cur = self._msg_list[idx]
            if cur['speaker']=='user':
                chat_round +=1
                j = idx+1
                while j < len(self._msg_list):
                    until = self._msg_list[j]
                    if until['speaker']!='user':
                        break
                    j+=1
                idx = j
            else:
                idx+=1
        return chat_round

    def _is_no_prompt_case(self, model_response):
        return 'NB' in model_response

    def _manual_response(self, response_key):
        import random
        if response_key not in self._preset_reply_dict:
            return None
        cur_list = self._preset_reply_dict[response_key]
        rand_idx = random.randint(0,len(cur_list)-1)
        return cur_list[rand_idx]

    def _msg_filter(self, msg):
        dummy_parse_dict = {}
        for item in self._useless_msgs:
            if item in msg:
                return '', dummy_parse_dict
        if msg.find('[')<0 or msg.find(']')<0:
            return msg, dummy_parse_dict
        return msg[:msg.find('[')]+msg[msg.find(']')+1:], dummy_parse_dict

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