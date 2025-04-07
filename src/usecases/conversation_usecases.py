import logging
from typing import List
from api.model import ChatScope, Conversation
from core import Result
from core.request_timer import RequestTimer
from core.singelton import SingletonMeta
from database.implementation import ConversationDatabase
from usecases.llm import Message

logger = logging.getLogger(__name__)


class ConversationUsecases(metaclass=SingletonMeta):
    """
    Interface to ask the LLM for information.
    Used in UseCases to ask the LLM for information.
    """

    _database: ConversationDatabase

    def __init__(self, database: ConversationDatabase) -> None:
        self._database = database

    @classmethod
    def create(cls, database: ConversationDatabase):
        return cls(database)

    @classmethod
    def Instance(cls) -> "ConversationUsecases":
        if cls not in SingletonMeta._instances:
            raise RuntimeError(
                "Singleton instance has not been created yet. Call `create` first."
            )
        return SingletonMeta._instances[cls]

    async def create_conversation(self, conversation: Conversation) -> Result[str]:
        timer = RequestTimer()
        timer.start("create conversation")
        if conversation.context.scope == ChatScope.file.value and (
            len(conversation.context.fileIds) != 1
        ):
            return Result.Err(
                ValueError("Chats with file scope need exactly on file id as reference")
            )

        result = await self._database.create(conversation)
        timer.end()
        return result

    async def update_conversation(
        self, id: str, conversation: Conversation
    ) -> Result[None]:
        conversation.id = id
        timer = RequestTimer()
        timer.start("create conversation")
        result = await self._database.update(id=id, obj=conversation)
        timer.end()
        return result

    async def find_user_conversations(self, user_id: str) -> Result[List[Conversation]]:
        timer = RequestTimer()
        timer.start("find user conversations")
        result = await self._database.find_user(user_id=user_id)
        timer.end()
        return result

    async def find_conversation(self, conversation_id: str) -> Result[Conversation]:
        timer = RequestTimer()
        timer.start("find conversatoin")
        result = await self._database.get(id=conversation_id)
        timer.end()
        return result

    async def add_context(self, conversation_id: str, courseId: str) -> Result[None]:
        timer = RequestTimer()
        timer.start("find conversatoin")
        result = await self._database.set_course_context(
            conversation_id=conversation_id, courseId=courseId
        )
        timer.end()
        return result

    async def appand_messages(self, conversation_id: str, messages: List[Message]):
        timer = RequestTimer()
        timer.start("delete conversatoin")
        result = await self._database.inject_messages(
            conversation_id=conversation_id, messages=messages
        )
        timer.end()
        return result

    async def delete_conversation(self, conversation_id: str) -> Result[None]:
        timer = RequestTimer()
        timer.start("delete conversatoin")
        result = await self._database.delete(id=conversation_id)
        timer.end()
        return result

    async def set_course_id(self, conversation_id: str, courseId: str) -> Result[None]:
        timer = RequestTimer()
        timer.start("set course context")
        result = await self._database.set_course_context(
            conversation_id=conversation_id, courseId=courseId
        )
        timer.end()
        return result

    async def find_by_context(
        self,
        user_id: str,
        course_id: str | None = None,
        file_id: str | None = None,
        scope: str | None = None,
    ) -> Result[List[Conversation]]:
        query = {"user": user_id}
        if course_id:
            query["context.courseId"] = course_id
        if file_id:
            query["context.fileIds"] = file_id
        if scope:
            query["context.scope"] = scope
        timer = RequestTimer()
        timer.start(f"find query{query}")
        result = await self._database.run_query(query=query)
        timer.end()
        return result
