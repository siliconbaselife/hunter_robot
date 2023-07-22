from chat_proxy import chat_contact
from enum import Enum
from config import config
from logger import  get_logger
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
    AlgoAbnormal = 'algo_abnormal'
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
    def __init__(self, robot_api, sess_id, last_status, page_history_msg, db_history_msg=None):
        self._mock = config['chat']['mock']
        self._mock_apply_list = config['chat']['mock_preset']
        self._sess_id = sess_id
        self._status = ChatStatus.from_str(last_status)
        self._merge_history(page_history_msg, db_history_msg)
        self._next_msg = None
        self._preset_reply_dict = config['chat']['preset_reply']
        self._robot_api = robot_api
        # if self._mock:
        #     logger.info(f'mock preset reply: {self._mock_apply_list}')
        # else:
        #     logger.info(f'normal preset reply: {self._preset_reply_dict}')
        self._init_and_contact()
        logger.info(f"chat robot create for seeeion {sess_id}, is mock: {self._mock}, robot_api: {self._robot_api}")

    def _init_and_contact(self):
        chat_round = self._chat_round()
        self._status = ChatStatus.NormalChat

        if self._mock:
            self._next_msg = self._mock_apply_list[chat_round%len(self._mock_apply_list)]
        else:
            if self._check_contact():
                self._status = ChatStatus.HasContact

            contact_res = chat_contact(self._robot_api, self._sess_id, self._last_user_msg)
            if contact_res:
                self._next_msg, algo_judge_intent = contact_res
                need_contact= True
                if self._user_ask:
                    need_contact = chat_round==1
                else:
                    need_contact= chat_round==3

                logger.info(f'normal mode: chat round: {chat_round}, user ask: {self._user_ask}, need contact: {need_contact}')

                if algo_judge_intent=='拒绝':
                    self._status = ChatStatus.FinishFail
                    logger.info(f'algo judge {self._sess_id} refuse, will finish')
                elif '过激' in algo_judge_intent:
                    self._status = ChatStatus.Dangerous
                    logger.info(f'algo judge {self._sess_id} dangerous, will finish')
                elif need_contact:
                    self._status= ChatStatus.NeedContact
                self._next_msg+= self._preset_reply_dict.get(self._status.value[0], '')
            else:
                self._status = ChatStatus.AlgoAbnormal
        logger.info(f'robot reaction: {self._status} {self._next_msg}')       
        self._msg_list.append({
            'speaker':'robot', 'msg': self._next_msg
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

    def _merge_last_user_msg(self, msg_list):
        assert msg_list and  msg_list[-1]['speaker']!='robot', f'msg list empty or last speaker not human: {msg_list}'
        merge_msg = msg_list[-1]['msg']
        until_idx = len(msg_list)-2
        while until_idx>=0:
            cur_item = msg_list[until_idx]
            if cur_item['speaker']=='robot':
                break
            merge_msg = cur_item['msg']+'。'+ merge_msg
            until_idx-=1
        return msg_list[:until_idx+1], merge_msg

    def _merge_history(self, page_history_msg, db_history_msg=None):
        page_history_msg, self._last_user_msg = self._merge_last_user_msg(page_history_msg)
        if db_history_msg is None:
            self._msg_list = page_history_msg
        else:
            self._msg_list = db_history_msg
        self._msg_list.append({
            'speaker': 'user', 'msg': self._last_user_msg
        })
        first_msg = self._msg_list[0]
        self._user_ask = False
        if first_msg['speaker']=='user':
            self._user_ask = True

    def _chat_round(self):
        round_cnt = 0
        for cur in self._msg_list:
            if cur['speaker']=='user':
                round_cnt+=1
        return round_cnt

    def _check_contact(self):
        pass
