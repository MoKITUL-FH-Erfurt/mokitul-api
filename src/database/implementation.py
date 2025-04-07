from typing import List
from api.model import Conversation, Message, NotFoundException
from bson import ObjectId
from core import Result
from database.session import BaseDatabase

import logging

logger = logging.getLogger(__name__)


class ConversationDatabase(BaseDatabase[Conversation]):
    def __init__(self):
        super().__init__(Conversation, "conversations")

    async def find_user(self, user_id: str) -> Result[List[Conversation]]:
        return await self.run_query({"user": user_id})

    async def inject_messages(
        self, conversation_id: str, messages: List[Message]
    ) -> Result[None]:
        try:
            result = await self._collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                message.model_dump(by_alias=True)
                                for message in messages
                            ]
                        }
                    }
                },
            )
            if result.modified_count == 1:
                Result.Ok()
            else:
                Result.Err(
                    NotFoundException(
                        f"Failed to inject messages into {conversation_id}"
                    )
                )
        except Exception as e:
            return Result.Err(e)

        return Result.Ok()

    async def set_course_context(
        self, conversation_id: str, courseId: str
    ) -> Result[None]:
        try:
            result = await self._collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": {"context.courseId": courseId}},
            )
            if result.modified_count == 1:
                return Result.Ok()
            else:
                return Result.Err(
                    NotFoundException(
                        f"Failed to set course for {conversation_id}, {result.raw_result}"
                    )
                )
        except Exception as e:
            return Result.Err(e)
