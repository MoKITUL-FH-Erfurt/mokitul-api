from functools import lru_cache

from api.settings import EMBEDDING_DEVICE, OLLAMA_HOST, MODEL, CONTEXT_LENGTH, EMBEDDING_MODEL
from llama_index.llms.ollama import Ollama
from llama_index.core.base.llms.base import BaseLLM

from llama_index.embeddings.huggingface import HuggingFaceEmbedding


@lru_cache
def get_embedding_model() -> HuggingFaceEmbedding:
    embeddings = HuggingFaceEmbedding(
        device=EMBEDDING_DEVICE,
        normalize=False,
        model_name=EMBEDDING_MODEL,
    )

    return embeddings

def get_llm():
    llm = Ollama(
        model=MODEL,
        base_url=OLLAMA_HOST,
        temperature=0.3,
        num_ctx=CONTEXT_LENGTH,
        request_timeout=120
    )

    return llm
