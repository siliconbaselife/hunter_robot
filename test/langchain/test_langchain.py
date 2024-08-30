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

from cryptography.fernet import Fernet

cipher = Fernet("Rthp08pOy1BzlI_PFXKXEXmqmxGv0k_DUsmFGjr6NZs=")

secret_token_0 = "gAAAAABlWsO9M5MHWyTjwMrJTxqj1yfzfuvJXNAxVFCZT4AoyklbVX3_EpmIVv59HhTjg4bYIZugs2sXBHDDpfvuJaThWXZr_lRomw5YYMNVdq9atyo7gcQUs8u8iDbsO3qOVDBKH_BXkGoiFJWXdAJSnJqT3xCKcg=="
OPENAI_API_KEY_0 = cipher.decrypt(secret_token_0).decode()

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY_0

loader = WebBaseLoader("https://docs.smith.langchain.com/user_guide")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)
embeddings = OpenAIEmbeddings()
vector = FAISS.from_documents(documents, embeddings)
retriever = vector.as_retriever()