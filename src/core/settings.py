import os
from typing import Optional
import logging


class ColorFormatter(logging.Formatter):
    # Define ANSI escape codes for colors
    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[1;91m",  # Bold Red
    }
    RESET = "\033[0m"  # Reset color

    def format(self, record):
        # Add color to the log level
        level_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"
        return super().format(record)


def init_logging(log_level: str):
    # Ensure other loggers are set to the same level
    logging.getLogger("PIL").setLevel(log_level)
    handler = logging.StreamHandler()
    formatter = ColorFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(handler)
    logger.debug("Colored logging initialized")


# ai
OLLAMA_HOST = "OLLAMA_HOST"
MODEL = "MODEL"
EMBEDDING_MODEL = "EMBEDDING_MODEL"
EMBEDDING_DEVICE = "EMBEDDING_DEVICE"
CONTEXT_LENGTH = "CONTEXT_LENGTH"

# qdrant
QDRANT_HOST = "QDRANT_HOST"
QDRANT_PORT = "QDRANT_PORT"
QDRANT_API_KEY = "QDRANT_API_KEY"
QDRANT_COLLECTION = "QDRANT_COLLECTION"

# mongo
MONGODB_USER = "MONGODB_USER"
MONGODB_PASSWORD = "MONGODB_PASSWORD"
MONGODB_SERVER = "MONGODB_SERVER"
MONGODB_COLLECTION = "MONGODB_COLLECTION"
MONGODB_SERVER_PORT = "MONGODB_SERVER_PORT"

# base
LOG_LEVEL = "LOG_LEVEL"
PORT = "PORT"
ROOT_PATH = "ROOT_PATH"
ENABLE_LLM_PATH = "ENABLE_LLM_PATH"

# moodle
MOODLE_HOST = "MOODLE_HOST"
MOODLE_API_KEY = "MOODLE_API_KEY"
REQUST_TIMEOUT = "REQUST_TIMEOUT"

# retrival
TOP_N_COUNT_RERANKER = "TOP_N_COUNT_RERANKER"
TOP_N_COUNT_DENS = "TOP_N_COUNT_DENS"
TOP_N_COUNT_SPARSE = "TOP_N_COUNT_SPARSE"
CHUNKE_SIZE = "CHUNKE_SIZE"
CHUNKE_OVERLAP = "CHUNKE_OVERLAP"
WORKER = "WORKER"


ENV_VARS: dict[str, Optional[str]] = {
    # mongo
    MONGODB_USER: None,
    MONGODB_SERVER: None,
    MONGODB_PASSWORD: None,
    MONGODB_COLLECTION: "mokitul_api",
    MONGODB_SERVER_PORT: "27017",
    # ai
    OLLAMA_HOST: "http://127.0.0.1:11434",
    MODEL: "llama3.1",
    EMBEDDING_DEVICE: "cpu",
    EMBEDDING_MODEL: "nomic-ai/nomic-embed-text-v2-moe",
    CONTEXT_LENGTH: "8192",
    # qdrant
    QDRANT_HOST: None,
    QDRANT_PORT: "6333",
    QDRANT_API_KEY: "",
    QDRANT_COLLECTION: "mokitul_ai",
    # retrival
    TOP_N_COUNT_RERANKER: "10",
    TOP_N_COUNT_DENS: "10",
    TOP_N_COUNT_SPARSE: "10",
    CHUNKE_SIZE: "128",
    CHUNKE_OVERLAP: "20",
    # moodle
    MOODLE_HOST: None,
    MOODLE_API_KEY: None,
    REQUST_TIMEOUT: "60.0",
    # base
    LOG_LEVEL: "INFO",
    ROOT_PATH: "/api",
    PORT: "8000",
    ENABLE_LLM_PATH: "True",
    WORKER: "1",
}
