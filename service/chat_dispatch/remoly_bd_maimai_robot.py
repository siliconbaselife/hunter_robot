from .base_robot import BaseChatRobot
import json

from dao.task_dao import get_job_by_id, query_status_infos, has_contact_db, update_candidate_contact_db
from utils.log import get_logger
from utils.config import config

import requests

logger = get_logger(config['log']['log_file'])


class RemolyBDMaimaiRobot(BaseChatRobot):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        super(RemolyBDMaimaiRobot, self).__init__(robot_api, account_id, job_id, candidate_id, source)
        self._job_id = job_id
        job_config = json.loads(get_job_by_id(job_id)[0][6], strict=False)
        logger.info(f"maimai robot init job_id: {job_id}")

    def contact(self, page_history_msg, db_history_msg):
        status_infos = self.fetch_now_status()
        logger.info(f"当前客户 {self._candidate_id} 的状态信息是 {status_infos}")

        contact_flag = self.deal_contact(page_history_msg, status_infos)
        intention_flag = self.deal_intention(page_history_msg, status_infos)
        introduction_flag = self.deal_introduction(page_history_msg, status_infos)
        flag_infos = {
            "contact": contact_flag,
            "intention": intention_flag,
            "introduction": introduction_flag
        }

        logger.info(f"当前客户 {self._candidate_id} 的 flag_infos: {flag_infos}")

        r_msg = self.chat_to_ai(page_history_msg, flag_infos)
        send_msg, action = self.deal_r_msg(r_msg)

        logger.info(f"需要返回给客户 {self._candidate_id} 的话术 '{send_msg}' 以及动作 {action}")

    def fetch_now_status(self):
        res = query_status_infos(self._account_id, self._candidate_id)
        if len(res) == 0:
            return {}

        return json.loads(res[0])

    def deal_contact_prompts(self, page_history_msg):
        msg_str = ""
        for msg in page_history_msg:
            if msg["speaker"] == "system":
                continue
            msg_str += "我: " if msg["speaker"] == "robot" else "客户: "
            msg_str += msg["msg"] + "\n"

        msg_prompt = f"'''\n{msg_str}\n'''\n问: 萃取出客户的电话号码和微信号，排除掉我的信息，结果用json格式表示，电话的key是phone，微信的key是wechat，没有获取到的信息为null"
        return msg_prompt

    def parse_contact_msg_results(self, msg):
        if '{' not in msg or '}' not in msg:
            return {}

        json_str = msg[msg.index_of('{'): msg.index_of('}') + 1]

        return json.loads(json_str)

    def deal_contact(self, page_history_msg, status_infos):
        if "contact_flag" in status_infos and status_infos["contact_flag"]:
            return True

        db_has_contact = has_contact_db(self._candidate_id, self._account_id)
        if db_has_contact:
            status_infos["contact_flag"] = True
            return True

        msg_prompt = self.deal_contact_prompts(page_history_msg)
        result_msg = self.chat_gpt_request({
            "history_chat": [],
            "system_prompt": msg_prompt,
            "user_message": ""
        })

        contact_infos = self.parse_contact_msg_results(result_msg)
        if len(contact_infos.keys()) == 0:
            status_infos["contact_flag"] = False
            return False

        update_candidate_contact_db(self._candidate_id, contact_infos)
        status_infos["contact_flag"] = True
        return True

    def deal_intention(self, page_history_msg, status_infos):
        return None

    def deal_introduction(self, page_history_msg, status_infos):
        return None

    def chat_to_ai(self, page_history_msg, flag_infos):
        prompt = self.generate_prompt(flag_infos)
        msgs = self.transfer_msgs(page_history_msg)
        r_msg = self.chat_to_gpt(prompt, msgs)
        return r_msg

    def generate_prompt(self, flag_infos):
        return None

    def transfer_msgs(self, page_history_msg):
        return None

    def chat_to_gpt(self, prompt, msgs):
        return None

    def deal_r_msg(self, r_msg):
        return None

    def chat_gpt_request(self, data):
        response = requests.post(url=self._robot_api, json=data, timeout=30)
        if response.status_code != 200 or response.json()['status'] != 1:
            logger.info(
                f"request chat algo {self._robot_api} failed, data: {data}, return {response.status_code} {response.text}")
            return None

        logger.info(f"session {self._sess_id} request {self._last_user_msg} got response: {response.json()['data']}")
        return response.json()['data']['message']
