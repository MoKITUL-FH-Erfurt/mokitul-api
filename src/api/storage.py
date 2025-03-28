from functools import lru_cache
from api.settings import CHROMA_DB_HOST, CHROMA_DB_PORT

from api.utils.chains import get_embedding_model
from api.utils.function_tools import list_to_tuple
from definitions import DATA_DIR

import os

from llama_index.core import (
    Document,
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
)

from llama_index.vector_stores.chroma import ChromaVectorStore

from chromadb import HttpClient

def get_chroma_index():
    chroma_client = HttpClient(host=CHROMA_DB_HOST,port=CHROMA_DB_PORT)

    chroma_collection = chroma_client.get_or_create_collection("mokitul-test")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=get_embedding_model(),
        storage_context=storage_context,
        show_progress=True
    )

    return index

def insert_document_into_index(document: Document) -> None:
    ...

def insert_documents_into_index(documents: list[Document]) -> None:
    ...
