from core import Result
from core.request_timer import RequestTimer
from core.singelton import SingletonMeta
from usecases.model.dto import (
    Document,
)

from usecases.storage import VectorDatabase


class VectorDBUsecases(metaclass=SingletonMeta):
    """
    Interface to ask the LLM for information.
    Used in UseCases to ask the LLM for information.
    """

    _vector_db: VectorDatabase

    def __init__(self, vector_db: VectorDatabase) -> None:
        self._vector_db = vector_db

    @classmethod
    def create(cls, vector_db: VectorDatabase):
        if cls not in SingletonMeta._instances:
            return cls(vector_db)
        else:
            raise RuntimeError("Singleton instance already created.")

    @classmethod
    def Instance(cls) -> "VectorDBUsecases":
        if cls not in SingletonMeta._instances:
            raise RuntimeError(
                "Singleton instance has not been created yet. Call `create` first."
            )
        return SingletonMeta._instances[cls]

    def store_doc(self, doc: Document) -> Result[None]:
        timer = RequestTimer()
        timer.start("query db")
        result = self._vector_db.create_document(doc=doc)
        timer.end()
        return result
