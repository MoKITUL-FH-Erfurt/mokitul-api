from abc import ABC, abstractmethod
from typing import Dict, List
from core import Result
from usecases.model.dto import (
    Document,
    Node,
)

"""
Contains interfaces for the database classes used in the project, that are used by the usecases
"""


class VectorDatabase(ABC):
    @abstractmethod
    def create_document(self, doc: Document) -> Result[None]:
        pass

    @abstractmethod
    def find_similar_nodes(self, query: str) -> Result[List[Node]]:
        pass

    @abstractmethod
    def does_object_with_metadata_exist(self, metadata: Dict[str, str]) -> Result[bool]:
        pass


class PDFConverter(ABC):
    @abstractmethod
    def transform_file_to_markdown(self, file: str) -> list[str]:
        pass
