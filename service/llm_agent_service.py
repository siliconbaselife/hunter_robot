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
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["structure_info"],
            temperature=0,
            template="以下是一个人结构化的学历相关信息\n{structure_info}\n请解析出该人 本科、研究生、博士 学历情况, 只给出有的学历, 时间只需要到年, 返回以下格式json:\n "
                     "key => 学历 学校 时间\n内容翻译成中文"
        )
        output_parser = JsonOutputParser()
        self.chain = prompt | chat | output_parser

    def get(self, educations):
        res = self.chain.invoke({"structure_info": json.dumps(educations)})
        return res


class experienceAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["structure_info"],
            template="以下是一个人结构化的工作经历历相关信息\n{structure_info}\n请解析出该人工作经历相关情况, 按照时间先后顺序, 时间只需要到年, 只需要开始到结束的时间, 返回以下格式json:\n "
                     "key => 公司 title 时间\n内容翻译成中文"
        )
        output_parser = JsonOutputParser()
        self.chain = prompt | chat | output_parser

    def get(self, experiences):
        res = self.chain.invoke({"structure_info": json.dumps(experiences)})
        return res


class parseChineseRelationAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["info"],
            template="这段文字是一个人相关的文章，请萃取出该段文字中，该人与中国相关的内容，并总结归纳，有时间或者能推算出时间，请记录时间。"
                     "返回格式json如下, 如果没有相关内容txt内容为空, 返回必须是json格式, 翻译成中文: \n key => txt \n 返回是数组，只有一个key txt \n文本如下: \n {info}"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser

    def parse(self, info):
        res = self.chain.invoke({"info": info})
        if "json" in res:
            ress = res.split('\n')
            ress = ress[1:]
            ress = ress[:-1]
            res = "".join(ress)

        return res


class infoParseAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["txt"],
            template="这段文字是一个人与中国相关的文章信息，请整理内容，去除掉重复的信息，按照时间线顺序排序内容。\n文本如下: \n{txt}"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser
        self.agent = parseChineseRelationAgent()

    def get(self, infos):
        relation_infos = ""
        for info in infos:
            parse_info_str = self.agent.parse(info)
            parse_info = json.loads(parse_info_str)
            print("-------------------")
            print(info)
            print(parse_info)
            print("-------------------")
            if 'txt' in parse_info and parse_info['txt'] is not None and len(parse_info['txt']) > 0:
                for txt in parse_info['txt']:
                    relation_infos += txt + "\n"

        res = self.chain.invoke({"txt": relation_infos})
        ress = res.split('\n')
        ress = ress[1:]
        "\n".join(ress)

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
