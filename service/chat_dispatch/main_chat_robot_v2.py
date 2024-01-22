from .base_robot import BaseChatRobot, ChatStatus
import json

from dao.task_dao import get_job_by_id, query_status_infos_v2, has_contact_db, update_candidate_contact_db, \
    update_status_infos_v2, update_chat_contact_db, query_template_config, get_template_id, query_chat_db
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


class MainChatRobotV2(BaseChatRobot):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        super(MainChatRobotV2, self).__init__(robot_api, account_id, job_id, candidate_id, source)
        self._job_id = job_id
        self.job_config = json.loads(get_job_by_id(job_id)[0][6], strict=False)
        self.platform = get_job_by_id(job_id)[0][1]
        self.template_id = get_template_id(job_id)[0][0]
        self._status_infos = self.fetch_now_status()
        self._reply_infos = self.fetch_reply_infos()
        self._template_info = self.fetch_template_info()
        self._msg_list = []

        logger.info(f'MainChatRobotV2, {candidate_id}, {job_id}, {self._status_infos}, {self.template_id}, {self._reply_infos}, {self.job_config}')

    def _parse_face(self, msg):
        for item in self._useless_msgs:
            if item in msg:
                return ''
        if msg.find('[')<0 or msg.find(']')<0:
            return msg
        return msg[:msg.find('[')]+msg[msg.find(']')+1:]

    def prepare_msgs(self, page_history_msg, db_history_msg):
        if db_history_msg is not None and len(db_history_msg) > 0:
            history_msg = db_history_msg
            new_msgs = []
            #这里其实做的不完善，有一致性问题，可以后面看是否真有这类case，先不改
            for i in range(len(page_history_msg)):
                if page_history_msg[len(page_history_msg) - i - 1]["speaker"] == "robot":
                    break
                new_msgs.append(page_history_msg[len(page_history_msg) - i - 1])
            # logger.info(f"MainChatRobotV2_new_msgs: {new_msgs}")
            new_msgs.reverse()
            r_new_msgs = []
            for msg in new_msgs:
                temp_time = msg['time'] if "time" in msg else None
                if temp_time is None:
                    temp_time = format_time(datetime.now())
                else:
                    try:
                        temp_time = format_time(datetime.fromtimestamp(msg['time']))
                    except BaseException as e:
                        logger.info(f'MainChatRobotV2,{self._candidate_id}, {e}, {e.args}, {traceback.format_exc()}')
                        temp_time = format_time(datetime.now())

                r_new_msgs.append({
                    'speaker': msg["speaker"],
                    'msg': self._parse_face(msg["msg"]),
                    'time': temp_time
                })

            history_msg.extend(r_new_msgs)
        else:
            history_msg = page_history_msg

        self._msg_list = history_msg
        logger.info(f"MainChatRobotV2_prepared_msg:{self._candidate_id}, {self._job_id}, {history_msg}")
        return history_msg

    def contact(self, page_history_msg, db_history_msg):
        logger.info(f"MainChatRobotV2_page_history_msg: {self._candidate_id}, {self._job_id}, {page_history_msg}")
        logger.info(f"MainChatRobotV2_db_history_msg:{self._candidate_id}, {self._job_id}, {db_history_msg}")
        try:
            processed_history_msgs = self.prepare_msgs(page_history_msg, db_history_msg)
            logger.info(f"MainChatRobotV2处理前 {self._candidate_id} 的状态信息是 {self._status_infos}")
            self.deal_contact(processed_history_msgs)
            intention = self.deal_intention(processed_history_msgs)
            if has_contact_db(self._candidate_id, self._account_id):
                self._status_infos['has_contact'] = True
            r_msg, action = self.generate_reply(intention, processed_history_msgs)
            self.deal_r_msg(r_msg, action)
            logger.info(f"MainChatRobotV2处理后 {self._candidate_id} 的状态信息是 {self._status_infos}")
            update_status_infos_v2(self._candidate_id, self._account_id, json.dumps(self._status_infos, ensure_ascii=False), self._job_id)
            logger.info(f"MainChatRobotV2需要返回给客户 {self._candidate_id} 的话术 '{self._next_msg}' 以及动作 {self._status}")
        except BaseException as e:
            logger.info(f'MainChatRobotV2,{self._candidate_id}, {e}, {e.args}, {traceback.format_exc()}')

    def fetch_template_info(self):
        rs = query_template_config(self.template_id)
        if len(rs) == 0:
            return {}
        return json.loads(rs[0][0])

    def fetch_reply_infos(self):
        return self.job_config.get("reply_infos", {})

    def fetch_now_status(self):
        res = query_status_infos_v2(self._candidate_id, self._account_id, self._job_id)
        if len(res) == 0:
            status_info = {}
        if res[0][0] is None or res[0][0] == 'NULL' or res[0][0] == 'Null':
            status_info = {}
        else:
            status_info = json.loads(res[0][0], strict=False)
        if status_info is None:
            status_info = {}
        if 'has_contact' not in status_info:
            status_info['has_contact'] = False
        if 'ask_contact' not in status_info:
            status_info['ask_contact'] = False
        if 'sent_first_msg' not in status_info:
            status_info['sent_first_msg'] = False
        if 'neg_intention' not in status_info:
            status_info['neg_intention'] = False
        if 'ask_rount' not in status_info:
            status_info['ask_rount'] = 0
        return status_info

    def deal_r_msg(self, r_msg, action):
        self._status = action
        self._next_msg = r_msg
        self._msg_list.append({'speaker': 'robot', 'msg': self._next_msg, 'algo_judge_intent': 'chat',
                               'time': format_time(datetime.now())})
        # self._next_msg = self._next_msg.replace('。', '。\n')
        
    def generate_reply(self, intention, history_msgs):
        if not self._status_infos["sent_first_msg"]:
            self._status_infos["sent_first_msg"] = True
            return self.first_reply(intention)
        if intention == INTENTION.NEGTIVE:
            return self.negtive_reply()
        if intention == INTENTION.POSITIVE:
            return self.positive_reply()
        if intention == INTENTION.NOINTENTION:
            return self.no_intention_reply(history_msgs)
        if intention == INTENTION.QUESTIOM:
            return self.deal_question_reply(history_msgs)
        return "", ChatStatus.NoTalk

    def first_reply(self, intention):
        self._status_infos['ask_contact'] = True
        if self._status_infos['has_contact']:
            return '', ChatStatus.NoTalk
        if intention == INTENTION.NEGTIVE:
            if self.platform == 'Linkedin':
                return "Would you mind leaving your email? When there's a new job opening on my end, I can share it with you right away.", ChatStatus.NeedContact
            else:
                return "您看方便留个电话或者微信吗，我这边有新的岗位也可以第一时间给您分享", ChatStatus.NeedContact
        else:
            if self.platform == 'Linkedin':
                return "Hello, would it be convenient to leave a contact information for us to discuss further?", ChatStatus.NeedContact
            else:
                return '您好，方便留个联系方式咱细聊下吗?', ChatStatus.NeedContact

    def deal_question_reply(self, history_msgs):
        if self.platform == 'Linkedin':
            prefix = '请用英语回答问题。一定要用英语回答。一定要用英语回答。一定要用英语回答。'
        else:
            prefix = ''
        prompt = f'''
{prefix}
你是一个猎头，你正在跟候选人推荐一个岗位，简洁回答候选人的问题。
不要说之前重复的话
不要用敬语
不要问用户问题
不要说类似“有什么可以帮您”的话术
回复在50个字以内。回复在50个字以内。
##
岗位要求:
{self._template_info["job_requirements"]}
岗位信息:
{self._template_info["job_description"]}
###
'''
        msgs, user_msg = self.transfer_msgs(history_msgs)
        r_msg = gpt_chat.generic_chat({"history_chat": msgs, "system_prompt": prompt, "user_message": user_msg})

        if not self._status_infos['has_contact']:
            if self.platform == 'Linkedin':
                r_msg += '\nHow about leaving an email? I can provide you with a detailed introduction.'
            else:
                r_msg += '\n您看要不加个微信，我给您详细介绍下'
        return r_msg, ChatStatus.NormalChat

    def no_intention_reply(self, history_msgs):
        if self._status_infos['has_contact']:
            return '', ChatStatus.NoTalk
        m = "找机会找候选人要联系方式, $PHONE$"
        if self.platform == 'Linkedin':
            prefix = '请用英语回答问题。一定要用英语回答。一定要用英语回答。一定要用英语回答。'
        else:
            prefix = ''
        prompt = f'''
{prefix}
你是一个猎头，你正在跟候选人推荐一个岗位，简洁回答候选人的问题
不要说之前重复的话
不要用敬语
不要问用户问题
不要说类似“有什么可以帮您”的话术
回答在30个字以内。回答在30个字以内。
{m}
###
岗位要求:
{self._template_info["job_requirements"]}
岗位信息:
{self._template_info["job_description"]}
###
        '''
        msgs, user_msg = self.transfer_msgs(history_msgs)
        r_msg = gpt_chat.generic_chat({"history_chat": msgs, "system_prompt": prompt, "user_message": user_msg})
        return r_msg.replace("$PHONE$", ""), ChatStatus.NormalChat

    def negtive_reply(self):
        if self._status_infos['has_contact']:
            return "", ChatStatus.NoTalk
        else:
            if not self._status_infos["neg_intention"]:
                self._status_infos["neg_intention"] = True
                if self.platform == 'Linkedin':
                    return "I have a variety of job opportunities, and if there's a good fit, I can recommend them to you at any time.", ChatStatus.NormalChat
                else:
                    return "咱也可以加个微信呗，我手里有挺多岗位的，要是合适的随时推荐给您。", ChatStatus.NormalChat
            else:
                return "", ChatStatus.NoTalk

    def positive_reply(self):
        if self._status_infos['has_contact']:
            return "", ChatStatus.NoTalk
        else:
            if self.platform == 'Linkedin':
                msgs = ["Could we correspond via email?"]
            else:
                msgs = [
                    "那我们加个微信细聊一下呗",
                    "您看方便的话咱可以微信上说，还方便"
                ]
            ask_round = self._status_infos['ask_round']
            if ask_round >= len(msgs):
                return "", ChatStatus.NormalChat
            self._status_infos['ask_round'] = ask_round + 1
            return msgs[ask_round], ChatStatus.NormalChat

    def _parse_msgs_contact(self, history_msgs):
        contact = ''
        for msg in history_msgs:
            if msg['speaker'] == 'user':
                filter_msg, parse_dict = self._parse_contact(msg['msg'])
                msg['msg'] = filter_msg
                if 'contact' in parse_dict and parse_dict['contact'] != '':
                    return parse_dict['contact']
        return contact

    def deal_contact_chi(self, history_msgs):
        if "contact_flag" in self._status_infos and self._status_infos["contact_flag"]:
            logger.info(f'MainChatRobotV2 already_have_contact, {self._candidate_id}')
            return True

        db_has_contact = has_contact_db(self._candidate_id, self._account_id)
        if db_has_contact:
            logger.info(f'MainChatRobotV2 already_have_contact, {self._candidate_id}')
            self._status_infos["contact_flag"] = True
            return True
        #这里等于有了一种联系方式就没再进行萃取了，直接return了
        contact = self._parse_msgs_contact(history_msgs)
        if contact == '':
            self._status_infos["contact_flag"] = False
            return False
        contact_info = {
            "wechat":contact,
            "phone":"",
            "cv":""
        }
        update_chat_contact_db(self._account_id, self._job_id, self._candidate_id, json.dumps(contact_info))
        self._status_infos["contact_flag"] = True
        return True
    
    def deal_contact_eng(self, history_msgs):
        if "contact_flag" in self._status_infos and self._status_infos["contact_flag"]:
            return True

        db_has_contact = has_contact_db(self._candidate_id, self._account_id)
        if db_has_contact:
            self._status_infos["contact_flag"] = True
            return True

        msg_prompt = self.deal_contact_prompts(history_msgs)
        result_msg = gpt_chat.generic_chat({"user_message": msg_prompt})

        contact_infos = self.parse_contact_msg_results(result_msg)
        if len(contact_infos.keys()) == 0:
            self._status_infos["contact_flag"] = False
            return False

        update_chat_contact_db(self._account_id, self._job_id, self._candidate_id, json.dumps(contact_infos))
        self._status_infos["contact_flag"] = True
        return True

    def deal_contact(self, history_msgs):
        if self.platform == 'Linkedin':
            return self.deal_contact_eng(history_msgs)
        else:
            return self.deal_contact_chi(history_msgs)

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

    
    def transfer_msgs(self, history_msgs):
        user_msg_list = []
        num = 1
        for i in range(len(history_msgs)):
            logger.info(f"MainChatRobotV2  {i} msg: {history_msgs[len(history_msgs) - i - 1]}")
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
        logger.info(f"MainChatRobotV2 user_msg: {user_msg}")

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

    
    def deal_intention(self, history_msgs):
        msg_prompt = self.deal_intention_prompts(history_msgs)
        if len(msg_prompt) == 0:
            return INTENTION.NOINTENTION

        result_msg = gpt_chat.generic_chat({"user_message": msg_prompt})

        if "A.拒绝" in result_msg:
            return INTENTION.NEGTIVE

        if "B.肯定" in result_msg:
            return INTENTION.POSITIVE

        if "C.问岗位信息的相关问题" in result_msg:
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
            if history_msgs[len(history_msgs) - i - 1]["speaker"] == "system":
                continue

            if history_msgs[len(history_msgs) - i - 1]["speaker"] == "robot":
                end_num = len(history_msgs) - i - 1
                break

            if history_msgs[len(history_msgs) - i - 1]["speaker"] == "user":
                new_msgs.append("候选人: " + history_msgs[len(history_msgs) - i - 1]["msg"])
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
你是一个猎头，判断一下，下面的对话中，用户最后一段对话的意图。
你和用户的历史对话在分隔符###中
用户最后一段对话在分隔符@@@中
答案选项 A.拒绝 B.肯定 C.问岗位信息的相关问题 D.没有任何意图
###
{msg_str}
###
@@@
{new_str}
@@@
'''
        return prompt


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