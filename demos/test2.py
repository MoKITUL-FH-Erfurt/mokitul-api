import os
from api.utils.chains import get_llm
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)

from llama_index.core.chat_engine.types import ChatMode

from llama_index.llms.lmstudio import LMStudio

sys_prompt = """

"""
Settings.llm = LMStudio(
    model_name="bartowski/Llama-3-SauerkrautLM-8b-Instruct-GGUF",
    base_url="http://127.0.0.1:4040/v1",
    temperature=0.7,
)

# Settings.llm = OpenAI(model="bartowski/Llama-3-SauerkrautLM-8b-Instruct-GGUF", request_timeout=120.0, api_base="http://localhost:4040/v1", api_key="lm-studio", system_prompt="Du bist ein freundlicher Chatbot welcher stets versucht zu helfen. Du darfst keine falschen aussagen treffen. Bitte beantworte fragen immer in der Sprache des Benutzers.",temperature=0.3)
Settings.embed_model =  "local:BAAI/bge-m3" #local:intfloat/e5-large-v2"

# check if storage already exists
PERSIST_DIR = "./storage"
if not os.path.exists(PERSIST_DIR):
    # load the documents and create the index
    documents = SimpleDirectoryReader("./data/zfq").load_data()
    print(documents)
    index = VectorStoreIndex.from_documents(documents)
    # store it for later
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

messages = [
    # ChatMessage(role="user", content="Hey how are you?", additional_kwargs={}),
    # ChatMessage(role="assistant", content="I am fine, thank you. How can I help you today?", additional_kwargs={}),
    #ChatMessage(role="user", content="Please tell me Which GPUs were utilized in the training of Llama2?", additional_kwargs={}),
    #ChatMessage(role="assistant", content="According to the information provided, the GPUs used for pretraining LLaMA 2 models were of type A100-80GB with a Thermal Design Power (TDP) of either 350W or 400W.", additional_kwargs={}),
]   

prompt = """Gebe mir eine Kurzbeschreibung des Moduls Vekehr und Umwelt. Gehe auf den Workload und die Lerninhalte ein.
                          Anworte auf Deutsch.
                          Wichtig ist das keine Informationen fehlen und keine Falschinformationen gegeben werden.
                         """

query_engine = index.as_query_engine()


print(query_engine.query(prompt))
print("\n\n\n\n --------------------------------- \n\n\n\n")

chat_engine = index.as_chat_engine(chat_mode=ChatMode.CONDENSE_PLUS_CONTEXT)
from llama_index.core.chat_engine import SimpleChatEngine

# chat_engine = SimpleChatEngine.from_defaults(llm=get_llm(),system_prompt="You are a instructor at a university and you are asked to answer questions about the course material. The course material is provided to you via context. You should ALWAYS reference the material first.")

# print(chat_engine.chat(message="Tell me which GPUs were utilized in the training of Llama2. Also tell me the page and document you found the information in. Thank you in advance!", chat_history=messages))
#print(chat_engine.chat(message="Hey!", chat_history=messages))
# print(chat_engine.chat(message="Hey!", chat_history=messages))

# CONDESE_PLUS_CONTEXT
# --> FileRetrieverAgent
# --> Code Interpreter

#chat_engine.chat_repl()


print(chat_engine.chat(prompt))
