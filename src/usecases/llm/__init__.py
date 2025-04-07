from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List
from api.model import Message
from pydantic import BaseModel

from core import Result
from usecases.model.dto import Node


class LLMResponse(BaseModel):
    response: str
    nodes: List[Node]


class ChatRole(Enum):
    Assistant = "assistant"
    User = "user"


def chatrole_from_string(string) -> ChatRole:
    if string == ChatRole.User.value:
        return ChatRole.User

    if string == ChatRole.Assistant.value:
        return ChatRole.Assistant

    raise Exception(f"String {string} could not be converted to ChatRole")


class RAGLLM(ABC):
    @abstractmethod
    def ask(
        self, messages: List[Message], model: str, filters: Dict[str, List[str]] = {}
    ) -> Result[LLMResponse]:
        pass
