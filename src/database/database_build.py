
from usecases.storage import (
    VectorDatabase,
)

"""
This module provides the database instances for the usecases.
"""

def get_vector_database() -> VectorDatabase:
    from vector_database.vectore_store import (
        LlamaIndexVectorStore,
        LlamaIndexVectorStoreSession,
    )

    return LlamaIndexVectorStore(
        vector_store=LlamaIndexVectorStoreSession.get_instance().get_database(),
        config=LlamaIndexVectorStoreSession.get_instance().get_config(),
    )
