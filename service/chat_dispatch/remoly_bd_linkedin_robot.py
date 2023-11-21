from .base_robot import BaseChatRobot, ChatStatus
import json

from dao.task_dao import get_job_by_id, query_status_infos, has_contact_db, update_candidate_contact_db, \
    update_status_infos, update_chat_contact_db
from utils.log import get_logger
from utils.config import config
from utils.utils import format_time
from datetime import datetime

from utils.gpt import GptChat

import traceback

import time

import requests

logger = get_logger(config['log']['log_file'])

gpt_chat = GptChat()

class RemolyBDLinkedinRobot(BaseChatRobot):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        super(RemolyBDLinkedinRobot, self).__init__(robot_api, account_id, job_id, candidate_id, source)
        self._job_id = job_id
        job_config = json.loads(get_job_by_id(job_id)[0][6], strict=False)

        self._msg_list = []
        logger.info(f"maimai robot init job_id: {job_id}")

    def contact(self, page_history_msg, db_history_msg):
        logger.info(f"page_history_msg: {page_history_msg}")
        logger.info(f"db_history_msg: {db_history_msg}")

        try:
            history_msgs = self.prepare_msgs(page_history_msg, db_history_msg)
            status_infos = self.fetch_now_status()
            logger.info(f"当前客户 {self._candidate_id} 的状态信息是 {status_infos}")

            self.deal_contact(history_msgs, status_infos)
            self.deal_intention(history_msgs, status_infos)
            self.deal_introduction(history_msgs, status_infos)

            logger.info(f"当前客户 {self._candidate_id} 的 status_infos: {status_infos}")

            r_msg, action = self.chat_to_ai(history_msgs, status_infos)
            self.deal_r_msg(r_msg, action)

            update_status_infos(self._candidate_id, self._account_id, json.dumps(status_infos, ensure_ascii=False))
            logger.info(f"需要返回给客户 {self._candidate_id} 的话术 '{self._next_msg}' 以及动作 {self._status}")
        except BaseException as e:
            logger.error(e)
            logger.error(str(traceback.format_exc()))

    def prepare_msgs(self, page_history_msg, db_history_msg):
        if db_history_msg is not None and len(db_history_msg) > 0:
            history_msg = db_history_msg

            new_msgs = []
            for i in range(len(page_history_msg)):
                if page_history_msg[len(page_history_msg) - i - 1]["speaker"] == "robot":
                    break
                new_msgs.append(page_history_msg[len(page_history_msg) - i - 1])
            logger.info(f"new_msgs: {new_msgs}")

            new_msgs.reverse()
            history_msg.extend(new_msgs)
        else:
            history_msg = page_history_msg

        self._msg_list = history_msg
        logger.info(f"history_msg: {history_msg}")

        return history_msg

    def fetch_now_status(self):
        res = query_status_infos(self._candidate_id, self._account_id)
        if len(res) == 0:
            return {}

        return json.loads(res[0][0], strict=False)

    def deal_contact(self, history_msgs, status_infos):
        if "contact_flag" in status_infos and status_infos["contact_flag"]:
            return True

        db_has_contact = has_contact_db(self._candidate_id, self._account_id)
        if db_has_contact:
            status_infos["contact_flag"] = True
            return True

        msg_prompt = self.deal_contact_prompts(history_msgs)
        result_msg = gpt_chat.generic_chat({"user_message": msg_prompt})

        contact_infos = self.parse_contact_msg_results(result_msg)
        if len(contact_infos.keys()) == 0:
            status_infos["contact_flag"] = False
            return False

        update_chat_contact_db(self._account_id, self._job_id, self._candidate_id, json.dumps(contact_infos))
        status_infos["contact_flag"] = True
        return True

    def deal_contact_prompts(self, page_history_msg):
        msg_str = ""
        for msg in page_history_msg:
            if msg["speaker"] == "system":
                continue
            msg_str += "me: " if msg["speaker"] == "robot" else "client: "
            msg_str += msg["msg"] + "\n"

        msg_prompt = f'''
@@@
{msg_str}
@@@
question:
Help me extract the client's phone number and WeChat, excluding my information.
The results are represented in JSON format, with 'phone' as the key for phone number, 'wechat' for wechat, 'email' for email, and 'whatsApp' for WhatsApp. Missing information is represented as null.
If there is no contact information for the client in the conversation, state that there is no contact information.
I don't need you to help me write code.
Response limited to 50 words or fewer.
        '''

        return msg_prompt