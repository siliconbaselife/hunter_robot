from utils.log import get_logger
from utils.decorator import exception_retry
from utils.config import config
import openai
from typing import Optional, List, Mapping, Any, Dict
import os
from pydantic import BaseModel
from abc import abstractmethod

logger = get_logger(config['log']['log_file'])


class BaseMessage(BaseModel):
    """Message object."""

    content: str

    @property
    @abstractmethod
    def type(self) -> str:
        """Type of the message, used for serialization."""


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


class HumanMessage(BaseMessage):
    """Type of message that is spoken by the human."""

    example: bool = False

    @property
    def type(self) -> str:
        """Type of the message, used for serialization."""
        return "human"


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

#
# OPENAI_API_KEY = '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'
#
# OPENAI_PROXY = 'http://127.0.0.1:7890'

class ChatGPT:
    def __init__(self) -> None:
        # openai.api_key = OPENAI_API_KEY
        # if OPENAI_PROXY and len(OPENAI_PROXY) > 0:
        #     openai.proxy = OPENAI_PROXY
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_PROXY"):
            openai.proxy = os.getenv("OPENAI_PROXY")

    def chat(self, prompt: Prompt):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt.get_messages(),
            temperature=0.2
        )
        logger.info(f"Total token: {response.usage.total_tokens}, cost ${response.usage.total_tokens / 1000 * 0.002}")
        return response.choices[0].message.content


class GptChat:
    def __init__(self):
        self.chat_gpt = ChatGPT()

    @exception_retry()
    def generic_chat(self, message):
        """
        message
        {
            "history_chat": [{'msg':'nihao','role':'robot/user'},{'msg':'nihao','role':'robot/user'}],
            "system_prompt": "回答不超过3个字",
            "user_message": "请问你是谁"
        }
        """
        prompt = Prompt()
        if 'system_prompt' in message:
            prompt.add_system_message(message['system_prompt'])

        if 'history_chat' in message:
            for msg in message['history_chat']:
                if msg['role'] == 'user':
                    prompt.add_user_message(msg['msg'])
                if msg['role'] == 'robot':
                    prompt.add_assistant_message(msg['msg'])

        prompt.add_user_message(message['user_message'])
        logger.info(f"generic chatgpt prompt: {prompt.get_messages()}")
        response = self.chat_gpt.chat(prompt)
        logger.info(f"generic chatgpt response: {response}")
        return response

if __name__ == "__main__":
    gpt = ChatGPT()

    prompt = Prompt()
    prompt.add_system_message('随便说点儿')
    prompt.add_user_message("hi")
    r = gpt.chat()
    print(r.text)
