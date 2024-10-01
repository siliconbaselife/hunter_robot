import json
import os

from cryptography.fernet import Fernet

from utils.log import get_logger
from utils.config import config

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.chains import LLMChain
from enum import Enum

logger = get_logger(config['log']['business_log_file'])

cipher = Fernet("Rthp08pOy1BzlI_PFXKXEXmqmxGv0k_DUsmFGjr6NZs=")

secret_token = "gAAAAABlWsO9M5MHWyTjwMrJTxqj1yfzfuvJXNAxVFCZT4AoyklbVX3_EpmIVv59HhTjg4bYIZugs2sXBHDDpfvuJaThWXZr_lRomw5YYMNVdq9atyo7gcQUs8u8iDbsO3qOVDBKH_BXkGoiFJWXdAJSnJqT3xCKcg=="
OPENAI_API_KEY = cipher.decrypt(secret_token).decode()
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

logger = get_logger(config['log']['log_file'])


class Intention(Enum):
    Normal = 1


class ChatIntention(object):
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    def judge(self, msgs):
        return Intention.Normal


class ChatAgent(object):
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        prompt = PromptTemplate(
            input_variables=["relation_info", "history_str", "question"],
            template="你是一个猎头/HR的咨询助理，需要回答问题，保证回复在150字以内，尽量不超过100字。\n当前咨询内容相关信息如下:\n"
                     "{relation_info}\n历史聊天记录如下:\n{history_str}\n当前用户问题:\n{question}"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser

    def transfer_msgs(self, history_msgs):
        history_str = ""
        for msg in history_msgs:
            if msg["role"] == "robot":
                history_str += f"agent: {msg['msg']}\n"
            if msg["role"] == "user":
                history_str += f"用户: {msg['msg']}\n"

        return history_str

    def chat(self, relation_info, history, msg):
        res = self.chain.invoke(
            {"relation_info": relation_info, "history_str": self.transfer_msgs(history), "question": msg})
        return res


class KeyWordsAgent:
    def __init__(self, company, position, country):
        self.company = company
        self.position = position
        self.country = country

    def get(self):
        pass


class BenchMarkCompanyAgent:
    def __init__(self, company, position, country):
        self.company = company
        self.position = position
        self.country = country

    def get(self):
        pass


class educationAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        prompt = PromptTemplate(
            input_variables=["structure_info"],
            template="以下是一个人结构化的学历相关信息\n{structure_info}\n请解析出该人 本科、研究生、博士 学历情况, 只给出有的学历，返回以下格式json:\n "
                     "[{'学历': '本科', '学校': '清华', '时间': '2007-2010'}, {'学历': '研究生', '学校': '北大', '时间': '2010-2013'}]"
        )
        output_parser = JsonOutputParser()
        self.chain = prompt | chat | output_parser

    def get(self, educations):
        res = self.chain.invoke({"structure_info": json.dumps(educations)})
        return res


if __name__ == "__main__":
    agent = ChatAgent()
    history = [
        {"role": "user", "msg": "你好"},
        {"role": "robot", "msg": "有什么需要帮助你的呢?"},
        {"role": "user", "msg": "想咨询锐捷对标公司"},
        {"role": "robot", "msg": "哪个国家?"}
    ]

    res = agent.chat(relation_info="锐捷在美国对标公司 => 思科，苹果 在韩国对标公司 => 三星，lg", history=history,
                     msg="美国")
    print(f"res => {res}")
