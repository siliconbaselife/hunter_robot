from chat_proxy import chat_contact
from utils import fetch_last_user_msg
from enum import Enum

class ChatStatus(Enum):
    Init = 'init',
    NormalChat = 'normal_chat',
    NeedContact = 'need_contact',
    HasContact = 'has_contact',
    NeedEnsure = 'need_ensure',
    FinishSuc = 'finish_suc',
    FinishFail = 'finish_fail',
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
        if status==ChatStatus.HasContact and status==ChatStatus.AlgoAbnormal:
            return 'normal_chat'
        elif status==ChatStatus.FinishSuc or status==ChatStatus.FinishFail:
            return 'finish'
        return status.value[0]


class ChatRobot(object):
    def __init__(self, sess_id, history_msg, last_status, mock=False):
        self._mock = mock
        self._sess_id = sess_id
        self._status = ChatStatus.from_str(last_status)
        self._msg_list = history_msg
        self._next_msg = None
        self._init_and_contact()

    def _init_and_contact(self):
        chat_round = self._chat_round()
        self._status = ChatStatus.NormalChat

        if self._mock:
            mock_ret_list = ["十分感谢我们这边的职位", "您的问题我们已经记录了，确认好了之后给您回复", "祝您生活愉快"]
            self._next_msg = mock_ret_list[chat_round%len(mock_ret_list)]
        else:
            last_user_msg = self._fetch_last_user_msg()
            if self._check_contact():
                self._status = ChatStatus.HasContact

            contact_res = chat_contact(self._sess_id, last_user_msg)
            if contact_res:
                self._next_msg, algo_judge_intent = contact_res
                if algo_judge_intent=='refuse':
                    self._status = ChatStatus.FinishFail
                    self._next_msg+= '\n谢谢您的投递'
                    return
                if chat_round >=5:
                    self._status= ChatStatus.NeedContact
                    self._next_msg+= '\n方便留一下您的手机号么'
                    return
            else:
                self._next_msg = '您好，请稍等'
                self._status = ChatStatus.AlgoAbnormal
                
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

    def _fetch_last_user_msg(self):
        msg_list = self._msg_list
        assert msg_list and  msg_list[-1]['speaker']!='robot', f'msg list empty or last speaker not human: {msg_list}'
        merge_msg = msg_list[-1]['msg']
        until_idx = len(msg_list)-2
        while until_idx>0:
            cur_item = msg_list[until_idx]
            if cur_item['speaker']=='robot':
                break
            merge_msg = cur_item['msg']+ merge_msg
            until_idx-=1
        return merge_msg


    def _chat_round(self):
        round_cnt = 0
        for cur in self._msg_list:
            if cur['speaker']=='robot':
                round+=1
        return round_cnt

    def _check_contact(self):
        pass