import logging
from typing import Callable
import unittest
from api.model import ChatScope, Context, Conversation, Message, NotFoundException
from api.utils.chains import get_posix_timestamp
from pydantic import InstanceOf
from testcontainers.mongodb import MongoDbContainer

from core.settings import init_logging
from database.implementation import ConversationDatabase
from database.session import DatabaseConfig, MongoDatabaseSession
from usecases.conversation_usecases import ConversationUsecases
from usecases.model.dto import Node

USER_DUMMY_ID = "dummy_user_id"
COURSE_DUMMY_ID = "dummy_course_id"
FILE_DUMMY_ID = "dummy_file_id"
CONVERSATION_DUMMY_ID = "65d7b8f9a5e9c3d4f1a2b3c4"

init_logging("INFO")
logger = logging.getLogger(__name__)


"""
Database Layer Tests
"""

async def run_test_with_mongo(handle_msg: Callable):
    """
    Wrapper function to run the test with a MongoDB container.
    """
    with MongoDbContainer(username="test", password="test") as mongodb:
        config = DatabaseConfig(
            host=mongodb.get_container_host_ip(),
            port=str(mongodb.get_exposed_port(mongodb.port)),
            database_name="test_db",
            username=mongodb.username,
            password=mongodb.password,
        )
        await create_database(config=config)
        await handle_msg()


async def create_database(config: DatabaseConfig):
    MongoDatabaseSession.init_database(config=config)

    conversation_database = ConversationDatabase()
    await conversation_database.start()
    ConversationUsecases.create(conversation_database)


async def create_conversatoin() -> str:
    """
    helper function to create a conversation if the tests needs an already existing one.
    """
    result = await ConversationUsecases.Instance().create_conversation(
        Conversation(
            user=USER_DUMMY_ID,
            messages=[],
            context=Context(fileIds=[], courseId=None, scope=ChatScope.course.value),
            timestamp=str(get_posix_timestamp()),
            summary="",
        )
    )
    if result.is_error():
        logger.error(result.get_error())
    assert result.is_ok()

    id = result.get_ok()

    result = await ConversationUsecases.Instance().find_conversation(id)
    assert result.is_ok()
    return id


class TestConversationDatbase(unittest.IsolatedAsyncioTestCase):
    async def test_create_conversation(self):
        async def run():
            result = await ConversationUsecases.Instance().create_conversation(
                Conversation(
                    user=USER_DUMMY_ID,
                    messages=[],
                    context=Context(
                        fileIds=[FILE_DUMMY_ID],
                        courseId=COURSE_DUMMY_ID,
                        scope=ChatScope.file.value,
                    ),
                    timestamp=str(get_posix_timestamp()),
                    summary="",
                )
            )
            assert result.is_ok()

            id = result.get_ok()

            # test all read operations
            # in the futur each operation should be tested in a separate test
            # but for the meoment this save a lot of time starting each time a new container
            # if the read operations get complexer or more operations are added
            # please refactor this

            result = await ConversationUsecases.Instance().find_conversation(id)
            assert result.is_ok()

            result = await ConversationUsecases.Instance().find_user_conversations(
                USER_DUMMY_ID
            )
            assert result.is_ok()
            assert len(result.get_ok()) == 1

            result = await ConversationUsecases.Instance().find_by_context(
                user_id=USER_DUMMY_ID
            )
            assert result.is_ok()
            assert len(result.get_ok()) == 1

            result = await ConversationUsecases.Instance().find_by_context(
                user_id=USER_DUMMY_ID, course_id=COURSE_DUMMY_ID
            )
            assert result.is_ok()
            assert len(result.get_ok()) == 1

            result = await ConversationUsecases.Instance().find_by_context(
                user_id=USER_DUMMY_ID, file_id=FILE_DUMMY_ID
            )
            assert result.is_ok()
            assert len(result.get_ok()) == 1

            result = await ConversationUsecases.Instance().find_by_context(
                user_id=USER_DUMMY_ID, file_id=FILE_DUMMY_ID, course_id=COURSE_DUMMY_ID
            )
            assert result.is_ok()
            assert len(result.get_ok()) == 1

            result = await ConversationUsecases.Instance().find_by_context(
                user_id=USER_DUMMY_ID, scope=ChatScope.course.value
            )
            assert result.is_ok()
            assert len(result.get_ok()) == 0

            result = await ConversationUsecases.Instance().find_by_context(
                user_id=USER_DUMMY_ID, file_id="not_existing"
            )
            assert result.is_ok()
            assert len(result.get_ok()) == 0

            result = await ConversationUsecases.Instance().find_by_context(
                user_id=USER_DUMMY_ID, course_id="not_existing"
            )
            assert result.is_ok()
            assert len(result.get_ok()) == 0

        await run_test_with_mongo(run)

    async def test_create_invalid_conversation(self):
        async def run():
            result = await ConversationUsecases.Instance().create_conversation(
                Conversation(
                    user=USER_DUMMY_ID,
                    messages=[],
                    context=Context(
                        fileIds=[],
                        courseId=COURSE_DUMMY_ID,
                        scope=ChatScope.file.value,
                    ),
                    timestamp=str(get_posix_timestamp()),
                    summary="",
                )
            )
            assert result.is_error()
            error = result.get_error()
            assert isinstance(error, ValueError)

        await run_test_with_mongo(run)

    async def test_delete_conversation(self):
        async def run():
            id = await create_conversatoin()

            result = await ConversationUsecases.Instance().delete_conversation(
                conversation_id=id
            )

            assert result.is_ok()

            result = await ConversationUsecases.Instance().find_conversation(id)
            assert result.is_error()
            assert isinstance(result.get_error(), NotFoundException)

        await run_test_with_mongo(run)

    async def test_delete_not_existing_conversation(self):
        async def run():
            result = await ConversationUsecases.Instance().delete_conversation(
                conversation_id=CONVERSATION_DUMMY_ID
            )
            assert result.is_error()
            assert isinstance(result.get_error(), NotFoundException)

        await run_test_with_mongo(run)

    async def test_append_messages(self):
        async def run():
            id = await create_conversatoin()

            result = await ConversationUsecases.Instance().add_context(
                conversation_id=id, courseId=COURSE_DUMMY_ID
            )
            user_message = Message(
                role="User", content="user", timestamp=get_posix_timestamp()
            )

            assistent_message = Message(
                role="assistent",
                content="assistent",
                timestamp=get_posix_timestamp(),
                nodes=[
                    Node(
                        id=COURSE_DUMMY_ID,
                        content="Hi :)",
                        relations=[],
                        metadata={},
                        similarity_score=0.74,
                    )
                ],
            )

            result = await ConversationUsecases.Instance().appand_messages(
                conversation_id=id, messages=[user_message, assistent_message]
            )
            assert result.is_ok()

            result = await ConversationUsecases.Instance().find_conversation(id)
            assert result.is_ok()
            conversation = result.get_ok()
            assert len(conversation.messages) == 2
            assert conversation.messages[0].role == user_message.role
            assert conversation.messages[1].role == assistent_message.role
            assert len(conversation.messages[0].nodes) == 0
            assert len(conversation.messages[1].nodes) == 1

        await run_test_with_mongo(run)

    async def test_add_context(self):
        async def run():
            id = await create_conversatoin()

            result = await ConversationUsecases.Instance().add_context(
                conversation_id=id, courseId=COURSE_DUMMY_ID
            )

            assert result.is_ok()

            result = await ConversationUsecases.Instance().find_conversation(id)
            if result.is_error():
                logger.error(result.get_error())
            assert result.is_ok()
            assert result.get_ok().context.courseId == COURSE_DUMMY_ID

        await run_test_with_mongo(run)

    async def test_add_context_missing_conversation(self):
        async def run():
            result = await ConversationUsecases.Instance().add_context(
                conversation_id=CONVERSATION_DUMMY_ID, courseId=COURSE_DUMMY_ID
            )

            assert result.is_error()
            assert isinstance(result.get_error(), NotFoundException)

        await run_test_with_mongo(run)
