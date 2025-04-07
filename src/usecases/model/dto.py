from enum import Enum, auto
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

"""
Data Transfer Objects used in the project
"""


class NodeRelationship(str, Enum):
    SOURCE = auto()
    PREVIOUS = auto()
    NEXT = auto()
    PARENT = auto()
    CHILD = auto()


class Document(BaseModel):
    id: str
    content: str | list[str]
    metadata: Dict[str, Any]


class Node(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    relations: List[NodeRelationship]
    similarity_score: Optional[float]
