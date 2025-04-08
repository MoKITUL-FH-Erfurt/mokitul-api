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


dummy_pdf = "dummy.pdf"

class TestSplitter(unittest.TestCase):
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
        PdfConverterUsecase.create(pdf_converter=MarkerPDFConverter(
            config=MarkerPDFConverterConfig(ollama_host=None,use_llm=False,model=None)
        ))
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
