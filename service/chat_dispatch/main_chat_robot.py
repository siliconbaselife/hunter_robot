from .base_robot import BaseChatRobot, ChatStatus
import json

from dao.task_dao import get_job_by_id, query_status_infos, has_contact_db, update_candidate_contact_db, \
    update_status_infos, update_chat_contact_db, query_template_config
from utils.log import get_logger
from utils.config import config
from utils.utils import format_time
from datetime import datetime

from utils.gpt import GptChat

import traceback

import time

from enum import Enum

import requests

logger = get_logger(config['log']['log_file'])

gpt_chat = GptChat()


class INTENTION(Enum):
    POSITIVE = 1
    NEGTIVE = 2
    QUESTIOM = 3
    NOINTENTION = 4


class MainChatRobot(BaseChatRobot):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        super(MainChatRobot, self).__init__(robot_api, account_id, job_id, candidate_id, source)
        self._job_id = job_id
        self.job_config = json.loads(get_job_by_id(job_id)[0][6], strict=False)
        self.template_id = get_job_by_id(job_id)[0][5]

        self._msg_list = []
        logger.info(f"maimai robot init job_id: {job_id}")

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

    def contact(self, page_history_msg, db_history_msg):
        logger.info(f"page_history_msg: {page_history_msg}")
        logger.info(f"db_history_msg: {db_history_msg}")
        try:
            history_msgs = self.prepare_msgs(page_history_msg, db_history_msg)
            status_infos = self.fetch_now_status()
            reply_infos = self.fetch_reply_infos()
            job_info = self.fetch_job_info()

            logger.info(f"当前客户 {self._candidate_id} 的状态信息是 {status_infos}")

            self.deal_contact(history_msgs, status_infos)
            intention = self.deal_intention(history_msgs, status_infos)
            r_msg, action = self.generate_reply(intention, status_infos, history_msgs, reply_infos, job_info)
            self.deal_r_msg(r_msg, action)

            update_status_infos(self._candidate_id, self._account_id, json.dumps(status_infos, ensure_ascii=False))
            logger.info(f"需要返回给客户 {self._candidate_id} 的话术 '{self._next_msg}' 以及动作 {self._status}")
        except BaseException as e:
            logger.error(e)
            logger.error(str(traceback.format_exc()))

    def fetch_job_info(self):
        rs = query_template_config(self.template_id)
        if len(rs) == 0:
            return {}

        return json.loads(rs[0][0])

    def fetch_reply_infos(self):
        return self.job_config["reply_infos"]

    def deal_r_msg(self, r_msg, action):
        self._status = action
        self._next_msg = r_msg
        self._next_msg = self._next_msg.replace('。', '。\n')
        self._msg_list.append({'speaker': 'robot', 'msg': self._next_msg, 'algo_judge_intent': 'chat',
                               'time': format_time(datetime.now())})

    def generate_reply(self, intention, status_infos, history_msgs, reply_infos, job_info):
        if intention == INTENTION.NEGTIVE:
            return self.negtive_reply(status_infos, reply_infos)

        if intention == INTENTION.POSITIVE:
            return self.positive_reply(status_infos, reply_infos)

        if intention == INTENTION.NOINTENTION:
            return self.no_intention_reply(status_infos, reply_infos, history_msgs, job_info)

        if intention == INTENTION.QUESTIOM:
            return self.deal_question_reply(status_infos, history_msgs, job_info)
        return "", ChatStatus.NoTalk

    def deal_question_reply(self, status_infos, history_msgs, job_info):
        prompt = f'''
你是一个猎头，你正在跟候选人聊这个岗位，回答候选人的问题。
不能说重复的话。
回复在50个字以内。
##
岗位要求:
{job_info["job_requirements"]}
岗位信息:
{job_info["job_description"]}
###
'''

        msgs, user_msg = self.transfer_msgs(history_msgs)
        r_msg = gpt_chat.generic_chat({"history_chat": msgs, "system_prompt": prompt, "user_message": user_msg})
        return r_msg, ChatStatus.NormalChat

    def no_intention_reply(self, status_infos, reply_infos, history_msgs, job_info):
        say_num = status_infos["say_num"] if "say_num" in status_infos else 0
        if "reply_msgs" in reply_infos and say_num < len(reply_infos["reply_msgs"]):
            status_infos["say_num"] = say_num + 1
            return reply_infos["reply_msgs"][say_num], ChatStatus.NormalChat

        m = ""
        if "contact_flag" in status_infos and status_infos["contact_flag"]:
            m = "找机会找候选人要联系方式, 要联系方式的话术是 我们加个微信细聊一下呗$PHONE$"
        prompt = f'''
你是一个猎头，你正在跟候选人聊这个岗位。
不能说重复的话术。
回答在30个字以内。
{m}
###
岗位要求:
{job_info["job_requirements"]}
岗位信息:
{job_info["job_description"]}
###
        '''

        msgs, user_msg = self.transfer_msgs(history_msgs)

        r_msg = gpt_chat.generic_chat({"history_chat": msgs, "system_prompt": prompt, "user_message": user_msg})
        if "$PHONE$" in r_msg:
            status_infos["contact_flag"] = True
            return r_msg.replace("$PHONE$", ""), ChatStatus.NeedContact
        else:
            return r_msg, ChatStatus.NormalChat

    def negtive_reply(self, status_infos, reply_infos):
        if "intention" in status_infos:
            status_infos["intention"] = False
            return "", ChatStatus.NoTalk

        if "intention" not in status_infos and "negtive_msg" in reply_infos:
            status_infos["intention"] = False
            status_infos["contact_flag"] = True
            return reply_infos["negtive_msg"], ChatStatus.NeedContact

        if "intention" not in status_infos and "negtive_msg" not in reply_infos:
            status_infos["intention"] = False
            status_infos["contact_flag"] = True
            negtive_msg = "我们加个微信呗，我手里有挺多岗位的，要是合适的推荐给您。", ChatStatus.NeedContact
            return negtive_msg, ChatStatus.NeedContact

    def positive_reply(self, status_infos, reply_infos):
        say_num = status_infos["say_num"] if "say_num" in status_infos else 0
        if "intention" in status_infos:
            status_infos["intention"] = True
            if "reply_msgs" in reply_infos and "reply_msgs" in reply_infos and say_num < len(reply_infos["reply_msgs"]):
                status_infos["say_num"] = say_num + 1
                return reply_infos["reply_msgs"][say_num], ChatStatus.NormalChat

        if "intention" not in status_infos and "positive_msg" in reply_infos:
            status_infos["intention"] = True
            status_infos["contact_flag"] = True
            return reply_infos["positive_msg"], ChatStatus.NeedContact

        if "intention" not in status_infos and "positive_msg" not in reply_infos:
            status_infos["intention"] = True
            status_infos["contact_flag"] = True
            positive_msg = "那我们加个微信细聊一下呗"
            return positive_msg, ChatStatus.NeedContact

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

    def parse_contact_msg_results(self, msg):
        if '{' not in msg or '}' not in msg:
            return {}

        json_str = msg[msg.index('{'): msg.index('}') + 1]
        contacts_raw = json.loads(json_str, strict=False)

        r_contacts = {}
        for key, value in contacts_raw.items():
            if value is None:
                continue
            r_contacts[key] = value

        return r_contacts

    def deal_contact_prompts(self, page_history_msg):
        msg_str = ""
        for msg in page_history_msg:
            if msg["speaker"] == "system":
                continue
            msg_str += "我: " if msg["speaker"] == "robot" else "客户: "
            msg_str += msg["msg"] + "\n"

        msg_prompt = f'''
@@@
{msg_str}
@@@
问: 
帮我萃取出客户的电话号码和微信号，排除掉我的信息。
结果用json格式表示，电话的key是phone，微信的key是wechat，获取不到的信息为null。
如果对话中没有客户的联系方式，就说没有联系方式。
我不需要你帮我写程序
回答限制在50个字以内
'''

        return msg_prompt

    def transfer_msgs(self, history_msgs):
        user_msg_list = []
        num = 1
        for i in range(len(history_msgs)):
            logger.info(f"{i} msg: {history_msgs[len(history_msgs) - i - 1]}")
            if history_msgs[len(history_msgs) - i - 1]["speaker"] == "system":
                if "好友请求" in history_msgs[len(history_msgs) - i - 1]["msg"]:
                    num += 1
                    user_msg_list.append("hi")
                continue

            if history_msgs[len(history_msgs) - i - 1]["speaker"] == "robot":
                break

            num += 1
            user_msg_list.append(history_msgs[len(history_msgs) - i - 1]["msg"])
        user_msg_list.reverse()
        user_msg = "\n".join(user_msg_list)
        logger.info(f"user_msg: {user_msg}")

        if num == 1:
            num += 1

        r_msgs = []
        for msg in history_msgs[: -(num - 1)]:
            if msg["speaker"] == "system":
                continue

            r_msgs.append({
                "role": msg["speaker"],
                "msg": msg["msg"]
            })

        return r_msgs, user_msg

    def fetch_now_status(self):
        res = query_status_infos(self._candidate_id, self._account_id)
        if len(res) == 0:
            return {}

        return json.loads(res[0][0], strict=False)

    def deal_intention(self, history_msgs, status_infos):
        msg_prompt = self.deal_intention_prompts(history_msgs)
        if len(msg_prompt) == 0:
            return INTENTION.NOINTENTION

        result_msg = gpt_chat.generic_chat({"user_message": msg_prompt})

        now_time = time.time()
        if "A.拒绝" in result_msg:
            return INTENTION.NEGTIVE

        if "B.肯定" in result_msg:
            return INTENTION.POSITIVE

        if "C.问岗位相关信息" in result_msg:
            return INTENTION.QUESTIOM

        if "D.没有任何意图" in result_msg:
            return INTENTION.NOINTENTION

        return INTENTION.NOINTENTION

    def deal_intention_prompts(self, history_msgs):
        msg_str = ""
        new_str = ""
        new_msgs = []
        end_num = 0
        for i in range(len(history_msgs)):
            if history_msgs[len(history_msgs) - i]["speaker"] == "system":
                continue

            if history_msgs[len(history_msgs) - i]["speaker"] == "robot":
                end_num = len(history_msgs) - i
                break

            if history_msgs[len(history_msgs) - i]["speaker"] == "user":
                new_msgs.append("候选人: " + history_msgs[len(history_msgs) - i].msg)
        new_msgs.reverse()
        new_str = "\n".join(new_msgs)

        for i in range(len(history_msgs)):
            if i > end_num:
                break

            msg = history_msgs[i]
            if msg["speaker"] == "system":
                continue
            msg_str += "我: " if msg["speaker"] == "robot" else "候选人: "
            msg_str += msg["msg"] + "\n"

        if len(msg_str) == 0:
            return ""

        if len(new_str) == 0:
            return ""

        prompt = f'''
你是一个猎头，判断一下，下面的对话，用户最后一段对话的意图。
历史对话在分隔符###里面，候选人最后一段对话在@@@里面
A.拒绝 B.肯定 C.问岗位相关信息 D.没有任何意图
###
{msg_str}
###
@@@
{new_str}
@@@
'''

        return prompt
