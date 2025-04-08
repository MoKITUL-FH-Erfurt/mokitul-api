import asyncio
import os
import threading

from core import str_to_bool
from database.implementation import ConversationDatabase
from database.session import DatabaseConfig, MongoDatabaseSession
from pdf_converter.pdf_converter import MarkerPDFConverter, MarkerPDFConverterConfig
from usecases.conversation_usecases import ConversationUsecases
from usecases.convert_pdf_to_markdown import PdfConverterUsecase
from usecases.llm.init_index import LLamaIndexHolder, LlamaIndexRAGConfig
from vector_database.vectore_store import LlamaIndexVectorStore

from config.config_loader import ConfigLoader
from core.request_timer import RequestTimer
from core.settings import (
    CHUNKE_OVERLAP,
    CHUNKE_SIZE,
    CONTEXT_LENGTH,
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
    ENABLE_LLM_PATH,
    ENV_VARS,
    MONGODB_COLLECTION,
    MONGODB_PASSWORD,
    MONGODB_SERVER,
    MONGODB_SERVER_PORT,
    MONGODB_USER,
    OLLAMA_HOST,
    QDRANT_COLLECTION,
    QDRANT_HOST,
    QDRANT_PORT,
    TOP_N_COUNT_DENS,
    TOP_N_COUNT_RERANKER,
    TOP_N_COUNT_SPARSE,
    LOG_LEVEL,
    MODEL,
    MOODLE_API_KEY,
    MOODLE_HOST,
    REQUST_TIMEOUT,
    init_logging,
)
from definitions import DATA_DIR
from moodle.downloads import MoodleClientImplementation, MoodleConfig
from usecases.download_file_from_moodle import MoodleUsecase
from usecases.vector_db import VectorDBUsecases


class Application:
    """
    Application class for managing the application lifecycle.
    It is a singleton class that holds the application state and configuration.

    Allows a startup "light" mode that only loads the configuration.
    This setup is nessary for the fastapi server to start up.
    We use uvicorn to start the server.
    for some reason inside fastapi can't access the singleton instance that hast been created before.
    This is a workaround to load the config before the server starts, allowing access to the config.

    The application itself will be started inside of fastapi.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                cls._instance = instance
        return cls._instance

    @staticmethod
    def Instance() -> "Application":
        return Application()

    def __init__(self) -> None:
        ...

    def startup_light(self):
        """
        Will only load the config and not start the application.
        """
        ConfigLoader.load_config(ENV_VARS)

    async def _async_startup(self):
        timer = RequestTimer()
        timer.start("Async Application startup")
        config_loader = ConfigLoader.get_instance()
        MongoDatabaseSession.init_database(
            DatabaseConfig(
                host=config_loader.get_value(MONGODB_SERVER),
                port=config_loader.get_value(MONGODB_SERVER_PORT),
                database_name=config_loader.get_value(MONGODB_COLLECTION),
                username=config_loader.get_value(MONGODB_USER),
                password=config_loader.get_value(MONGODB_PASSWORD),
            )
        )

        conversation_database = ConversationDatabase()
        await conversation_database.start()
        ConversationUsecases.create(database=conversation_database)
        timer.end()

    def startup(self):
        from vector_database.vectore_store import LlamaIndexVectorStoreSession
        from usecases.ask_llm import AskLLMUsecase
        from vector_database.vectore_store import LlamaIndexVectorStoreConfig
        from usecases.llm.llama_index_rag_llm import (
            LLamaIndexRAGLLM,
        )

        ConfigLoader.load_config(ENV_VARS)
        config_loader = ConfigLoader.get_instance()
        init_logging(config_loader.get_value(LOG_LEVEL))
        timer = RequestTimer()
        timer.start("Application startup")

        timer.checkpoint("MongoDB Startup")
        if str_to_bool(config_loader.get_value(ENABLE_LLM_PATH)):
            LlamaIndexVectorStoreSession.init_database(
                config=LlamaIndexVectorStoreConfig(
                    qdrant_host=config_loader.get_value(QDRANT_HOST),
                    qdrant_port=int(config_loader.get_value(QDRANT_PORT)),
                    collection=config_loader.get_value(QDRANT_COLLECTION),
                    embedding_mode=config_loader.get_value(EMBEDDING_MODEL),
                    top_n_count_dens=int(config_loader.get_value(TOP_N_COUNT_DENS)),
                    top_n_count_sparse=int(config_loader.get_value(TOP_N_COUNT_SPARSE)),
                    top_n_count_reranker=int(
                        config_loader.get_value(TOP_N_COUNT_RERANKER)
                    ),
                    chunk_size=int(config_loader.get_value(CHUNKE_SIZE)),
                    chunk_overlap=int(config_loader.get_value(CHUNKE_OVERLAP)),
                    device=config_loader.get_value(EMBEDDING_DEVICE),
                )
            )
            timer.checkpoint("Init VektorDB Connection")

            llm_config = LlamaIndexRAGConfig(
                embedding_mode=config_loader.get_value(EMBEDDING_MODEL),
                top_n_count_dens=int(config_loader.get_value(TOP_N_COUNT_DENS)),
                top_n_count_sparse=int(config_loader.get_value(TOP_N_COUNT_SPARSE)),
                top_n_count_reranker=int(config_loader.get_value(TOP_N_COUNT_RERANKER)),
                device=config_loader.get_value(EMBEDDING_DEVICE),
                ollama_url=config_loader.get_value(OLLAMA_HOST),
                llm_model=config_loader.get_value(MODEL),
                timeout=float(config_loader.get_value(REQUST_TIMEOUT)),
                context_window=int(config_loader.get_value(CONTEXT_LENGTH)),
            )

            LLamaIndexHolder.create(
                vector_store=LlamaIndexVectorStoreSession.get_instance().get_database(),
                config=llm_config,
            )

            AskLLMUsecase.create(
                llm=LLamaIndexRAGLLM(
                    config=llm_config,
                )
            )

            VectorDBUsecases.create(
                vector_db=LlamaIndexVectorStore(
                    config=LlamaIndexVectorStoreConfig(
                        qdrant_host=config_loader.get_value(QDRANT_HOST),
                        qdrant_port=int(config_loader.get_value(QDRANT_PORT)),
                        collection=config_loader.get_value(QDRANT_COLLECTION),
                        embedding_mode=config_loader.get_value(EMBEDDING_MODEL),
                        top_n_count_dens=int(config_loader.get_value(TOP_N_COUNT_DENS)),
                        top_n_count_sparse=int(
                            config_loader.get_value(TOP_N_COUNT_SPARSE)
                        ),
                        top_n_count_reranker=int(
                            config_loader.get_value(TOP_N_COUNT_RERANKER)
                        ),
                        device=config_loader.get_value(EMBEDDING_DEVICE),
                        chunk_size=int(config_loader.get_value(CHUNKE_SIZE)),
                        chunk_overlap=int(config_loader.get_value(CHUNKE_OVERLAP)),
                    ),
                    vector_store=LlamaIndexVectorStoreSession.get_instance().get_database(),
                )
            )

            PdfConverterUsecase.create(
                pdf_converter=MarkerPDFConverter(
                    config=MarkerPDFConverterConfig(
                        ollama_host=None, model=None, use_llm=False
                    )
                )
            )

        MoodleUsecase.create(
            MoodleClientImplementation(
                config=MoodleConfig(
                    timeout=float(config_loader.get_value(REQUST_TIMEOUT)),
                    file_store_location=DATA_DIR,
                    moodle_host=config_loader.get_value(MOODLE_HOST),
                    api_key=config_loader.get_value(MOODLE_API_KEY),
                )
            )
        )

        timer.checkpoint("Init Usecase")

        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        loop = asyncio.get_event_loop()
        loop.create_task(self._async_startup())

        timer.checkpoint("Created Data Dir")
        timer.end()
