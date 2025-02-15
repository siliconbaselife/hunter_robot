import json
import os
import re

os.environ[
    'USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

from cryptography.fernet import Fernet

from utils.log import get_logger
from utils.config import config

from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
# from langchain.retrievers.web_research import QuestionListOutputParser
from langchain.output_parsers.pydantic import PydanticOutputParser
from pydantic import BaseModel, Field

# from langchain.vectorstores import Chroma
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models.openai import ChatOpenAI

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from langchain_core.tools import Tool
from langchain.utilities import GoogleSearchAPIWrapper

from langchain.retrievers.web_research import WebResearchRetriever
from langchain_community.document_loaders import WebBaseLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from scipy.spatial import distance

from enum import Enum

import concurrent.futures

logger = get_logger(config['log']['business_log_file'])

cipher = Fernet("Rthp08pOy1BzlI_PFXKXEXmqmxGv0k_DUsmFGjr6NZs=")

secret_token = "gAAAAABlWsO9M5MHWyTjwMrJTxqj1yfzfuvJXNAxVFCZT4AoyklbVX3_EpmIVv59HhTjg4bYIZugs2sXBHDDpfvuJaThWXZr_lRomw5YYMNVdq9atyo7gcQUs8u8iDbsO3qOVDBKH_BXkGoiFJWXdAJSnJqT3xCKcg=="
OPENAI_API_KEY = cipher.decrypt(secret_token).decode()
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

os.environ["GOOGLE_CSE_ID"] = "a5bb86389c8d54e04"
os.environ["GOOGLE_API_KEY"] = "AIzaSyADsE884QVkWz_Y8X1zJMvGl3lVmJ-IbZc"

logger = get_logger(config['log']['log_file'])


class Intention(Enum):
    Normal = 1


class ChatIntention(object):
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    def judge(self, msgs):
        return Intention.Normal


def transfer_json(r_txt):
    rres = ""
    if "```json" in r_txt:
        lines = r_txt.split('\n')
        lines = lines[1:]
        lines = lines[:-1]
        rres = " ".join(lines)
    return json.loads(rres)


class CompanyAgent(object):
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        # prompt = PromptTemplate(
        #     input_variables=["job_position", "country", "industry_type"],
        #     template="1. 通过网页搜索，找到与{job_position}和{country}相关的公司名单。 \n 2.分析这些公司，识别出潜在的人才来源，特别关"
        #              "注{industry_type}行业中的公司。\n 3. 提取关键信息，分析同质化的产品或者相同销售渠道的产品类型，生成可寻访的目标公司"
        #              "。\n 4. 再根据不同的产品方向整理出公司名单，每个产品类型要20家公司，"
        #              "对公司介绍在20个字节以内。\n 5. 输出的内容应为一份清晰的备忘录，返回json格式 3个key company_name description product_type"
        # )
        product_prompt = PromptTemplate(
            input_variables=["job_position", "country", "industry_type"],
            template="what are the product directions in {country} {industry_type}? Return the results as a JSON with the "
                     "on other word, only json. return only english."
                     "return format [product1, product2]"
        )

        output_parser = StrOutputParser()
        self.product_chain = product_prompt | chat | output_parser

        company_prompt = PromptTemplate(
            input_variables=["job_position", "country", "industry_type", "product"],
            template="what are the {product} in the {country} industry? List at least 20 companies and provide a description for each company, with the description being within 20 words."
                     "return the results as a JSON array with the keys `company_name` and `description`.on other word, only json. return only english."
                     "return format [company1, company2]"
        )
        output_parser = StrOutputParser()
        self.company_chain = company_prompt | chat | output_parser

    def run(self, job_position, country, industry_type, product):
        res = self.company_chain.invoke(
            {"job_position": job_position, "country": country, "industry_type": industry_type, "product": product})
        company_list = transfer_json(res)
        return product, company_list

    def chat(self, contents):
        job_position = contents["job_position"]
        country = contents["country"]
        industry_type = contents["industry_type"]

        res = self.product_chain.invoke(
            {"job_position": job_position, "country": country, "industry_type": industry_type})

        products = transfer_json(res)
        # products = product_directions[industry_type]

        company_infos = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.run, job_position, country, industry_type, products[i]) for i in
                       range(len(products))]
            for future in concurrent.futures.as_completed(futures):
                product, company_list = future.result()
                company_infos[product] = company_list

        return company_infos


class JDAgent(object):
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        prompt = PromptTemplate(
            input_variables=["job_title", "industry", "location", "application_email", "additional_requirements"],
            template="You are a professional Executive Search Consultant for global talent recruitment. Your task is to "
                     "create a LinkedIn recruitment ad based on the following variables. Follow the steps below to ensure "
                     "the ad content is concise and professional to attract suitable candidates.\nThe job title is {job_title}, "
                     "in the {industry} industry， and the work location is {location}.\nWrite a job description that "
                     "is clear and attractive, highlighting the key responsibilities and requirements of the position.\nAdd "
                     "the application email at the end of the ad: {application_email}.\nEnsure the overall tone is concise "
                     "and professional, with a beautiful layout. Include emoticons in the front text to make it lively, "
                     "aligning with the concerns of white-collar workers in the corresponding recruitment country and the "
                     "community style of LinkedIn. At the end of the article, generate keywords that match this LinkedIn "
                     "recruitment ad, such as #recruit #jobs and other relevant keywords.\nAdd a variable: {additional_requirements} "
                     "to supplement or modify the input content information.\nAll user input content is first translated into English, "
                     "and then the output text is unified into English. If there is output content in other languages, it is also translated "
                     "into English to ensure language consistency. Do not include any XML tags in the output.\nPlease ensure that the "
                     "output is well-structured and follows the guidelines provided."
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser

    def chat(self, contents):
        job_title = contents["job_title"]
        industry = contents["industry_type"]
        location = contents["country"]
        application_email = contents["application_email"]
        additional_requirements = contents["additional_requirements"]

        res = self.chain.invoke(
            {"job_title": job_title, "industry": industry, "location": location, "application_email": application_email,
             "additional_requirements": additional_requirements})
        return res


class ChatAgent(object):
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        prompt = PromptTemplate(
            input_variables=["relation_info", "history_str", "question"],
            template="你是一个猎头/HR的咨询助理，需要回答问题。\n回复结果尽量用markdown格式\n当前咨询内容相关信息如下:\n"
                     "{relation_info}\n历史聊天记录如下:\n{history_str}\n当前用户问题:\n{question}"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser

    @staticmethod
    def transfer_msgs(history_msgs):
        history_str = ""
        for msg in history_msgs:
            if msg["role"] == "robot":
                history_str += f"agent: {msg['msg']}\n"
            if msg["role"] == "user":
                history_str += f"用户: {msg['msg']}\n"

        return history_str

    def chat(self, relation_info, history, msg):
        history_str = self.transfer_msgs(history)
        res = self.chain.invoke(
            {"relation_info": relation_info, "history_str": history_str, "question": msg})
        return res


# class ChatAgentRaw(object):
#     def __init__(self):
#         self.chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
#         prompt = PromptTemplate()
#     def chat(self, msg):
#         r = self.chat.predict(msg)
#         print(r)


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
            input_variables=["structure_info", "json_format"],
            temperature=0,
            template="以下是一个人结构化的学历相关信息\n{structure_info}\n请解析出该人 本科、研究生、博士 学历情况, 只给出有的学历, 时间只需要到年, 返回以下格式json, 找不到的key可以为空, 没有的学历不显示:\n "
                     "{json_format}\n内容翻译成中文"
        )
        output_parser = JsonOutputParser()
        self.json_format = "[{'学历': '本科', '学校': '清华', '时间': '2009-2013'}, {'学历': '研究生', '学校': '本大', '时间': ''}]"
        self.chain = prompt | chat | output_parser

    def get(self, educations):
        res = self.chain.invoke({"structure_info": json.dumps(educations), "json_format": self.json_format})
        return res


class experienceAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["structure_info", "json_format"],
            template="以下是一个人结构化的工作经历历相关信息\n{structure_info}\n请解析出该人工作经历相关情况, 按照时间先后顺序, 时间只需要到年, 只需要开始到结束的时间, 返回以下格式json, 找不到的key可以为空:\n "
                     "{json_format} \n内容翻译成中文"
        )
        output_parser = JsonOutputParser()
        self.json_format = "[{'公司': '阿里巴巴', 'title': '销售总监', '时间': '2010-2011'}, {'公司': '百度', 'title': 'HR', '时间': ''}]"
        self.chain = prompt | chat | output_parser

    def get(self, experiences):
        res = self.chain.invoke({"structure_info": json.dumps(experiences), "json_format": self.json_format})
        return res


class parseChineseRelationAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["info", "json_format"],
            template="这段文字是一个人相关的文章，请萃取出该段文字中，该人与中国相关的内容，并总结归纳，有时间或者能推算出时间，请记录时间。"
                     "返回格式json如下, 如果没有相关内容txt内容为空, 返回必须是json格式, 翻译成中文, json格式如下: \n {json_format} \n文本如下: \n {info}"
        )
        output_parser = StrOutputParser()
        self.join_format = "[{'txt': 'hahaha'}, {'txt': 'lalala'}]"
        self.chain = prompt | chat | output_parser

    def parse(self, info):
        res = self.chain.invoke({"info": info, "json_format": self.join_format})
        if "json" in res:
            ress = res.split('\n')
            ress = ress[1:]
            ress = ress[:-1]
            res = "".join(ress)

        return res


class parseAcademicRelationAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["info", "json_format"],
            template="这段文字是一个人相关的文章，请萃取出该段文字中，该人与学术文章发表相关的内容，并总结归纳，有时间或者能推算出时间，请记录时间。"
                     "返回格式json如下, 如果没有相关内容txt内容为空, 返回必须是json格式, 翻译成中文, json格式如下: \n {json_format} \n文本如下: \n {info}"
        )
        output_parser = StrOutputParser()
        self.join_format = "[{'txt': 'hahaha'}, {'txt': 'lalala'}]"
        self.chain = prompt | chat | output_parser

    def parse(self, info):
        res = self.chain.invoke({"info": info, "json_format": self.join_format})
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
            template="这段文字是一个人与中国相关的文章信息，请整理内容，去除掉重复的信息，尽量按照时间线顺序排序内容。\n文本如下: \n{txt}"
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
            # if 'txt' in parse_info and parse_info['txt'] is not None and len(parse_info['txt']) > 0:
            #     for txt in parse_info['txt']:
            #         relation_infos += txt + "\n"
            for info in parse_info:
                relation_infos += info["txt"] + "\n"

        res = self.chain.invoke({"txt": relation_infos})
        ress = res.split('\n')
        ress = ress[1:]
        "\n".join(ress)

        return res


class academicInfoParseAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["txt"],
            template="这段文字是一个人与学术文章发表相关的内容信息，请整理内容，去除掉重复的信息，尽量按照时间线顺序排序内容。\n文本如下: \n{txt}"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser
        self.agent = parseAcademicRelationAgent()

    def get(self, infos):
        relation_infos = ""
        for info in infos:
            parse_info_str = self.agent.parse(info)
            parse_info = json.loads(parse_info_str)
            print("-------------------")
            print(info)
            print(parse_info)
            print("-------------------")
            # if 'txt' in parse_info and parse_info['txt'] is not None and len(parse_info['txt']) > 0:
            #     for txt in parse_info['txt']:
            #         relation_infos += txt + "\n"
            for info in parse_info:
                relation_infos += info["txt"] + "\n"

        res = self.chain.invoke({"txt": relation_infos})
        ress = res.split('\n')
        ress = ress[1:]
        "\n".join(ress)

        return res


class extractionRelationAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o", temperature=0)
        prompt = PromptTemplate(
            input_variables=["info", "json_format", "query"],
            template="这段文字是一个人相关的文章，请萃取出该段文字中，与问题相关的信息，并总结归纳成一个json列表，有时间或者能推算出时间。"
                     "返回格式json如下, 如果没有相关内容txt内容为空, 返回必须是能接汐的json格式，千万不要给多余的格式, 翻译成中文, json格式如下, 一定要按照我给的这个格式返回: \n{json_format} \n"
                     "文本如下: \n{info} \n 问题如下: \n{query}"
        )
        output_parser = StrOutputParser()
        self.join_format = '[{"txt": "hahaha"}, {"txt": "lalala"}]'
        self.chain = prompt | chat | output_parser

    def parse(self, info, query):
        res = self.chain.invoke({"info": info, "json_format": self.join_format, "query": query})
        # if "json" in res:
        #     ress = res.split('\n')
        #     ress = ress[1:]
        #     ress = ress[:-1]
        #     res = "".join(ress)

        lines = res.split('\n')
        rres = ""
        for line in lines:
            if "```" in line:
                continue
            rres += line
        return json.loads(rres)


class summarizeAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["content", "query"],
            template="请按照问题解析文本内容，解析结果按照事件顺序排列，去掉重复内容，或者是与问题不相关的内容。\n 文本内通如下: {content} \n 问题如下: \n{query}"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser

    def get(self, content, query):
        res = self.chain.invoke({"content": content, "query": query})
        lines = res.split('\n')
        rres = ""
        for line in lines:
            if line == '':
                continue
            rres += line + "\n"

        return rres


class EmbeddingAgent:
    def __init__(self, texts):
        # text_splitter = RecursiveCharacterTextSplitter(separators=["\n"], chunk_size=1, chunk_overlap=0)
        # pages = text_splitter.create_documents(texts)
        pages = []
        for txt in texts:
            pages.append(Document(txt))

        self.llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)
        embeddings = OpenAIEmbeddings()
        self.db = Chroma.from_documents(documents=pages, embedding=embeddings)

    def cal(self, query):
        results = self.db.similarity_search_with_relevance_scores(query, k=10)
        relation_txts = ""
        for r in results:
            relation_txts += r[0].page_content
        print(relation_txts)
        return relation_txts


class parseAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["query", "txt"],
            template="按照下面的问题分析文本给出结果\n{query}\n需要分析的文本如下:\n{txt}"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser

    def cal(self, query, txt):
        res = self.chain.invoke({"query": query, "txt": txt})
        return res


class searchAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["query", "search_txt"],
            template="你需要按照google搜索结果，整合内容，得出问题结论，问题: \n{query} \n 返回结果需要是json格式，key 为answer，只需要回答答案不要说废话 \n搜索结果如下: \n{search_txt}"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser

    def cal(self, query, search_infos):
        res = self.chain.invoke({"query": query, "search_txt": json.dumps(search_infos)})
        return res


class LineList(BaseModel):
    lines: List[str] = Field(description="Question")


class QuestionListOutputParser(PydanticOutputParser):
    def __init__(self) -> None:
        super().__init__(pydantic_object=LineList)

    def parse(self, text) -> LineList:
        lines = re.findall(r"\d+\..*?\n", text)
        return LineList(lines=lines)


import logging

logging.basicConfig()
logging.getLogger("langchain.retrievers.web_search").setLevel(logging.INFO)


def google_search_back(n, query):
    search = GoogleSearchAPIWrapper(k=n)

    search_prompt = PromptTemplate(
        input_variables=["question"],
        template="you are an assistant tasked with improving Google search results. Generate 5 Google search queries "
                 "that are similar to this question. The output should be a numbered list of questions and each should have"
                 " a question mark at the end: {question}"
    )
    # llm = ChatOpenAI(temperature=0)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    # llm_chain = LLMChain(llm=llm, prompt=search_prompt, output_parser=QuestionListOutputParser())
    llm_chain = search_prompt | llm | QuestionListOutputParser()
    vectorstore = Chroma(embedding_function=OpenAIEmbeddings())
    # tool = Tool(
    #     name="google_search",
    #     description="Search Google for recent results.",
    #     func=search.run,
    # )
    web_research_retriever = WebResearchRetriever.from_llm(vectorstore=vectorstore, llm=llm_chain, search=search,
                                                           allow_dangerous_requests=True)
    docs = web_research_retriever.get_relevant_documents(query)

    return docs


search = GoogleSearchAPIWrapper(k=10)


def top5_results(query):
    return search.results(query, 5)


def google_search(n, query):
    tool = Tool(
        name="Google Search Snippets",
        description="Search Google for recent results.",
        func=top5_results,
    )
    rs = tool.run(query)
    for r in rs:
        link = r["link"]
        loader = WebBaseLoader(link)
        docs = loader.load()
        print(docs)

    return rs


class googleKeyAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["query"],
            template="你需要根据我的问题设计google搜索的关键字，能让我搜索出问题的相关信息，问题如下: \n {query} \n"
                     "返回2个关键字，一个关键字是中文，一个关键字是英文，返回格式为json，返回key为keywords"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser

    def cal(self, query):
        res = self.chain.invoke({"query": query})
        lines = res.split('\n')
        rres = ""
        for line in lines:
            if "```" in line:
                continue
            rres += line

        res_json = json.loads(rres)
        key_word_list = res_json["keywords"]
        key_words = []
        for _, value in key_word_list.items():
            key_words.append(value)

        return key_words


# def top10_results(query):
#     return search.results(query, 5)


class googleSearchAgent:
    def __init__(self, n=5):
        self.search = GoogleSearchAPIWrapper(k=n)
        self.embeddings = OpenAIEmbeddings()
        self.tool = Tool(
            name="Google Search Snippets",
            description="Search Google for recent results.",
            func=top5_results,
        )

        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["query", "snippet"],
            template="这个是google搜索出的摘要，帮我判断一下摘要跟我的问题是否相关，A.相关，B.不相关"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser

    def is_snippet_relation(self, query, snippet):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = PromptTemplate(
            input_variables=["query", "snippet"],
            template="这个是google搜索出的摘要，帮我判断一下摘要跟我的问题是否相关，A.相关，B.不相关. \n 问题: {query} \n 摘要: {snippet}"
        )
        output_parser = StrOutputParser()
        self.chain = prompt | chat | output_parser
        res = self.chain.invoke({"query": query, "snippet": snippet})
        if "A.相关" in res:
            return True
        else:
            return False

    def cal(self, key_word, query):
        query_features = self.embeddings.embed_query(query)
        rs = self.tool.run(key_word)

        relation_txt = []
        for r in rs:
            print(r)
            link = r["link"]
            if ".pdf" in link:
                continue

            snippet = r["snippet"]
            if not self.is_snippet_relation(query, snippet):
                logger.info(f"googleSearchAgent 链接 {link} 跟问题 {query} 不相关")
                continue

            try:
                loader = WebBaseLoader(link)
                docs = loader.load()
            except BaseException as e:
                print(f"googleSearchAgent 链接 {link} 获取不到内容")
                continue

            doc = str(docs[0])
            lines = doc.split('\n')
            print(f"googleSearchAgent 链接 {link} 跟问题 {query} 获取到内容 {len(lines)} 行")

            info_txt = ''
            token_num = 0
            times = 0
            for line in lines:
                line = line.strip()
                if len(line) == 0:
                    continue
                info_txt += line
                token_num += len(line)

                if token_num > 1000:
                    # txt_features = self.embeddings.embed_query(info_txt)
                    # txt_distance = distance.cosine(query_features, txt_features)

                    # if txt_distance < 0.2:
                    relation_txt.append(info_txt)

                    # print("--------------------------------------------")
                    # print(info_txt)
                    # print(txt_distance)
                    # print("--------------------------------------------")

                    info_txt = ""
                    token_num = 0
                    times += 1
                    if times > 5:
                        break

            if token_num > 0:
                # txt_features = self.embeddings.embed_query(info_txt)
                # txt_distance = distance.cosine(query_features, txt_features)
                # if txt_distance < 0.2:
                relation_txt.append(info_txt)

        # print(f"相关文档 数量: {len(relation_txt)}: {relation_txt}")
        return relation_txt


class comprehendAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        extract_prompt = PromptTemplate(
            input_variables=["query", "txt"],
            template="萃取出问题内容中与问题相关的内容，要简要，不超过50个字，如果认为文本内容与问题不相关，返回'不相关'。文本如下: \n {txt} \n 问题如下: \n {query}"
        )
        output_parser = StrOutputParser()
        self.extract_chain = extract_prompt | chat | output_parser

        prompt = PromptTemplate(
            input_variables=["query", "txt"],
            template="这个是我们从google上萃取出的相关文本内容: \n {txt} \n 这个是我们的问题: \n {query} \n 请根据提示，以及你自己的理解以及你自己已有的知识回答问题。返回结果控制在400个字以内。返回结果用markdown格式。"
        )
        self.chain = prompt | chat | output_parser

    def cal(self, query, txts):
        extract_txt = ""
        for txt in txts:
            res = self.extract_chain.invoke({"query": query, "txt": txt})
            if "不相关" in res:
                continue

            # print("txt = >")
            # print(txt)
            logger.info(f"comprehendAgent 问题 {query} 萃取出的结果: {res}")
            extract_txt += res

        res = self.chain.invoke({"query": query, "txt": extract_txt})
        return res


class SearchMan:
    def __init__(self):
        self.google_key_agent = googleKeyAgent()
        self.google_search_agent = googleSearchAgent()
        self.comprehend_agent = comprehendAgent()

    def cal(self, query):
        logger.info(f"SearchMan get query: {query}")
        key_words = self.google_key_agent.cal(query)
        logger.info(f"key_words: {key_words}")

        relation_txts = []
        for key_word in key_words:
            logger.info(f"begin search key word: {key_word}")
            relation_txt = self.google_search_agent.cal(key_word, query)
            relation_txts.extend(relation_txt)

        res = self.comprehend_agent.cal(query, relation_txts)
        return res


class huiweiPeopleAgent:
    def __init__(self):
        chat = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        output_parser = StrOutputParser()
        prompt = PromptTemplate(
            input_variables=["profile"],
            template='{profile}\n'
                     '====================================\n'
                     '以上是一个候选人在linkedin的简历。请帮我对该简历进行分析，并返回json格式。\n'
                     '需要萃取出的字段如下\n'
                     'age => 通过学校毕业的时间，大学 + 22，研究生 + 25，高中 + 18\n'
                     'chinese => 是否是中国人\n'
                     'graduate_school => 毕业学校，最高学历学校。如果没有 返回 "无法判断"\n'
                     'education_background => 学历，枚举值 "本科" "研究生" "博士" "博士后" "其他"，不能判断就返回 "其他"\n'
                     'school_level => 学校的层级，枚举值 "常青藤联盟" "双一流" "985" "211" "QS前100" "QS前300" "QS前500" "QS前1000" "其他", 不能判断就返回 "其他"\n'
                     'service_or_product_type => 根据简历判断一下，他的服务与产品类型，如果无法判断，给出 "无法判断" 的字段。枚举值有 '
                     '"运营商网络通信服务" "企业网络通信服务" "消费者终端" "Cloud云服务" "S-BG(海外研发实验室/供应链采购)" "储能" "新能源汽车""无法判断"\n'
                     'function_type => 根据简历判断一下，他的职能类型，如果无法判断，给出 "无法判断" 的字段。枚举值有 "人力" "财经" "企业发展" '
                     '"战略" "GR/PR" "法务" "内部审计业务合规" "sales" "KA sales" "渠道sales" "企业B2B sales" "销售管理" "零售分销" "数字营销-SEO" '
                     '"新媒体运营" "独立站" "亚马逊" "电商运营" "Market" "Brand" "GTM" "solution" "售后" "项目交付" "战略分析" "半导体" '
                     '"数字前端工程师" "数字后端工程师" "模拟芯片设计工程师" "IC验证工程师" "模拟版图设计工程师" "芯片CAD工程师" "半导体工艺工程师" '
                     '"半导体设备工程师" "IC测试" "封装研发" "IC失效分析" "半导体产品工程师" "FAE现场应用工程师" "半导体技术工程师" "PCB工程师" '
                     '"射频工程师" "FPGA工程师" "单片机工程师" "嵌入式硬件开发" "硬件测试工程师" "DSP工程师" "驱动开发" "嵌入式软件开发" "信号完整性工程师" '
                     '"硬件工程师" "硬件产品经理" "数通工程师" "通信标准化工程师" "核心网工程师" "无线网络优化" "无线通信工程师" "通信传输工程师" "通信电源工程师" '
                     '"通信软件工程师" "通信技术工程师" "通信项目管理" "储能-仿真" "储能硬件" "EDA" "储能-电子设计" "储能-算法" "PCB软件" "DSP" "储能-电子研发" '
                     '"储能-软硬件工程师" "PLC" "嵌入式" "微逆电力" "电池管理" "逆变器" "PCS" "变流器""无法判断"\n'
                     'service_country => 服务的国家，如果无法判断，给出 "无法判断" 的字段。\n'
                     'rank_of_position => 根据简历判断一下，他的岗位级别，如果无法判断，给出 "无法判断" 的字段。枚举值有 "Specialist" "Supervisor" "manager" '
                     '"director" "General Manager " "Vice President " "CXO" "无法判断"\n'
                     'department => 根据简历判断一下，他应该隶属于什么部门，如果无法判断，给出 "无法判断" 的字段。枚举值有 "运营商网络通讯服务" "企业网络通讯服务" '
                     '"消费者" "Cloud" "S-BG(海外研发实验室/供应链采购)" "储能" "新能源汽车" "人力" "财经" "企业发展" "战略" "GR/PR" "法务" "内部审计" "业务合规" "无法判断"\n'
                     'cooperative_department => 根据简历判断一下，推导他的日常工作中需要对接哪些部门或客户，如果无法判断，给出 "无法判断" 的字段。'
                     '枚举值有 "销售协同市场" "产品协同市场" "iot协同市场" "无法判断"'
        )
        self.chain = prompt | chat | output_parser

    def cal(self, profile):
        res = self.chain.invoke({"profile": profile})
        print(res)
        lines = res.split('\n')
        rres = ""
        for line in lines:
            if "```" in line:
                continue
            rres += line
        return json.loads(rres)


class OnlineSearchAgent:
    def __init__(self):
        pass

    def cal(self, query):
        pass


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
