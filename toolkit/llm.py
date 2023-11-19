import json
from abc import abstractmethod
from pathlib import Path
from typing import Optional, List, Mapping, Any, Dict

import openai
import requests
from dotenv import load_dotenv
import os
# import logging
from utils.log import get_logger

import curlify
from pydantic import BaseModel

load_dotenv(Path(__file__).parent.absolute() / './.llm.env')


loggerL = get_logger(f"{Path(__file__).parent.absolute()}/../log/llm.log")
# logger = logging.getLogger(__name__)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)
# logger.addHandler(console_handler)



class BaseMessage(BaseModel):
    """Message object."""

    content: str

    @property
    @abstractmethod
    def type(self) -> str:
        """Type of the message, used for serialization."""


class HumanMessage(BaseMessage):
    """Type of message that is spoken by the human."""

    example: bool = False

    @property
    def type(self) -> str:
        """Type of the message, used for serialization."""
        return "human"


class AIMessage(BaseMessage):
    """Type of message that is spoken by the AI."""

    example: bool = False

    @property
    def type(self) -> str:
        """Type of the message, used for serialization."""
        return "ai"


class SystemMessage(BaseMessage):
    """Type of message that is a system message."""

    @property
    def type(self) -> str:
        """Type of the message, used for serialization."""
        return "system"


class Prompt:

    def __init__(self):
        self.messages: List[BaseMessage] = []

    def add_system_message(self, content):
        self.messages.append(SystemMessage(content=content))
        return self

    def add_user_message(self, content):
        self.messages.append(HumanMessage(content=content))
        return self

    def add_assistant_message(self, content):
        self.messages.append(AIMessage(content=content))
        return self

    def to_string(self):
        return "\n".join([msg.content for msg in self.messages])

    def get_messages(self) -> List[Dict]:
        """
        返回chatgpt api需要的messages格式
        :return:
        """
        result = []
        for msg in self.messages:
            if msg.type == 'system':
                result.append({'role': 'system', 'content': msg.content})
            elif msg.type == 'human':
                result.append({'role': 'user', 'content': msg.content})
            elif msg.type == 'ai':
                result.append({'role': 'assistant', 'content': msg.content})
        return result

    def get_token_size(self):
        return len(self.to_string())


class LLMQueryException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class ChatGPT:

    def __init__(self) -> None:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_PROXY"):
            openai.proxy = os.getenv("OPENAI_PROXY")

    def chat(self, prompt: Prompt):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt.get_messages(),
            temperature=0.2
        )
        loggerL.info(f"Total token: {response.usage.total_tokens}, cost ${response.usage.total_tokens/1000*0.002}")
        return response.choices[0].message.content


class GPT:
    def __init__(self) -> None:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_PROXY"):
            openai.proxy = os.getenv("OPENAI_PROXY")

    def chat(self, message: List):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message,
            temperature=0.2
        )

        return response.choices[0].message.content


class Vicuna:

    def __init__(self):
        pass

    def chat(self, prompt: Prompt):
        url = f'{os.getenv("VICUNA_API_URL")}/v1/chat/completions'
        payload = {
            'model': 'vicuna-7b',
            'messages': prompt.get_messages(),
            'temperature': 0.2
        }

        res = requests.post(url, json=payload)
        try:
            res_json = json.loads(res.text)
            return res_json.get('choices')[0].get('message').get('content')
        except Exception as e:
            loggerL.error(
                f"没有返回正确的推理结果. \npayload = {payload} \ntoken_size = {prompt.get_token_size()} \nres.status = {res.status_code} \nres.context = {res.content} \n{curlify.to_curl(res.request)}")
            raise e


class LLM:

    def __init__(self):
        self.gpt = ChatGPT()
        pass

    def get_answer(self, prompt: Prompt):
        if os.getenv('DISABLE_LLM'):
            return prompt.to_string()

        try:
            # logger.info(f"PROMPT:\n {prompt.get_messages()}")
            # msg = requests.post('http://10.0.232.23:12121/vision/python/template/example/v1', json={'msg':prompt.get_messages()}).json()['data']
            msg = self.gpt.chat(prompt)
            # logger.info(f"gpt response: {msg}")
            msg = msg.replace("根据招聘要求，", "")
            return msg, 1

            # VICUNA_TOKEN_LIMIT = int(os.getenv('VICUNA_TOKEN_LIMIT', 0))
            # if prompt.get_token_size() < VICUNA_TOKEN_LIMIT:
            #     return Vicuna().chat(prompt)
            # else:
            #     return ChatGPT().chat(prompt)

        except Exception as e:
            loggerL.error(e, exc_info=True)
            return "", 0


if __name__ == '__main__':
    print('OPENAI_API_KEY', os.getenv("OPENAI_API_KEY"))
    print('OPENAI_PROXY', os.getenv("OPENAI_PROXY"))

    gpt = Vicuna()
    prompt = Prompt().add_user_message("""
    请问日本的首都是哪里？
    """)
    print(gpt.chat(prompt))
