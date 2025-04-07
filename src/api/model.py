import datetime
from enum import Enum
from typing import Annotated, List, Optional
from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime

from usecases.model.dto import Node


PyObjectId = Annotated[str, BeforeValidator(str)]


class NotFoundException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ChatScope(Enum):
    file = "file"
    course = "course"


class Context(BaseModel):
    fileIds: list[str] = Field(default=[])
    courseId: str | None = Field(default=None)
    scope: str


class Message(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=ObjectId())
    role: str = Field(...)
    content: str = Field(...)
    nodes: List[Node] = Field(default=[])
    timestamp: float

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "user",
                    "content": "Hello, how are you?",
                }
            ]
        }
    }


class ResponseMessage(BaseModel):
    conversationId: PyObjectId
    response: str
    timestamp: float
    nodes: list[Node]


class Conversation(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user: str = Field(...)
    messages: list[Message] = Field(default=[])
    context: Context = Field(...)
    timestamp: str | None = Field(default=None)
    summary: str | None = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user": "1",
                    "messages": [],
                    "context": {"fileIds": ["2", "4"], "courseId": "1"},
                }
            ]
        }
    }


class MessageRequest(BaseModel):
    message: str = Field(...)
    model: str = Field(...)
