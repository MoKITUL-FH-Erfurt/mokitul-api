from typing import Any, Dict, List, Optional, Tuple, cast
import logging
import re

from huggingface_hub import file_exists
from llama_index.core.base.embeddings.base import similarity
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, NodeRelationship, RelatedNodeType
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.core import Document as LlamaIndexDoc, Response
from llama_index.core.node_parser.file.markdown import MarkdownNodeParser
from pydantic import BaseModel
from qdrant_client.http import models
from core import Result
from usecases.llm.init_index import LLamaIndexHolder
from usecases.model.dto import Document, Node
from usecases.storage import VectorDatabase


from qdrant_client import QdrantClient

from llama_index.core import VectorStoreIndex
from llama_index.postprocessor.colbert_rerank import ColbertRerank
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class LlamaIndexVectorStoreConfig(BaseModel):
    """
    Configuration for the LlamaIndexVectorStore.
    """

    qdrant_host: str
    qdrant_port: int
    collection: str
    embedding_mode: str
    top_n_count_reranker: int
    top_n_count_dens: int
    top_n_count_sparse: int
    chunk_size: int
    chunk_overlap: int
    device: str


class LlamaIndexVectorStoreSession:
    """
    LlamaIndexVectorStoreSession is a singleton class that holds the database instance.
    Allows to reuse the same database instance across the application.
    """

    _instance = None
    _vectore_store: Optional[BasePydanticVectorStore] = None
    _config: Optional[LlamaIndexVectorStoreConfig]
    _client: Optional[QdrantClient] = None

    def __new__(cls, config: Optional[LlamaIndexVectorStoreConfig] = None):
        if cls._instance is None:
            from llama_index.core import Settings

            assert config is not None, (
                "Configuration must be provided for the first initialization."
            )
            Settings.llm = None  # type: ignore
            cls._instance = super().__new__(cls)
            vectore_store, client = cls._build_qdrant_vector_store(config)
            cls._instance._initialize(
                vectore_store=vectore_store, config=config, client=client
            )
        return cls._instance

    @staticmethod
    def _build_qdrant_vector_store(
        config: LlamaIndexVectorStoreConfig,
    ) -> Tuple[BasePydanticVectorStore, QdrantClient]:
        """Build the MongoDB connection URL from the configuration."""
        client = QdrantClient(host=config.qdrant_host, port=config.qdrant_port)
        vector_store = QdrantVectorStore(
            config.collection,
            client=client,
            enable_hybrid=True,
            batch_size=20,
        )
        return (vector_store, client)

    @staticmethod
    def init_database(config: LlamaIndexVectorStoreConfig):
        LlamaIndexVectorStoreSession(config)

    @staticmethod
    def get_instance() -> "LlamaIndexVectorStoreSession":
        return LlamaIndexVectorStoreSession()

    def _initialize(
        self,
        vectore_store: BasePydanticVectorStore,
        config: LlamaIndexVectorStoreConfig,
        client: QdrantClient,
    ):
        self._vectore_store = vectore_store
        self._config = config
        self._client = client

    def get_database(self) -> BasePydanticVectorStore:
        assert self._vectore_store is not None, "Database is not initialized."
        return self._vectore_store

    def get_config(self) -> LlamaIndexVectorStoreConfig:
        assert self._config is not None, "Database is not initialized."
        return self._config

    def get_qdrant_client(self) -> QdrantClient:
        assert self._client is not None, "Database is not initialized."
        return self._client


class NodeSplitterConfig(BaseModel):
    chunk_size: int
    chunk_overlap: int


class NodeSplitter:
    _config: NodeSplitterConfig

    PageSplitPattern = r"---- Ende Seite (\d+) ----"
    MetaDateStartPageKey = "start_page"
    MetaDateUpToPageKey = "up_to_page"

    def __init__(self, config: NodeSplitterConfig) -> None:
        self._config = config

    def _merge_doc(self, pages: list[str]) -> str:
        content = ""
        for i in range(len(pages)):
            content = f"""{content}\n\n{pages[i]}\n\n---- Ende Seite {i + 1} ----\n\n"""
        return content

    def split_documents(self, doc: Document) -> List[BaseNode]:
        content = ""
        if isinstance(doc.content, list):
            content = self._merge_doc(pages=doc.content)
        else:
            content = doc.content

        doc_llama_index = LlamaIndexDoc(text=content)  # type: ignore
        doc_llama_index.excluded_llm_metadata_keys = ["course_id", "file_id"]
        doc_llama_index.metadata = {**doc_llama_index.metadata, **doc.metadata}
        nodes = SentenceSplitter(
            chunk_size=self._config.chunk_size, chunk_overlap=self._config.chunk_overlap
        ).get_nodes_from_documents(documents=[doc_llama_index])
        page_number = 1
        for i in range(len(nodes)):
            node = nodes[i]
            matches = re.findall(self.PageSplitPattern, node.get_content())
            node.metadata[self.MetaDateStartPageKey] = page_number
            if len(matches) > 0:
                page_number = matches[len(matches) - 1]
                page_number = int(page_number) + 1
            node.metadata[self.MetaDateUpToPageKey] = page_number
            if i == 0:
                continue
            prev_node = nodes[i - 1]
            node.relationships[NodeRelationship.PREVIOUS] = (
                prev_node.as_related_node_info()
            )

            prev_node.relationships[NodeRelationship.NEXT] = node.as_related_node_info()

        return nodes


class LlamaIndexVectorStore(VectorDatabase):
    """
    implementation of the VectorDatabase interface using LlamaIndex.
    """

    _note_splitter: NodeSplitter
    _config: LlamaIndexVectorStoreConfig

    def __init__(
        self, vector_store: BasePydanticVectorStore, config: LlamaIndexVectorStoreConfig
    ):
        self._config = config
        self._note_splitter = NodeSplitter(
            config=NodeSplitterConfig(
                chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
            )
        )

        colbert_reranker = LLamaIndexHolder.Instance().get_reranker()
        embedding_model = LLamaIndexHolder.Instance().get_embedding()

        self._index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, embed_model=embedding_model
        )

        self._query_engine = self._index.as_query_engine(
            llm=None,
            similarity_top_k=self._config.top_n_count_dens,
            sparse_top_k=self._config.top_n_count_dens,
            node_postprocessors=[colbert_reranker],
            vector_store_query_mode="hybrid",
        )

    def create_document(self, doc: Document) -> Result[None]:
        try:
            nodes = self._note_splitter.split_documents(doc=doc)
            self._index.insert_nodes(nodes=nodes)
            logging.getLogger(__name__).info(f"stored {doc.id}")
            return Result.Ok(None)
        except Exception as e:
            logging.getLogger(__name__).error(f"{e}")
            return Result.Err(e)

    def find_similar_nodes(self, query: str) -> Result[List[Node]]:
        try:
            response = cast(Response, self._query_engine.query(query))
            llama_index_nodes = response.source_nodes
            nodes = [
                Node(
                    id=node.id_,
                    content=node.text,
                    metadata=node.metadata,
                    relations=[],
                    similarity_score=node.get_score(raise_error=False),
                )
                for node in llama_index_nodes
            ]
            return Result.Ok(nodes)

        except Exception as e:
            return Result.Err(e)

    def does_object_with_metadata_exist(self, metadata: Dict[str, str]) -> Result[bool]:
        try:
            client = LlamaIndexVectorStoreSession.get_instance().get_qdrant_client()
            if not client.collection_exists(self._config.collection):
                return Result.Ok(False)

            qdrant_nodes, point_id = client.scroll(
                collection_name=self._config.collection,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=metadata[key]),
                        )
                        for key in metadata.keys()
                    ]
                ),
            )
            return Result.Ok(len(qdrant_nodes) > 0)
        except Exception as e:
            return Result.Err(e)
