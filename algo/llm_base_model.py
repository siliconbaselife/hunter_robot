from abc import abstractmethod
from typing import List, Dict
from pydantic import BaseModel


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

    def clear(self):
        self.messages = []

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
