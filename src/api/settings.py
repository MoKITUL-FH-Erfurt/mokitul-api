import os

PORT = int(os.environ.get("PORT", 8000))

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("MODEL", "llama3.1")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DEVICE = os.environ.get("EMBEDDING_DEVICE", "cpu")
CONTEXT_LENGTH = os.environ.get("CONTEXT_LENGTH", 8192)

CHROMA_DB_HOST = os.environ.get("CHROMADB_HOST", "localhost")
CHROMA_DB_PORT = int(os.environ.get("CHROMADB_PORT", 8000))

MONGO_DETAILS = os.environ.get("MONGO_DETAILS", "mongodb://root:example@localhost:27017/")

MOODLE_URL = os.environ.get("MOODLE_URL", "https://localhost")
