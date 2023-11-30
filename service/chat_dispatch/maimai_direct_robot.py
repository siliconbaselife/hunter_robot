from .base_robot import BaseChatRobot, ChatStatus
from utils.config import config
from utils.log import get_logger
from utils.utils import format_time

from datetime import datetime
import json
from dao.task_dao import get_job_by_id
import traceback

from utils.gpt import GptChat

import time

import requests

logger = get_logger(config['log']['log_file'])

gpt_chat = GptChat()


class MaimaiDirectRobot(BaseChatRobot):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        super(MaimaiDirectRobot, self).__init__(robot_api, account_id, job_id, candidate_id, source)
        self._job_id = job_id
        job_config = json.loads(get_job_by_id(job_id)[0][6], strict=False)

        self._msg_list = []
        logger.info(f"maimai robot init job_id: {job_id}")

    def contact(self, page_history_msg, db_history_msg):
        logger.info(f"page_history_msg: {page_history_msg}")
        logger.info(f"db_history_msg: {db_history_msg}")
        try:
            history_msgs = self.prepare_msgs(page_history_msg, db_history_msg)
            if self.isFirstTask(history_msgs):
                intent_flag = self.has_intent(history_msgs)
                if intent_flag:
                    r_msg = self.send_positive_word()
                else:
                    r_msg = self.send_negtive_word()
                self.deal_r_msg(r_msg)
            else:
                self._status = ChatStatus.NoTalk
                self._next_msg = ""

        except BaseException as e:
            logger.error(e)
            logger.error(str(traceback.format_exc()))

    def send_positive_word(self):
        return "感谢您的回复。我这边的职位是一家能源行业垄断性质央企的一个在编岗位。方便约您时间咱们电话或者微信语音详细沟通一下吗？我会从职位背景、用人喜好、软性要求等角度和您详细沟通。"

    def send_negtive_word(self):
        return "不好意思打扰到您了，还是十分感谢您的回复，咱们保持联系。我这边的机会是能源行业垄断性质央企的一个在编岗位，如果您周围有朋友看机会麻烦帮忙介绍一下。这个机会对于35-40岁想要开辟新职业方向的朋友是个绝佳的上岸机会。"

    def deal_r_msg(self, r_msg):
        self._status = ChatStatus.NeedContact
        self._next_msg = r_msg
        self._next_msg = self._next_msg.replace('。', '。\n')
        self._msg_list.append({'speaker': 'robot', 'msg': self._next_msg, 'algo_judge_intent': 'chat',
                               'time': format_time(datetime.now())})

    def isFirstTask(self, history_msgs):
        flag = 0
        for msg in history_msgs:
            if msg["speaker"] == "user":
                flag = 1

            if msg["speaker"] == "system" and msg["msg"] == "我已通过了好友请求，以后多交流":
                flag = 1

            if msg["speaker"] == "robot" and flag == 1:
                return False

        return flag == 1

    def has_intent(self, history_msgs):
        msg_prompt = self.deal_intention_prompts(history_msgs)
        if len(msg_prompt) == 0:
            return

        result_msg = gpt_chat.generic_chat({"user_message": msg_prompt})

        if "A.不看机会" in result_msg:
            return False

        return True

    def deal_intention_prompts(self, history_msgs):
        msg_str = ""
        for msg in history_msgs:
            if msg["speaker"] == "system":
                continue
            msg_str += "我: " if msg["speaker"] == "robot" else "候选人: "
            msg_str += msg["msg"] + "\n"
        if len(msg_str) == 0:
            return ""

        prompt = f'''
        @@@
        {msg_str}
        @@@
        问题:
        假设你是一个猎头，判断上面对话，候选人是否看当前机会，一共3个选项。
        A.不看机会 B.看机会 C.未知
        写出推理过程，答案放在最后一行。
        '''

        return prompt

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
            r_new_msgs = []
            for msg in new_msgs:
                temp_time = msg['time'] if "time" in msg else None
                if temp_time is None:
                    temp_time = format_time(datetime.now())
                else:
                    temp_time = format_time(datetime.fromtimestamp(msg['time']))

                r_new_msgs.append({
                    'speaker': msg["speaker"],
                    'msg': msg["msg"],
                    'time': temp_time
                })

            history_msg.extend(r_new_msgs)
        else:
            history_msg = page_history_msg

        self._msg_list = history_msg
        logger.info(f"history_msg: {history_msg}")

        return history_msg
