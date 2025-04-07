from usecases.storage import ImageFileProcessedDatabase, ReverseIndexImageDatabase
from usecases.storage import (
    TextFileProcessedDatabase,
    ReverseIndexDocumentDatabase,
    ReverseIndexProjectDatabase,
    VectorDatabase,
)

"""
This module provides the database instances for the usecases.
"""

from database.project_database import ProjectDatabase


def get_project_database() -> ProjectDatabase:
    from database.project_database import ProjectDatabaseImpl

    return ProjectDatabaseImpl()


def get_file_database() -> TextFileProcessedDatabase:
    from database.processing.files_procced import FilesProccessDatabaseImpl

    return FilesProccessDatabaseImpl()


def get_image_file_database() -> ImageFileProcessedDatabase:
    from database.processing.image_files_processed import ImageFilesProcessDatabaseImpl

    return ImageFilesProcessDatabaseImpl()


def get_vector_database() -> VectorDatabase:
    from vector_database.vectore_store import (
        LlamaIndexVectorStore,
        LlamaIndexVectorStoreSession,
    )

    return LlamaIndexVectorStore(
        vector_store=LlamaIndexVectorStoreSession.get_instance().get_database(),
        config=LlamaIndexVectorStoreSession.get_instance().get_config(),
    )


def get_reverseindex_project_database() -> ReverseIndexProjectDatabase:
    from database.reverse_index_database import ReverseIndexProjectDatabaseImpl

    return ReverseIndexProjectDatabaseImpl()


def get_reverseindex_image_database() -> ReverseIndexImageDatabase:
    from database.reverse_index_database import ReverseIndexImageDatabaseImpl

    return ReverseIndexImageDatabaseImpl()


def get_reverseindex_document_database() -> ReverseIndexDocumentDatabase:
    from database.reverse_index_database import ReverseIndexDocDatabaseImpl

    return ReverseIndexDocDatabaseImpl()
