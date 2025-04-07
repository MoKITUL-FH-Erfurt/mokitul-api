import logging

from api.model import (
    ChatScope,
    Conversation,
    Message,
    MessageRequest,
    ResponseMessage,
)
from api.utils.chains import get_posix_timestamp
from fastapi import APIRouter

from llama_index.core.llms import ChatMessage, MessageRole
from pydantic import BaseModel
from usecases.conversation_usecases import ConversationUsecases
from usecases.convert_pdf_to_markdown import PdfConverterUsecase
from usecases.download_file_from_moodle import MoodleUsecase
from usecases.ask_llm import AskLLMUsecase
from usecases.llm import LLMResponse
from usecases.model.dto import Document
from usecases.vector_db import VectorDBUsecases

logger = logging.getLogger(__name__)


def map_message(message: Message):
    return ChatMessage(
        role=MessageRole(message.role), content=message.content, additional_kwargs={}
    )


def map_messages(messages: list[Message]):
    return [map_message(message) for message in messages]


# v1 of the app


class ConvesationAPIConfig(BaseModel):
    start_llm_path: bool


class ConversationAPI:
    _config: ConvesationAPIConfig
    _router: APIRouter

    def __init__(self, config: ConvesationAPIConfig) -> None:
        self._config = config
        self._router = APIRouter()
        if config.start_llm_path:
            self.register_llm_path()
        self.register_basic_api()

    def get_rounter(self) -> APIRouter:
        return self._router

    def register_basic_api(self):
        @self._router.get("/")
        async def get_conversation(
            user_id: str,
            course_id: str | None = None,
            file_id: str | None = None,
            scope: str | None = None,
        ):
            result = await ConversationUsecases.Instance().find_by_context(
                user_id=user_id, course_id=course_id, file_id=file_id, scope=scope
            )
            # await sleep(120);
            if result.is_error():
                raise result.get_error()
            return result.get_ok()

        @self._router.post("/")
        async def create_conversation(conversation: Conversation):
            logger.debug(f"Create Conversation {conversation}")
            result = await ConversationUsecases.Instance().create_conversation(
                conversation
            )
            if result.is_ok():
                return {"id": result.get_ok()}
            else:
                raise result.get_error()

        @self._router.get("/{user_id}")
        async def all_conversations(user_id: str):
            result = await ConversationUsecases.Instance().find_user_conversations(
                user_id=user_id
            )
            if result.is_error():
                raise result.get_error()
            return result.get_ok()

        @self._router.put("/{conversation_id}")
        async def update_conversation(conversation_id: str, conversation_update: dict):
            result = await ConversationUsecases.Instance().find_conversation(
                conversation_id
            )

            if result.is_error():
                raise result.get_error()

            given_conversation = Conversation(**conversation_update)

            result = await ConversationUsecases.Instance().update_conversation(
                id=conversation_id, conversation=given_conversation
            )

            if result.is_error():
                raise result.get_error()

            return {"id": conversation_id}

        @self._router.delete("/{conversation_id}")
        async def delete_all_conversations(conversation_id: str):
            result = await ConversationUsecases.Instance().delete_conversation(
                conversation_id=conversation_id
            )

            if result.is_error():
                raise result.get_error()

            return

        @self._router.put("/{conversation_id}/context/course")
        async def add_course_context(conversation_id: str, courseId: str):
            result = await ConversationUsecases.Instance().add_context(
                conversation_id=conversation_id, courseId=courseId
            )
            if result.is_error():
                raise result.get_error()

            return {"id": conversation_id}

    def register_llm_path(self):
        @self._router.put("/{conversation_id}/message")
        async def send_message(conversation_id: str, message: MessageRequest):
            result = await ConversationUsecases.Instance().find_conversation(
                conversation_id
            )

            if result.is_error():
                raise result.get_error()
            conversation = result.get_ok()

            user_message = Message(
                role="user", content=message.message, timestamp=get_posix_timestamp()
            )

            file_ids = conversation.context.fileIds
            logger.error(conversation.context)
            if conversation.context.scope == ChatScope.course.value:
                assert conversation.context.courseId is not None
                logging.info(
                    "Getting files for course: ", conversation.context.courseId
                )
                file_ids = MoodleUsecase.Instance().get_file_ids_to_course(
                    course_id=conversation.context.courseId
                )

            file_ids.remove("") if "" in file_ids else None
            logging.info(f"Ensuring File IDs: {file_ids}")
            if result.is_error():
                raise result.get_error()

            conversation.messages.append(user_message)

            for file_id in file_ids:
                file = MoodleUsecase.Instance().download_file(file_id=file_id)
                if file.has_been_downloaded:
                    metadata = {
                        "course_id": conversation.context.courseId,
                        "file_id": file_id,
                        "filename": file.org_filename,
                    }
                    pages = PdfConverterUsecase.Instance().run(file=file.local_filename)

                    VectorDBUsecases.Instance().store_doc(
                        doc=Document(id=file_id, content=pages, metadata=metadata)
                    )

            filters = {"file_id": file_ids}
            response = AskLLMUsecase.Instance().run(
                messages=conversation.messages, filters=filters, model=message.model
            )

            if response.is_error():
                raise response.get_error()

            response_message: LLMResponse = response.get_ok()

            result = await ConversationUsecases.Instance().appand_messages(
                conversation_id=conversation_id,
                messages=[
                    user_message,
                    Message(
                        role="assistant",
                        content=response_message.response,
                        timestamp=get_posix_timestamp(),
                        nodes=response_message.nodes,
                    ),
                ],
            )

            if result.is_error():
                raise result.get_error()

            return ResponseMessage(
                conversationId=conversation_id,
                response=response_message.response,
                timestamp=get_posix_timestamp(),
                nodes=response_message.nodes,
            )
