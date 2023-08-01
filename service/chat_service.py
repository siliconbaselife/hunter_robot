import requests
from datetime import datetime
from enum import Enum

from utils.config import config
from utils.log import  get_logger
from utils.utils import format_time

logger = get_logger(config['log_file'])

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
        self._mock_apply_list = config['chat']['mock_preset']
        self._sess_id = sess_id
        # self._status = ChatStatus.from_str(last_status)
        # self._merge_history(page_history_msg, db_history_msg)
        self._source = source
        self._next_msg = None
        self._preset_reply_dict = config['chat']['preset_reply']
        self._trivial_reply_intent = config['chat']['trivial_reply_intent']
        self._robot_api = robot_api
        self._init_and_contact(page_history_msg, db_history_msg)
        logger.info(f"chat robot create for seeeion {sess_id}, robot_api: {self._robot_api}, source: {self._source}")

    def _init_and_contact(self, page_history_msg, db_history_msg):
        ## merge db history with page history. fetch latest msg. and judge:
        ### if user ask
        ### if first user say hello
        page_history_msg, self._last_user_msg, system_msgs = self._merge_last_user_msg(page_history_msg)
        if db_history_msg is None:
            self._msg_list = page_history_msg
        else:
            self._msg_list = db_history_msg
        hello_msg = False
        if len(self._msg_list)==0:
            hello_msg = True
        has_system_msg = len(system_msgs) > 0
        user_msg_useless = len(self._last_user_msg) ==0
        self._msg_list.append({
            'speaker': 'user', 'msg': self._last_user_msg
        })
        self._msg_list+= system_msgs
        if self._source is None:
            first_msg = self._msg_list[0]
            self._source = 'search'
            if first_msg['speaker']=='user':
                self._source = 'user_ask'
        user_ask = self._source=='user_ask'

        ## chat logic
        chat_round, has_contact = self._chat_ana()
        self._status = ChatStatus.NormalChat

        logger.info(f'chat log {self._sess_id}: info system_msgs: {system_msgs}, user msg useless: {user_msg_useless}, is_hello: {hello_msg}, user ask: {user_ask}, chat round: {chat_round}, has contact: {has_contact}')

        ### user ask and say hello, just reply and need contact
        algo_judge_intent = None
        if hello_msg and user_ask:
            self._next_msg = self._preset_reply_dict['need_contact']
            self._status= ChatStatus.NeedContact
            logger.info(f'chat log {self._sess_id}: reply user hello mode, ask for contact directly')
        elif has_system_msg:
            self._next_msg = self._preset_reply_dict['got_contact']
            logger.info(f'chat log {self._sess_id}: got user contact')
        elif user_msg_useless:
            if has_contact:
                logger.info(f'chat log {self._sess_id}: trivial case, intent: {algo_judge_intent}, has contact already, will no reply')
                self._next_msg = ''
            else:
                logger.info(f'chat log {self._sess_id}: trivial case, intent: {algo_judge_intent}, no contact yet, will ask for')
                self._status= ChatStatus.NeedContact
                self._next_msg = self._preset_reply_dict.get(self._status.value[0], '')
        else:
            contact_res = self._chat_request()
            if contact_res:
                self._next_msg, algo_judge_intent = contact_res
                # need_contact= True
                # if user_ask:
                #     need_contact = chat_round==1
                # else:
                need_contact = chat_round==3

                # if algo_judge_intent=='拒绝':
                #     self._status = ChatStatus.FinishFail
                #     self._next_msg = self._preset_reply_dict.get(self._status.value[0], '')
                #     logger.info(f'algo judge {self._sess_id} refuse, will finish')
                # elif '过激' in algo_judge_intent:
                #     self._status = ChatStatus.Dangerous
                #     self._next_msg = self._preset_reply_dict.get(self._status.value[0], '')
                #     logger.info(f'algo judge {self._sess_id} dangerous, will finish')
                # elif '感谢' in algo_judge_intent or '考虑' in algo_judge_intent or '确认' in algo_judge_intent or '无法判断' in algo_judge_intent:
                #     pass

                if algo_judge_intent in self._trivial_reply_intent:
                    if has_contact:
                        logger.info(f'chat log {self._sess_id}: trivial case, intent: {algo_judge_intent}, has contact already, will no reply')
                        self._next_msg = ''
                    else:
                        logger.info(f'chat log {self._sess_id}: trivial case, intent: {algo_judge_intent}, no contact yet, will ask for')
                        self._status= ChatStatus.NeedContact
                        self._next_msg = self._preset_reply_dict.get(self._status.value[0], '')
                elif need_contact:
                    self._status= ChatStatus.NeedContact
                    self._next_msg += '\n'
                    self._next_msg += self._preset_reply_dict.get(self._status.value[0], '')
            else:
                self._status = ChatStatus.AlgoAbnormal
                algo_judge_intent = 'algo_abnormal'


        logger.info(f'chat log {self._sess_id}: robot reaction: {self._status} {algo_judge_intent}: {self._next_msg}')       
        self._msg_list.append({
            'speaker':'robot', 'msg': self._next_msg, 'algo_judge_intent': algo_judge_intent
        })
            
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

    def _filter_useless(self, msg):
        if msg.find('[')<0 or msg.find(']')<0:
            return msg
        return msg[:msg.find('[')]+msg[msg.find(']')+1:]

    def _merge_last_user_msg(self, msg_list):
        assert msg_list and  msg_list[-1]['speaker']!='robot', f'msg list empty or last speaker not human: {msg_list}'
        merge_user_msg = ''
        system_msgs = []
        until_idx = len(msg_list)-1
        while until_idx>=0:
            cur_item = msg_list[until_idx]
            if cur_item['speaker']=='robot':
                break
            if cur_item['speaker']=='system':
                system_msgs.append(cur_item)
            merge_user_msg = self._filter_useless(cur_item['msg']) +'。'+ merge_user_msg
            until_idx-=1
        return msg_list[:until_idx+1], merge_user_msg, system_msgs

    def _chat_ana(self):
        has_contact = False
        round_cnt = 0
        for cur in self._msg_list:
            if cur['speaker']=='user':
                round_cnt+=1
            if cur['speaker']=='system':
                has_contact = True
        return round_cnt, has_contact

    def _chat_request(self):
        data = {
            "conversation_id": self._sess_id, # 对话id
            "message": self._last_user_msg, # 消息内容
            "message_time": format_time(datetime.now())
        }
        url = config['chat']['chat_url']
        url += self._robot_api
        response = requests.post(url=url, json=data)
        if response.status_code!=200 or response.json()['status']!=1:
            logger.info(f"request chat algo {url} failed, data: {data}, return {response.status_code} {response.text}")
            return None
        
        logger.info(f"session {self._sess_id} got response: {response.json()['data']}")
        return response.json()['data']['message'], response.json()['data']['last_message_intent']