# Configuration Variables

This document outlines the configuration variables used in the Mokitul API.
Each variable is categorized based on its functionality, with default values and descriptions provided for clarity.
At the moment we support only environment variables.

## 🔮 AI Settings

| Variable           | Default Value                                  | Description                                              |
|--------------------|------------------------------------------------|----------------------------------------------------------|
| `OLLAMA_HOST`      | `http://127.0.0.1:11434`                        | Host address for the Ollama inference server.            |
| `MODEL`            | `llama3.1`                                     | Primary LLM model used.                                  |
| `EMBEDDING_MODEL`  | `nomic-ai/nomic-embed-text-v2-moe`             | Embedding model for vector representation.               |
| `EMBEDDING_DEVICE` | `cpu`                                          | Device used for embeddings (`cpu` or `cuda`).            |
| `CONTEXT_LENGTH`   | `8192`                                         | Max token context length supported by the model.         |

## 🧠 Qdrant (Vector DB)

| Variable            | Default Value | Description                                       |
|---------------------|---------------|---------------------------------------------------|
| `QDRANT_HOST`        | *None*        | Host of the Qdrant server.                        |
| `QDRANT_PORT`        | `6333`        | Port for the Qdrant server.                       |
| `QDRANT_API_KEY`     | `""`          | API key for Qdrant, if authentication is enabled. |
| `QDRANT_COLLECTION`  | `mokitul_ai`  | Qdrant collection name for vector storage.        |

## 🍃 MongoDB

| Variable              | Default Value   | Description                                 |
|-----------------------|-----------------|---------------------------------------------|
| `MONGODB_USER`         | *None*          | MongoDB username.                           |
| `MONGODB_PASSWORD`     | *None*          | MongoDB password.                           |
| `MONGODB_SERVER`       | *None*          | MongoDB server host.                        |
| `MONGODB_SERVER_PORT`  | `27017`         | MongoDB server port.                        |
| `MONGODB_COLLECTION`   | `mokitul_api`   | Default MongoDB collection name.            |

## ⚙️ Base Settings

| Variable          | Default Value | Description                                       |
|-------------------|---------------|---------------------------------------------------|
| `LOG_LEVEL`        | `INFO`        | Logging level (`DEBUG`, `INFO`, `WARNING`, etc).  |
| `PORT`             | `8000`        | Port on which the app runs.                      |
| `ROOT_PATH`        | `/api`        | Root path for the API endpoints.                 |
| `ENABLE_LLM_PATH`  | `True`        | Toggle for enabling LLM routes.                  |
| `WORKER`           | `1`           | Number of workers to run.                        |

## 🎓 Moodle Integration

| Variable         | Default Value | Description                            |
|------------------|---------------|----------------------------------------|
| `MOODLE_HOST`     | *None*        | Base URL of the Moodle instance.       |
| `MOODLE_API_KEY`  | *None*        | API key for accessing Moodle.          |
| `REQUST_TIMEOUT`  | `60.0`        | Request timeout (in seconds).          |

## 📚 Retrieval Parameters

| Variable                | Default Value | Description                                      |
|-------------------------|---------------|--------------------------------------------------|
| `TOP_N_COUNT_RERANKER`  | `10`          | Top-N results after re-ranking.                 |
| `TOP_N_COUNT_DENS`      | `10`          | Top-N results from dense retriever.             |
| `TOP_N_COUNT_SPARSE`    | `10`          | Top-N results from sparse retriever.            |
| `CHUNKE_SIZE`           | `128`         | Number of tokens per document chunk.            |
| `CHUNKE_OVERLAP`        | `20`          | Overlap between chunks (in tokens).             |
