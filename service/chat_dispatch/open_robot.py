from .base_robot import BaseChatRobot, ChatStatus
from utils.config import config
from utils.log import  get_logger
from utils.utils import format_time

from datetime import datetime
import json
from dao.task_dao import get_job_by_id

logger = get_logger(config['log']['log_file'])

class OpenChatRobot(BaseChatRobot):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        super(OpenChatRobot, self).__init__(robot_api, account_id, job_id, candidate_id, source)
        job_config = json.loads(get_job_by_id(job_id)[0][6],strict=False)
        self._preset_reply_dict['hello'] = [job_config['touch_msg']]
        logger.info(f"open chat robot init, preset touch msg: {self._manual_response('hello')}")

    def contact(self, page_history_msg, db_history_msg):
        chat_round = self._preprocess(page_history_msg, db_history_msg)
        need_hello = chat_round==0
        self._status = ChatStatus.NormalChat

        if need_hello:
            self._next_msg = self._manual_response('hello')
        else:
            contact_res = self._chat_request()
            model_response, model_judge_intent = contact_res
            self._next_msg = model_response

        logger.info(f'open chat log {self._sess_id}: info: robot_api: {self._robot_api}, chat round: {chat_round}, \
            model response: {model_response}, model_judge_intent: {model_judge_intent},\
              finally: {self._status}, {self._next_msg}')

        self._msg_list.append({
            'speaker':'robot', 'msg': self._next_msg, 'algo_judge_intent': model_judge_intent, 'time': format_time(datetime.now())
        })


    def _preprocess(self, page_history_msg, db_history_msg):
        self._init_msgs(page_history_msg, db_history_msg)

        ## analysis msgs
        if self._source is None:
            self._source = 'search'

        chat_round = self._calc_chat_round()
        return chat_round

    def _msg_filter(self, msg):
        return msg, {}