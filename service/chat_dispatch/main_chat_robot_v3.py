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
import random
import requests

logger = get_logger(config['log']['log_file'])

gpt_chat = GptChat()


class INTENTION(Enum):
    POSITIVE = 1
    NEGTIVE = 2
    QUESTIOM_PAYMENT = 3    ##薪资
    QUESTIOM_BENIFITS = 4   ##福利
    QUESTIOM_POSITION = 5   ##工作地点
    QUESTIOM_WORKTIME = 6   ##工作时长
    QUESTIOM_OTHER = 7      ##岗位相关的其他问题
    NOINTENTION = -1

class MainChatRobotV3(BaseChatRobot):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        super(MainChatRobotV3, self).__init__(robot_api, account_id, job_id, candidate_id, source)
        self._job_id = job_id
        self.job_config = json.loads(get_job_by_id(job_id)[0][6], strict=False)
        self.platform = get_job_by_id(job_id)[0][1]
        self.template_id = get_template_id(job_id)[0][0]
        self._status_infos = self.fetch_now_status()
        self._reply_infos = self.fetch_reply_infos()
        self._questions_collection = self.fetch_question_collection()
        self._questions_to_ask, self._remain_questions_to_ask = self.fetch_questions_to_ask(self._questions_collection)
        self._template_info = self.fetch_template_info()
        self._msg_list = []

        logger.info(f'MainChatRobotV3: {candidate_id}| {job_id}| {self._status_infos}| {self.template_id}| {self._reply_infos}| {self._questions_to_ask}| {self._remain_questions_to_ask}| {self._questions_collection.keys()}')

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
            # logger.info(f"MainChatRobotV3_new_msgs: {new_msgs}")
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
                        logger.info(f'MainChatRobotV3,{self._candidate_id}, {e}, {e.args}, {traceback.format_exc()}')
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
        logger.info(f"MainChatRobotV3_prepared_msg:{self._candidate_id}, {self._job_id}, {history_msg}")
        return history_msg

    def contact(self, page_history_msg, db_history_msg):
        logger.info(f"MainChatRobotV3_page_history_msg: {self._candidate_id}, {self._job_id}, {page_history_msg}")
        logger.info(f"MainChatRobotV3_db_history_msg:{self._candidate_id}, {self._job_id}, {db_history_msg}")
        try:
            processed_history_msgs = self.prepare_msgs(page_history_msg, db_history_msg)
            logger.info(f"MainChatRobotV3处理前 {self._candidate_id} 的状态信息是 {self._status_infos}")
            self.deal_contact(processed_history_msgs)
            # self.deal_question_collections(processed_history_msgs)
            intention = self.deal_intention(processed_history_msgs)
            if has_contact_db(self._candidate_id, self._account_id):
                self._status_infos['has_contact'] = True
            r_msg, action = self.generate_reply(intention, processed_history_msgs)
            self.deal_r_msg(r_msg, action)
            self.update_question_collections_2_status_infos()
            logger.info(f"MainChatRobotV3处理后 {self._candidate_id} 的状态信息是 {self._status_infos}")
            update_status_infos_v2(self._candidate_id, self._account_id, json.dumps(self._status_infos, ensure_ascii=False), self._job_id)
            ## TODO update question_collections
            logger.info(f"MainChatRobotV3需要返回给客户 {self._candidate_id} 的话术 '{self._next_msg}' 以及动作 {self._status}")
        except BaseException as e:
            logger.info(f'MainChatRobotV3,{self._candidate_id}, {e}, {e.args}, {traceback.format_exc()}')

    def fetch_template_info(self):
        rs = query_template_config(self.template_id)
        if len(rs) == 0:
            return {}
        return json.loads(rs[0][0])

    def fetch_reply_infos(self):
        return self.job_config.get("reply_infos", {})

    def fetch_questions_to_ask(self, already_question_collection):
        question_list = self.job_config['dynamic_job_config'].get("questions_to_ask", [])
        remain_question_list = list(set(question_list) - set(already_question_collection.keys()))
        return question_list, remain_question_list

    def fetch_question_collection(self):
        return self._status_infos['question_collection']

    def update_question_collections_2_status_infos(self):
        self._status_infos['question_collection'] = self._questions_collection

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
        if 'question_collection' not in status_info:
            status_info['question_collection'] = {}
        return status_info

#     def deal_question_collections(self, history_msgs):
#         ## 用最新用户信息
#         # msg_list = []
#         # reach_user_msg = False
#         # for i in range(len(history_msgs)-1, -1, -1):
#         #     msg = history_msgs[i]
#         #     if msg['speaker'] != 'user' and reach_user_msg:
#         #         break
#         #     if msg['speaker'] == 'user':
#         #         reach_user_msg = True
#         #         msg_list.append(msg['msg'])

#         # msg_list = sorted(msg_list, reverse=True)
#         # msg_str = ''
#         # for msg in msg_list:
#         #     msg_str+=f'{msg}\n'

#         # 用所有用户的信息
#         msg_str = ''
#         for msg in history_msgs:
#             if msg['speaker']== 'user':
#                 msg_str+=f'{msg["msg"]}\n'

#         ## 用所有历史信息，llm会乱提取
#         # msg_str = ''
#         # for i in range(len(history_msgs)):
#         #     msg = history_msgs[i]
#         #     if msg["speaker"] == "system":
#         #         continue
#         #     msg_str += "我: " if msg["speaker"] == "robot" else "候选人: "
#         #     msg_str += msg["msg"] + "\n"

#         # if len(msg_str) == 0:
#         #     return ""
#         prefix = ''
#         questions_str=''
#         for i, q in enumerate(self._questions_to_ask):
#             questions_str+=f'{i}: {q}\n'
#         prompt = f'''
# {prefix}
# 你是一个猎头，你正在跟候选人沟通交流，你需要从用户的消息中提取你感兴趣的问题的答案。
# 用户的历史消息在以下分隔符###中，
# 你感兴趣的问题列表在以下分隔符@@@中：
# ###
# {msg_str}
# ###
# @@@
# {questions_str}
# @@@
# 请从用户的消息里提取这些问题的答案。
# 具体要求：
# 返回中包括 有答案的问题的序号 和 对应提取出来的答案信息，以换行符隔开不同的问题，一定注意，没有答案的问题不需要！没有答案的问题不需要！没有答案的问题不需要！；
# 如果没有发现所有问题都没有找到答案，就只返回：无。
# 以下是一个示例：
# 2 <关于问题2的答案>
# 4 <关于问题4的答案>
# '''
#         r_msg = gpt_chat.generic_chat({"user_message": prompt})
#         logger.info(f"MainChatRobotV3 deal_question_collections, prompt: {prompt}, return from llm: {r_msg}")
#         if r_msg[0]=='无':
#             return
#         for line in r_msg.split('\n'):
#             question_index = int(line[0])
#             answer = line[2:]
#             if question_index=='无' or answer=='无':
#                 continue
#             question = self._questions_to_ask[question_index]
#             self._questions_collection[question] = answer
#             # if question not in self._questions_collection:
#             #     self._questions_collection[question] = []
#             # self._questions_collection[question].append(answer)

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
        if intention == INTENTION.QUESTIOM_PAYMENT or intention == INTENTION.QUESTIOM_BENIFITS \
            or intention == INTENTION.QUESTIOM_POSITION or intention == INTENTION.QUESTIOM_WORKTIME or intention == INTENTION.QUESTIOM_OTHER:
            return self.deal_question_reply(history_msgs, intention)
        return "", ChatStatus.NoTalk

    def first_reply(self, intention):
        self._status_infos['ask_contact'] = True
        if self._status_infos['has_contact']:
            return '', ChatStatus.NoTalk
        if intention == INTENTION.NEGTIVE:
            if self.platform == 'Linkedin':
                return "ok, when there's a new job opening on my end, I will share it with you right away.", ChatStatus.NeedContact
            else:
                return "您看方便留个电话或者微信吗，我这边有新的岗位也可以第一时间给您分享", ChatStatus.NeedContact
        else:
            if self.platform == 'Linkedin':
                return "Hello, would it be convenient to leave a resume for us to discuss further?", ChatStatus.NeedContact
            else:
                return '您好，方便留个联系方式咱细聊下吗?', ChatStatus.NeedContact

    def deal_question_reply(self, history_msgs, qustion_intention):
        plugin_q_prompt, plugin_r_prompt = self.generate_question_intention_reply_prompt(qustion_intention)
        if self.platform == 'Linkedin':
            prefix = '请用英语回答问题。一定要用英语回答。一定要用英语回答。一定要用英语回答。'
        else:
            prefix = ''
        prompt = f'''
{prefix}
你是一个猎头，你正在跟候选人推荐一个岗位，简洁回答候选人的问题({plugin_q_prompt})。
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
{plugin_r_prompt}
###
'''
        msgs, user_msg = self.transfer_msgs(history_msgs)
        r_msg = gpt_chat.generic_chat({"history_chat": msgs, "system_prompt": prompt, "user_message": user_msg})

        if not self._status_infos['has_contact']:
            if self.platform == 'Linkedin':
                r_msg += '\nCould you please share your resume? I would like to discuss it with the boss on our end.'
            else:
                r_msg += '\n您看要不加个微信，我给您详细介绍下'
        return r_msg, ChatStatus.NormalChat

    def no_intention_reply(self, history_msgs):
        logger.info(f'MainChatRobotV3 no_intention_reply in')
        has_contact = self._status_infos['has_contact']
        ask_question_msg = self.generate_question_2_ask(has_contact)
        
        if ask_question_msg:
            logger.info(f'MainChatRobotV3 no_intention_reply, will ask_question {ask_question_msg}')
            return ask_question_msg, ChatStatus.NormalChat
        if has_contact:
            return '', ChatStatus.NoTalk
                    
        reply_msg = self.generate_ask_contact_reply(history_msgs)
        return reply_msg, ChatStatus.NormalChat

    def generate_question_intention_reply_prompt(self, question_intention):
        job_info = self.job_config['dynamic_job_config']
        job_info_map = {
            INTENTION.QUESTIOM_PAYMENT: ('薪资相关', job_info['salary_info']),
            INTENTION.QUESTIOM_BENIFITS: ('福利相关', job_info["benifits_info"]),
            INTENTION.QUESTIOM_POSITION: ('工作地点相关', job_info["location_info"]),
            INTENTION.QUESTIOM_WORKTIME: ('工作时长相关', job_info["location_info"]),
            INTENTION.QUESTIOM_OTHER: ('其他', job_info["other_info"]),
        }
        intention_str, reply_info = job_info_map[question_intention]
        question_prompt = f'岗位的{intention_str}问题'
        reply_prompt = f'''岗位的{intention_str}信息：\n{reply_info}
        '''
        return question_prompt, reply_prompt

    def generate_question_2_ask(self, need_ask_question, quit_prob=0.3):
        if len(self._remain_questions_to_ask) > 0:
            random_range = len(self._remain_questions_to_ask)-1 if need_ask_question else int(len(self._remain_questions_to_ask)* (1+quit_prob))
            random_choose_idx = random.randint(0, random_range)
            if random_choose_idx < len(self._remain_questions_to_ask):
                ## pop from remain, this question will not be asked any more
                question_2_ask = self._remain_questions_to_ask.pop(random_choose_idx)
                # self._questions_collection[question_2_ask] = []
                self._questions_collection[question_2_ask] = ''
                return question_2_ask
        return None

    def generate_ask_contact_reply(self, history_msgs):
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
        return r_msg.replace("$PHONE$", "")

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
            logger.info(f'MainChatRobotV3 already_have_contact, {self._candidate_id}')
            return True

        db_has_contact = has_contact_db(self._candidate_id, self._account_id)
        if db_has_contact:
            logger.info(f'MainChatRobotV3 already_have_contact, {self._candidate_id}')
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
            "cv":"",
            "email":""
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
            logger.info(f"MainChatRobotV3  {i} msg: {history_msgs[len(history_msgs) - i - 1]}")
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
        logger.info(f"MainChatRobotV3 user_msg: {user_msg}")

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
        logger.info(f"MainChatRobotV3 deal_intention, user user_message: {msg_prompt}, return from llm: {result_msg}")

        if "A.拒绝" in result_msg:
            return INTENTION.NEGTIVE

        if "B.肯定" in result_msg:
            return INTENTION.POSITIVE

        if "C.问岗位相关的薪资问题" in result_msg:
            return INTENTION.QUESTIOM_PAYMENT

        if "D.问岗位相关的福利问题" in result_msg:
            return INTENTION.QUESTIOM_BENIFITS

        if "E.问岗位相关的工作地点问题" in result_msg:
            return INTENTION.QUESTIOM_POSITION

        if "F.问岗位相关的工作时长问题" in result_msg:
            return INTENTION.QUESTIOM_WORKTIME

        if "G.问岗位相关的其他问题" in result_msg:
            return INTENTION.QUESTIOM_OTHER

        if "H.没有任何意图" in result_msg:
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
答案选项 A.拒绝 B.肯定 C.问岗位相关的薪资问题 D.问岗位相关的福利问题 E.问岗位相关的工作地点问题 F.问岗位相关的工作时长问题 G.问岗位相关的其他问题  H.没有任何意图
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
帮我萃取出客户的电话号码和whatsapp号或者邮箱email，排除掉我的信息。
结果用json格式表示，邮箱的key是email，电话的key是phone，whatsapp的key是wechat，获取不到的信息为null。
如果对话中没有客户的联系方式，就说没有联系方式。
我不需要你帮我写程序
回答限制在50个字以内
    '''
        return msg_prompt