import logging
from urllib.parse import urlencode
from api.routes.v1.conversations import ConversationAPI, ConvesationAPIConfig
from httpx import AsyncClient
from typing import Callable
import unittest
from api.model import ChatScope, Context, Conversation, MessageRequest
from api.routes.moodle import router as MoodleRouter
from api.utils.chains import get_posix_timestamp
from fastapi.testclient import TestClient


from database.implementation import ConversationDatabase
from database.session import DatabaseConfig, MongoDatabaseSession
from fastapi import FastAPI
from moodle.downloads import MoodleClient, MoodleFile
from pdf_converter.pdf_converter import MarkerPDFConverter, MarkerPDFConverterConfig
from testcontainers.mongodb import MongoDbContainer
from testcontainers.qdrant import QdrantContainer

from core.settings import init_logging
from usecases.ask_llm import AskLLMUsecase
from usecases.conversation_usecases import ConversationUsecases
from usecases.convert_pdf_to_markdown import PdfConverterUsecase
from usecases.download_file_from_moodle import MoodleUsecase
from usecases.llm.init_index import LLamaIndexHolder, LlamaIndexRAGConfig
from usecases.llm.llama_index_rag_llm import LLamaIndexRAGLLM
from usecases.vector_db import VectorDBUsecases
from vector_database.vectore_store import (
    LlamaIndexVectorStore,
    LlamaIndexVectorStoreConfig,
    LlamaIndexVectorStoreSession,
)

USER_DUMMY_ID = "dummy_user_id"
COURSE_DUMMY_ID = "dummy_course_id"
FILE_DUMMY_ID = "dummy_file_id"
FILE_2_DUMMY_ID = "dummy_file_id_2"
CONVERSATION_DUMMY_ID = "65d7b8f9a5e9c3d4f1a2b3c4"
METADATA_DUMMY_ATTRIBUTE = "test_attribute"
METADATA_DUMMY_VALUE = "test_value"

"""
The Tests in this file are just to test if the dataflow works.
They are not for Quality tests.
"""

init_logging("INFO")
logger = logging.getLogger(__name__)


collection = "qdrant_collection"
embedding_mode = "nomic-ai/nomic-embed-text-v2-moe"
chunk_size = 128
chunk_overlap = 32

top_n_count_dens = 5
top_n_count_sparse = 5
top_n_count_reranker = 5
device = "mps"
ollama_url = "http://127.0.0.1:11434"
llm_model = "llama3.2"
timeout = 60.0
context_window = 8192

dummy_pdf = "dummy.pdf"


app = FastAPI(
    root_path="/api",
    title="MoKITUL API",
    version="0.1.0",
)

# PUBLISHED version 1 of the API
v1 = FastAPI()

conversationAPI = ConversationAPI(config=ConvesationAPIConfig(start_llm_path=True))

v1.include_router(
    conversationAPI.get_rounter(), tags=["Conversation"], prefix="/conversations"
)
v1.include_router(MoodleRouter, tags=["Moodle"], prefix="/moodle")

# mount the playground and v1 routers
app.mount("/v1", v1)

# client = TestClient(app)

API_PREFIX: str = "/api/v1"
CONVERATION_PATH = f"{API_PREFIX}/conversations/"


def get_user_conversation_path(user_id: str) -> str:
    return f"{CONVERATION_PATH}{user_id}"


def get_chat_path(chat_id: str) -> str:
    return f"{CONVERATION_PATH}{chat_id}/message"


def query_conversation_path(
    user_id: str,
    course_id: str | None = None,
    file_id: str | None = None,
    scope: str | None = None,
) -> str:
    query_params = {"user_id": user_id}

    if course_id:
        query_params["course_id"] = course_id
    if file_id:
        query_params["file_id"] = file_id
    if scope:
        query_params["scope"] = scope

    return f"{CONVERATION_PATH}?{urlencode(query_params)}"


def create_usecases(
    config_v_db: LlamaIndexVectorStoreConfig, config_llm: LlamaIndexRAGConfig
):
    LlamaIndexVectorStoreSession.init_database(config=config_v_db)
    LLamaIndexHolder.create(
        vector_store=LlamaIndexVectorStoreSession.get_instance().get_database(),
        config=config_llm,
    )
    VectorDBUsecases.create(
        vector_db=LlamaIndexVectorStore(
            vector_store=LlamaIndexVectorStoreSession.get_instance().get_database(),
            config=config_v_db,
        )
    )
    PdfConverterUsecase.create(
        pdf_converter=MarkerPDFConverter(
            config=MarkerPDFConverterConfig(use_llm=False, model=None, ollama_host=None)
        )
    )

    AskLLMUsecase.create(
        llm=LLamaIndexRAGLLM(
            config=config_llm,
        )
    )

    MoodleUsecase.create(MoodleDummyClient())


async def create_database(config: DatabaseConfig):
    MongoDatabaseSession.init_database(config=config)

    conversation_database = ConversationDatabase()
    await conversation_database.start()
    ConversationUsecases.create(conversation_database)


async def run_test_with_container(handle_msg: Callable):
    with QdrantContainer(image="qdrant/qdrant:v1.12.6") as qdrant_container:
        with MongoDbContainer(username="test", password="test") as mongodb:
            config = DatabaseConfig(
                host=mongodb.get_container_host_ip(),
                port=str(mongodb.get_exposed_port(mongodb.port)),
                database_name="test_db",
                username=mongodb.username,
                password=mongodb.password,
            )

            config_v_db = LlamaIndexVectorStoreConfig(
                qdrant_host=qdrant_container.get_container_host_ip(),
                qdrant_port=int(qdrant_container.get_exposed_port(6333)),
                collection=collection,
                embedding_mode=embedding_mode,
                top_n_count_dens=top_n_count_dens,
                top_n_count_sparse=top_n_count_sparse,
                top_n_count_reranker=top_n_count_reranker,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                device=device,
            )

            config_llm = LlamaIndexRAGConfig(
                embedding_mode=embedding_mode,
                top_n_count_dens=top_n_count_dens,
                top_n_count_sparse=top_n_count_sparse,
                top_n_count_reranker=top_n_count_reranker,
                ollama_url=ollama_url,
                llm_model=llm_model,
                timeout=timeout,
                context_window=context_window,
                device=device,
            )
            await create_database(config=config)
            create_usecases(config_v_db=config_v_db, config_llm=config_llm)
            await handle_msg()


class TestVectorDB(unittest.IsolatedAsyncioTestCase):
    async def test_integration_happy_path(self):
        async def run():
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    url=CONVERATION_PATH,
                    json=Conversation(
                        user=USER_DUMMY_ID,
                        messages=[],
                        context=Context(
                            fileIds=[FILE_DUMMY_ID],
                            courseId=COURSE_DUMMY_ID,
                            scope=ChatScope.course.value,
                        ),
                        timestamp=str(get_posix_timestamp()),
                        summary="",
                    ).model_dump(),
                )
                if response.status_code != 200:
                    logger.error(response)
                assert response.status_code == 200
                id = response.json()["id"]

                # check get convertsations on user path
                response = await client.get(
                    url=get_user_conversation_path(USER_DUMMY_ID)
                )
                if response.status_code != 200:
                    logger.error(response)
                assert response.status_code == 200
                assert len(response.json()) == 1
                conversation = response.json()[0]
                assert conversation["user"] == USER_DUMMY_ID

                # check get user convertsations on user path
                response = await client.get(
                    url=query_conversation_path(
                        USER_DUMMY_ID,
                        course_id=COURSE_DUMMY_ID,
                        file_id=FILE_DUMMY_ID,
                        scope=ChatScope.course.value,
                    )
                )
                if response.status_code != 200:
                    logger.error(response)
                assert response.status_code == 200
                logger.error(response.json())
                assert len(response.json()) == 1
                conversation = response.json()[0]
                assert conversation["user"] == USER_DUMMY_ID

                response = await client.get(
                    url=query_conversation_path(
                        USER_DUMMY_ID,
                        course_id="invalid",
                    )
                )
                if response.status_code != 200:
                    logger.error(response)
                assert response.status_code == 200
                assert len(response.json()) == 0

                response = await client.get(
                    url=query_conversation_path(
                        USER_DUMMY_ID,
                        file_id="invalid",
                    )
                )
                if response.status_code != 200:
                    logger.error(response)
                assert response.status_code == 200
                assert len(response.json()) == 0

                response = await client.get(
                    url=query_conversation_path(
                        USER_DUMMY_ID,
                        scope=ChatScope.file.value,
                    )
                )
                if response.status_code != 200:
                    logger.error(response)
                logger.error(response)
                logger.error(response.json())
                assert response.status_code == 200
                assert len(response.json()) == 0

                # test vector

                response = await client.put(
                    url=get_chat_path(id),
                    json=MessageRequest(
                        message="What information do you have access?", model=llm_model
                    ).model_dump(),
                )
                if response.status_code != 200:
                    logger.error(response)
                assert response.status_code == 200
                message = response.json()
                assert message["response"] != ""
                assert len(message["nodes"]) > 0

                response = await client.get(
                    url=get_user_conversation_path(USER_DUMMY_ID)
                )
                if response.status_code != 200:
                    logger.error(response)
                assert response.status_code == 200
                assert len(response.json()) == 1
                chat = response.json()[0]
                assert len(chat["messages"]) == 2

                # Delete Test
                response = await client.delete(url=get_user_conversation_path(id))
                if response.status_code != 200:
                    logger.error(response)
                assert response.status_code == 200
                response = await client.get(
                    url=get_user_conversation_path(USER_DUMMY_ID)
                )
                assert response.status_code == 200
                assert len(response.json()) == 0

        await run_test_with_container(run)


class MoodleDummyClient(MoodleClient):
    def download(self, file_id: str) -> MoodleFile:
        return MoodleFile(
            id=file_id,
            org_filename=dummy_pdf,
            local_filename=dummy_pdf,
            has_been_downloaded=True,
        )

    def get_file_ids_for_course(self, courseId: str) -> list[str]:
        return [FILE_DUMMY_ID, FILE_2_DUMMY_ID]
