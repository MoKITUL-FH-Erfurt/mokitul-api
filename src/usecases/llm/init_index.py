from typing import Optional
from core.singelton import SingletonMeta
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.postprocessor.colbert_rerank import ColbertRerank
from pydantic import BaseModel


class LlamaIndexRAGConfig(BaseModel):
    """
    Configuration for the LlamaIndexRAGLLM
    """

    embedding_mode: str

    top_n_count_reranker: int
    top_n_count_dens: int
    top_n_count_sparse: int
    device: str

    ollama_url: str
    llm_model: str
    timeout: float

    context_window: int


class LLamaIndexHolder(metaclass=SingletonMeta):
    _index: Optional[VectorStoreIndex]
    _colbert_reranker: Optional[ColbertRerank]
    _embedding_model: Optional[HuggingFaceEmbedding]
    _llm: Optional[Ollama]

    def __init__(
        self,
        vector_store: BasePydanticVectorStore,
        config: LlamaIndexRAGConfig,
    ):
        self._config = config

        self._colbert_reranker = ColbertRerank(
            top_n=config.top_n_count_reranker,
            model="colbert-ir/colbertv2.0",
            tokenizer="colbert-ir/colbertv2.0",
            keep_retrieval_score=True,
        )

        self._embedding_model = HuggingFaceEmbedding(
            model_name=config.embedding_mode,
            device=config.device,
            trust_remote_code=True,
        )

        self._llm = Ollama(
            model=self._config.llm_model,
            base_url=self._config.ollama_url,
            request_timeout=self._config.timeout,
            context_window=self._config.context_window,
        )

        self._index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, embed_model=self._embedding_model
        )

    @classmethod
    def create(
        cls,
        vector_store: BasePydanticVectorStore,
        config: LlamaIndexRAGConfig,
    ):
        if cls not in SingletonMeta._instances:
            return cls(vector_store, config)
        else:
            raise RuntimeError("Singleton instance already created.")

    @classmethod
    def Instance(cls) -> "LLamaIndexHolder":
        if cls not in SingletonMeta._instances:
            raise RuntimeError(
                "Singleton instance has not been created yet. Call `create` first."
            )
        return SingletonMeta._instances[cls]

    def get_index(self) -> VectorStoreIndex:
        assert self._index is not None
        return self._index

    def get_reranker(self) -> ColbertRerank:
        assert self._colbert_reranker is not None
        return self._colbert_reranker

    def get_embedding(self) -> HuggingFaceEmbedding:
        assert self._embedding_model is not None
        return self._embedding_model

    def get_llm(self) -> Ollama:
        assert self._llm is not None
        return self._llm
