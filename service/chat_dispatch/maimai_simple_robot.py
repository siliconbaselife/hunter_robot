from .base_robot import BaseChatRobot, ChatStatus
from utils.config import config
from utils.log import  get_logger
from utils.utils import format_time

from datetime import datetime
import json
from dao.task_dao import get_job_by_id

logger = get_logger(config['log']['log_file'])

class MaimaiSimpleRobot(BaseChatRobot):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        super(MaimaiSimpleRobot, self).__init__(robot_api, account_id, job_id, candidate_id, source)
        job_config = json.loads(get_job_by_id(job_id)[0][6],strict=False)
        self._preset_reply_dict['hello'] = [job_config['touch_msg']]
        logger.info(f"maimai simple robot init, preset touch msg: {self._manual_response('hello')}")

    def contact(self, page_history_msg, db_history_msg):
        is_first_msg, has_system_msg, user_msg_useless, user_ask, chat_round, cur_has_contact, has_manual_touch = \
                self._preprocess(page_history_msg, db_history_msg)
        need_hello = chat_round==0 or (chat_round==1 and not has_manual_touch) 
        self._status = ChatStatus.NormalChat

        self._next_msg = self._manual_response('hello') if need_hello else ''
        ##增加换行，前端分多次发出
        self._next_msg = self._next_msg.replace('。','。\n')
        # self._next_msg = self._next_msg.replace('.','.\n')
        logger.info(f'maimai simple chat log {self._sess_id}: info: robot_api: {self._robot_api}, source: {self._source}; \
            tmp: system_msgs: {self._last_system_msgs}, user msgs: {self._last_user_msg}, user msg useless: {user_msg_useless}, \
            is_first: {is_first_msg}, user ask: {user_ask}, chat round: {chat_round}, cur has contact: {cur_has_contact}, has manual touch: {has_manual_touch} \
                            finally: {self._status}, {self._next_msg}')

        self._msg_list.append({
            'speaker':'robot', 'msg': self._next_msg, 'algo_judge_intent': None, 'time': format_time(datetime.now())
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

        cur_has_contact = False
        for parse_dict in self._last_parse_list:
            if 'contact' in parse_dict:
                cur_has_contact = True
                break
        chat_round = self._calc_chat_round()
        has_manual_touch = False
        for idx, cur in enumerate(self._msg_list):
            if cur['speaker']=='system' and '我已同意好友申请' in cur['msg']:
                if idx+1 < len(self._msg_list):
                    next_item = self._msg_list[idx+1]
                    if next_item['speaker']=='robot':
                        has_manual_touch = True
        return is_first_msg, has_system_msg, user_msg_useless, user_ask, chat_round, cur_has_contact, has_manual_touch
