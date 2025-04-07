import logging
from typing import Callable
import unittest

from api.model import Message
from api.utils.chains import get_posix_timestamp
from pdf_converter.pdf_converter import MarkerPDFConverter, MarkerPDFConverterConfig
from testcontainers.qdrant import QdrantContainer

from core.settings import init_logging
from usecases.ask_llm import AskLLMUsecase
from usecases.convert_pdf_to_markdown import PdfConverterUsecase
from usecases.llm.init_index import LLamaIndexHolder, LlamaIndexRAGConfig
from usecases.llm.llama_index_rag_llm import LLamaIndexRAGLLM
from usecases.model.dto import Document
from usecases.storage import PDFConverter
from usecases.vector_db import VectorDBUsecases
from vector_database.vectore_store import (
    LlamaIndexVectorStore,
    LlamaIndexVectorStoreConfig,
    LlamaIndexVectorStoreSession,
    NodeSplitter,
    NodeSplitterConfig,
)

USER_DUMMY_ID = "dummy_id"
COURSE_DUMMY_ID = "dummy_id"
FILE_DUMMY_ID = "dummy_id"
CONVERSATION_DUMMY_ID = "65d7b8f9a5e9c3d4f1a2b3c4"
METADATA_DUMMY_ATTRIBUTE = "test_attribute"
METADATA_DUMMY_VALUE = "test_value"

"""
The Tests in this file are just to test if the dataflow works.
They are not for Quality tests.
"""

init_logging("INFO")
logger = logging.getLogger(__name__)


doc_content = """
mein Toller Text
---- Ende Seite 1 ----
mein Toller Text
---- Ende Seite 2 ----
mein Toller Text 
---- Ende Seite 3 ----
mein Toller Text 
"""
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


def run_test_with_qdrant(handle_msg: Callable):
    with QdrantContainer(image="qdrant/qdrant:v1.12.6") as qdrant_container:
        # container = qdrant_container.start()
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
        create_usecases(config_v_db=config_v_db, config_llm=config_llm)
        handle_msg()


class TestVectorDB(unittest.TestCase):
    def test_splitter(self):
        splitter = NodeSplitter(
            config=NodeSplitterConfig(chunk_size=100, chunk_overlap=20)
        )

        doc = Document(id="", content=doc_content, metadata={})
        nodes = splitter.split_documents(doc=doc)
        assert len(nodes) == 1
        node = nodes[0]
        assert node.metadata[NodeSplitter.MetaDateStartPageKey] == 1
        assert node.metadata[NodeSplitter.MetaDateUpToPageKey] == 4

    def test_with_splitting_pdf(self):
        pages = PdfConverterUsecase.Instance().run(dummy_pdf)
        assert len(pages) == 4

        splitter = NodeSplitter(
            config=NodeSplitterConfig(chunk_size=100, chunk_overlap=20)
        )

        doc = Document(id="", content=doc_content, metadata={})
        nodes = splitter.split_documents(doc=doc)
        assert len(nodes) == 1
        node = nodes[len(nodes) - 1]
        assert node.metadata[NodeSplitter.MetaDateStartPageKey] == 1
        assert node.metadata[NodeSplitter.MetaDateUpToPageKey] == 4

    def test_splitter_lager_files(self):
        llama2_paper = ""
        with open("llama2_paper.md", "r") as file:
            llama2_paper = file.read()

        splitter = NodeSplitter(
            config=NodeSplitterConfig(chunk_size=100, chunk_overlap=20)
        )

        doc = Document(id="", content=llama2_paper, metadata={})
        nodes = splitter.split_documents(doc=doc)
        assert len(nodes) > 1
        node = nodes[len(nodes) - 1]
        assert node.metadata[NodeSplitter.MetaDateUpToPageKey] == 78

    def test_add_document(self):
        def run():
            content = PdfConverterUsecase.Instance().run(dummy_pdf)
            assert len(content) == 4
            doc = Document(
                id="dummy_id",
                content=content,
                metadata={METADATA_DUMMY_ATTRIBUTE: METADATA_DUMMY_VALUE},
            )
            result = VectorDBUsecases.Instance().store_doc(doc)
            assert result.is_ok()
            result = AskLLMUsecase.Instance().run(
                messages=[
                    Message(
                        role="user",
                        content="What information do you have access to?",
                        timestamp=get_posix_timestamp(),
                    )
                ],
                model=llm_model,
            )
            if result.is_error():
                logger.error(result.get_error().__class__)
                logger.error(result.get_error())
            assert result.is_ok()
            response = result.get_ok()
            assert len(response.nodes) > 0

            # test with metadaten filter
            result = AskLLMUsecase.Instance().run(
                messages=[
                    Message(
                        role="user",
                        content="What information do you have access to?",
                        timestamp=get_posix_timestamp(),
                    )
                ],
                model=llm_model,
                filters={METADATA_DUMMY_ATTRIBUTE: [METADATA_DUMMY_VALUE]},
            )
            if result.is_error():
                logger.error(result.get_error().__class__)
                logger.error(result.get_error())
            assert result.is_ok()
            response = result.get_ok()
            assert len(response.nodes) > 0

            result = AskLLMUsecase.Instance().run(
                messages=[
                    Message(
                        role="user",
                        content="What information do you have access to?",
                        timestamp=get_posix_timestamp(),
                    )
                ],
                model=llm_model,
                filters={METADATA_DUMMY_ATTRIBUTE: ["invalid option"]},
            )
            assert result.is_error()

            result = AskLLMUsecase.Instance().run(
                messages=[
                    Message(
                        role="user",
                        content="What information do you have access to?",
                        timestamp=get_posix_timestamp(),
                    )
                ],
                model=llm_model,
                filters={METADATA_DUMMY_ATTRIBUTE: ["not existing valu"]},
            )
            assert result.is_error()

        run_test_with_qdrant(run)
