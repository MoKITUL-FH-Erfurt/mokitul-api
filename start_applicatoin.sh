
# mongodb settings
export MONGODB_USER=root
export MONGODB_PASSWORD=example
export MONGODB_SERVER=127.0.0.1
export MONGODB_COLLECTION=mokitul_api
export MONGODB_SERVER_PORT=27017

export OLLAMA_HOST=https://ollama.draco.uni-jena.de
export MODEL=llama3.1
export EMBEDDING_DEVICE=mps # cuda (nvdia), mps (mac), cpu(any other)
export EMBEDDING_MODEL=BAAI/bge-m3
export CONTEXT_LENGTH=8192

# qdrant settings
export QDRANT_HOST=127.0.0.1
export QDRANT_PORT=6333
export QDRANT_API_KEY=
export QDRANT_COLLECTION=mokitul_api


# defines the number of chunks that are retrived from the vector database
export TOP_N_COUNT_RERANKER=10
export TOP_N_COUNT_DENS=10
export TOP_N_COUNT_SPARSS=10
export CHUNKE_SIZE=128
export CHUNKE_OVERLAP=16

export MOODLE_HOST=http://127.0.0.1:80
export MOODLE_API_KEY=dummy
export REQUST_TIMEOUT=600.0

export LOG_LEVEL=INFO
export ROOT_PATH=/api
export PORT=8000
export WORKER=1

export ENABLE_LLM_PATH=True


# the device used to run the embedding model
export TOKENIZERS_PARALLELISM=True

python ./src/main.py
