from .base_robot import BaseChatRobot, ChatStatus
import json

from dao.task_dao import get_job_by_id, query_status_infos, has_contact_db, update_candidate_contact_db
from utils.log import get_logger
from utils.config import config
from utils.utils import format_time
from datetime import datetime

import time

import requests

logger = get_logger(config['log']['log_file'])


class RemolyBDMaimaiRobot(BaseChatRobot):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        super(RemolyBDMaimaiRobot, self).__init__(robot_api, account_id, job_id, candidate_id, source)
        self._job_id = job_id
        job_config = json.loads(get_job_by_id(job_id)[0][6], strict=False)

        self._msg_list = []
        logger.info(f"maimai robot init job_id: {job_id}")

    def contact(self, page_history_msg, db_history_msg):
        history_msgs = self.prepare_msgs(page_history_msg, db_history_msg)

        status_infos = self.fetch_now_status()
        logger.info(f"当前客户 {self._candidate_id} 的状态信息是 {status_infos}")

        self.deal_contact(history_msgs, status_infos)
        self.deal_intention(history_msgs, status_infos)
        self.deal_introduction(history_msgs, status_infos)

        logger.info(f"当前客户 {self._candidate_id} 的 status_infos: {status_infos}")

        r_msg, action = self.chat_to_ai(history_msgs, status_infos)
        self.deal_r_msg(r_msg, action)

        logger.info(f"需要返回给客户 {self._candidate_id} 的话术 '{self._next_msg}' 以及动作 {self._status}")

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

        msg_prompt = f'''
{msg_str}
问: 萃取出客户的电话号码和微信号，排除掉我的信息，结果用json格式表示，电话的key是phone，微信的key是wechat，没有获取到的信息为null
'''

        return msg_prompt

    def parse_contact_msg_results(self, msg):
        if '{' not in msg or '}' not in msg:
            return {}

        json_str = msg[msg.index_of('{'): msg.index_of('}') + 1]

        return json.loads(json_str)

    def deal_contact(self, history_msgs, status_infos):
        if "contact_flag" in status_infos and status_infos["contact_flag"]:
            return True

        db_has_contact = has_contact_db(self._candidate_id, self._account_id)
        if db_has_contact:
            status_infos["contact_flag"] = True
            return True

        msg_prompt = self.deal_contact_prompts(history_msgs)
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

    def deal_intention(self, history_msgs, status_infos):
        if not self.check_need_intention(status_infos):
            return

        msg_prompt = self.deal_intention_prompts(history_msgs)

        result_msg = self.chat_gpt_request({
            "history_chat": [],
            "system_prompt": msg_prompt,
            "user_message": ""
        })

        now_time = time.time()
        if "A.有需求" in result_msg:
            status_infos["intention_flag"] = {"intention": "有需求", "time": now_time}

        if "B.没有需求" in result_msg:
            status_infos["intention_flag"] = {"intention": "没有需求", "time": now_time}

        if "C.暂时没有需求" in result_msg:
            status_infos["intention_flag"] = {"intention": "暂时没有需求", "time": now_time}

        if "D.无法判断" in result_msg:
            status_infos["intention_flag"] = {"intention": "无法判断", "time": now_time}

    def deal_intention_prompts(self, history_msgs):
        msg_str = ""
        for msg in history_msgs:
            if msg["speaker"] == "system":
                continue
            msg_str += "我: " if msg["speaker"] == "robot" else "客户: "
            msg_str += msg["msg"] + "\n"

        prompt = f'''
{msg_str}
问题:
假设你是一个销售人员，判断上面对话，客户最终对业务产品是什么意图，一共4个选项。
A.有需求 B.没有需求 C.暂时没有需求 D.无法判断
如果客户显示的说有没有需求，都是无法判断。
写出推理过程，答案放在最后一行。
'''

        return prompt

    def check_need_intention(self, status_infos):
        if "intention_flag" not in status_infos:
            return True

        intention = status_infos["intention_flag"]["intention"]
        if intention == "需要":
            return False

        intention_time = status_infos["intention_flag"]["time"]
        now_time = time.time()

        if now_time - intention_time > 3600 * 24 * 7:
            return True

        return False

    def deal_introduction(self, page_history_msg, status_infos):
        if "introduction_flag" in status_infos:
            return True

        now_time = time.time()
        for msg in page_history_msg:
            if msg["speaker"] == "system":
                continue

            if msg["speaker"] == "user":
                continue

            if "我是remoly" in msg["msg"]:
                status_infos["introduction_flag"] = {"introduction_flag": True, "time": now_time}
                return True

        return False

    def chat_to_ai(self, history_msgs, flag_infos):
        prompt = self.generate_prompt(flag_infos)
        msgs, user_msg = self.transfer_msgs(history_msgs)
        r_msg = self.chat_to_gpt(prompt, msgs, user_msg)
        say_msg, action = self.transfer_r_msg(r_msg)
        return say_msg, action

    def prepare_msgs(self, page_history_msg, db_history_msg):
        if db_history_msg is not None and len(db_history_msg) > 0:
            history_msg = db_history_msg

            new_msgs = []
            for i in range(len(page_history_msg)):
                if page_history_msg[len(page_history_msg) - i].speaker == "user":
                    break
                new_msgs.append(page_history_msg[len(page_history_msg) - i])

            new_msgs.reverse()
            history_msg.extends(new_msgs)
        else:
            history_msg = page_history_msg

        self._msg_list = history_msg
        return history_msg

    def transfer_r_msg(self, msg):
        if '$PHONE$' in msg:
            msg = msg.replace('$PHONE$', '')
            return msg, ChatStatus.NeedContact

        return msg, ChatStatus.NormalChat

    def generate_prompt(self, flag_infos):
        if not flag_infos["contact_flag"]:
            m1 = "你要想办法要客户的联系方式，微信，电话等，并给出特殊字符$PHONE$。"
        else:
            m1 = ""

        if not flag_infos["contact_flag"]:
            m2 = "我们海外业务挺多的，能给我联系方式吗？看后面有没有可以合作的地方$PHONE$"
        else:
            m2 = "我们海外业务挺多的，如果后面需要，麻烦联系我呢。"

        if not flag_infos["contact_flag"]:
            m3 = "能给个微信或者电话吗?我们细聊一下$PHONE$"
        else:
            m3 = "我们微信上面细聊吧"

        if "introduction_flag" not in flag_infos["introduction_flag"]:
            m4 = '用户打招呼(你好，hi)。回答"我是remoly的bd，我们做全球的EOR、招聘以及payroll，你们公司有相关需求吗"。'
        else:
            m4 = "用户打招呼(你好，hi)。询问对方公司最近是否有新的海外人力方面的需求。"

        prompt = f'''
            你是remoly公司的销售，别人会问你一些公司业务相关的信息。remoly公司可以做全球的EOR(跨境员工挂靠)，全球的招聘，全球的工作签证，全球payroll(跨境转账)。在全球大部分国家都有实体公司。
            {m1}
            不能说自己是AI或者是虚拟助手。
            尽量推销自己的产品和业务。
            所有的回答尽量在30个字以内，30个字以内，最多不能超过50个字。
            不要说重复的话。
            你是一个很稳重又很有礼貌的人。
            用户问的问题:
               用户表现出拒绝的意图，说"暂时不需要"，"不需要"，"现在不需要"等话术，你需要回复"{m2}"
               用户表现出需要的意图，你需要回复"{m3}"
               用户问签证可不可以办理。回答"可以办理"。
               用户问在有没有实体公司。回答"有实体公司"。
               用户问在本地有没有团队。回答"有团队"。
               用户问可不可以做招聘服务。回答"可以"。
               用户问相关业务报价。回答"具体情况微信上我给你发个excel，我们微信细聊"。
               {m4}
               用户问联系方式。回答"我电话和微信是18611747979"。
               问任何跟国家相关的。都回答"可以"
        '''

        return prompt

    def transfer_msgs(self, page_history_msg):
        user_msg_list = []
        num = 0
        for i in range(len(page_history_msg)):
            num += 1
            if page_history_msg[len(page_history_msg) - i]["speaker"] == "system":
                continue
            if page_history_msg[len(page_history_msg) - i]["speaker"] == "robot":
                break
            user_msg_list.append(page_history_msg[len(page_history_msg) - i]["msg"])
        user_msg_list.reverse()
        user_msg = "\n".join(user_msg_list)

        if num == 1:
            num += 1

        r_msgs = []
        for msg in page_history_msg[: -(num - 1)]:
            if msg["speaker"] == "system":
                continue

            r_msgs.append(msg)

        return r_msgs, user_msg

    def chat_to_gpt(self, prompt, msgs, user_msg):
        result_msg = self.chat_gpt_request({
            "history_chat": msgs,
            "system_prompt": prompt,
            "user_message": user_msg
        })

        return result_msg

    def deal_r_msg(self, r_msg, action):
        self._status = action
        self._next_msg = r_msg
        self._next_msg = self._next_msg.replace('。', '。\n')
        self._msg_list.append({'speaker': 'robot', 'msg': self._next_msg, 'algo_judge_intent': 'chat',
                               'time': format_time(datetime.now())})

    def chat_gpt_request(self, data):
        response = requests.post(url=self._robot_api, json=data, timeout=30)
        if response.status_code != 200 or response.json()['status'] != 1:
            logger.info(
                f"request chat algo {self._robot_api} failed, data: {data}, return {response.status_code} {response.text}")
            return None

        logger.info(f"session {self._sess_id} request {self._last_user_msg} got response: {response.json()['data']}")
        return response.json()['data']['message']
