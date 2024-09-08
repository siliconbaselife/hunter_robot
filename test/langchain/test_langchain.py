#!/usr/bin/env python
from typing import List

from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub
from langchain.agents import create_openai_functions_agent
from langchain.agents import AgentExecutor
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.messages import BaseMessage
from langserve import add_routes
import os
from langchain_openai import ChatOpenAI

from cryptography.fernet import Fernet

from langchain_openai import OpenAI

from langchain_core.prompts import PromptTemplate

cipher = Fernet("Rthp08pOy1BzlI_PFXKXEXmqmxGv0k_DUsmFGjr6NZs=")

secret_token_0 = "gAAAAABlWsO9M5MHWyTjwMrJTxqj1yfzfuvJXNAxVFCZT4AoyklbVX3_EpmIVv59HhTjg4bYIZugs2sXBHDDpfvuJaThWXZr_lRomw5YYMNVdq9atyo7gcQUs8u8iDbsO3qOVDBKH_BXkGoiFJWXdAJSnJqT3xCKcg=="
OPENAI_API_KEY_0 = cipher.decrypt(secret_token_0).decode()

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY_0


from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from langchain_experimental.utilities import PythonREPL
from langchain_openai import ChatOpenAI

template = """编写一些用于解决用户问题的Python代码。 

只返回Markdown格式的Python代码，例如：

```python
....
```"""
prompt = ChatPromptTemplate.from_messages([("system", template), ("human", "{input}")])

model = ChatOpenAI()

def _sanitize_output(text: str):
    _, after = text.split("```python")
    return after.split("```")[0]

chain = prompt | model
        # | StrOutputParser()
        # | _sanitize_output | PythonREPL().run

r = chain.invoke({"input": "2加2等于多少"})
print(r)





