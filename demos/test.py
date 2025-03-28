import os
from api.storage import get_chroma_storage
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings


from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from llama_index_client import ChatMessage
from pydantic import Field

Settings.llm = Ollama(model="llama3", request_timeout=120.0, base_url="http://localhost:11434", system_prompt="You are a instructor at a university and you are asked to answer questions about the course material. You can ask me anything about the course material and I will try to answer it as best as I can.")
Settings.embed_model = "local:BAAI/bge-m3"

# check if storage already exists
PERSIST_DIR = "./storage"
if not os.path.exists(PERSIST_DIR):
    # load the documents and create the index
    documents = SimpleDirectoryReader("./data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    # store it for later
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

chat_engine = index.as_chat_engine()

messages = [
    ChatMessage(role="user", content="Hey how are you?", additional_kwargs={}),
    ChatMessage(role="assistant", content="I am fine, thank you. How can I help you today?", additional_kwargs={}),
    #ChatMessage(role="user", content="Please tell me Which GPUs were utilized in the training of Llama2?", additional_kwargs={}),
    #ChatMessage(role="assistant", content="According to the information provided, the GPUs used for pretraining LLaMA 2 models were of type A100-80GB with a Thermal Design Power (TDP) of either 350W or 400W.", additional_kwargs={}),
]   


from api.utils.chains import get_llm
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent

from llama_index.core.tools import QueryEngineTool, FunctionTool

from llama_index.core import PromptTemplate

from llama_index.core.chat_engine.condense_question import CondenseQuestionChatEngine

react_system_header_str = """\

You are designed to help communicating with a user. You are responsible for answering questions, \
    providing summaries and other types of analyses. You also are able to have a conversation with the user. \

## Task
You are asked to help with a variety of tasks.
When the user seems to be interested in a simple conversation, you should use the provided tools to help you with that.
    
## Tools
The provieded tools are designed to help you with the task at hand.
They already provide you with the information you need to answer the question.
You should ask yourself what is the user asking for and how can you use the tools to help you answer the question.
While using the tools keep in mind that the repeated use of the same tool may not be the most efficient way to complete the task.

It is not always necessary to use the tools provided to answer the question.

You have access to the following tools:
{tool_desc}

## Output Format
To answer the question, please use the following format.

```
Thought: I need to use a tool to help me answer the question.
Action: tool name (one of {tool_names}) if using a tool.
Action Input: the input to the tool, in a JSON format representing the kwargs (e.g. {{"input": "hello world", "num_beams": 5}})
```

Please ALWAYS start with a Thought.

Please use a valid JSON format for the Action Input. Do NOT do this {{'input': 'hello world', 'num_beams': 5}}.

If this format is used, the tools will will respond in the following format:

```
Observation: tool response
```

After you got the tools response you should reevaluate the question and the information you have.
If you have enough information to answer the question without using any more tools, you should respond with the format later discussed.
If not you should keep repeating the above format until you have enough information
to answer the question without using any more tools. At that point, you MUST respond
in the one of the following two formats:

```
Thought: I can answer without using any more tools.
Answer: [your answer here]
```

```
Thought: I cannot answer the question with the provided tools.
Answer: Sorry, I cannot answer your query.
```

## Additional Rules
- The answer MUST contain a sequence of bullet points that explain how you arrived at the answer. This can include aspects of the previous conversation history.
- You MUST obey the function signature of each tool. Do NOT pass in no arguments if the function expects arguments.
- You SHOULD NOT use the same tool more than once in a row. This is to encourage you to think about the problem from different angles.
- you MUST always reevaluate the question and the information you have before using a tool. If the tool is not necessary, do not use it. 

## Current Conversation
Below is the current conversation consisting of interleaving human and assistant messages.

"""


react_system_prompt = PromptTemplate(react_system_header_str)

from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.llms.langchain import LangChainLLM


def simple_chat_query(
        message: str = "",
)-> str:
    chat_engine = SimpleChatEngine.from_defaults(llm=get_llm(),system_prompt="""
                                                 You are beeing asked to help with simple chatting.
                                                 You are prompted by a supervising AI Agent you should annotate your messages by saying.
                                                 ```
                                                 As an AI I would recommend using: [[your answer]]
                                                 ```.
                                                 Be nice and helpful.""")
    response = chat_engine.chat(message=message)
    return response.__str__()

def file_query(
        message: str = "",
)-> str:
    query_engine = index.as_query_engine(),
    response = query_engine.query(message)
    return response.__str__()

from llama_index.llms.llama_cpp import LlamaCPP

def build_agent():
    index = get_chroma_storage()
    
    # hgf_llm = HuggingFaceLLM(
        # model_name="mradermacher/Mistral-7b-V0.3-ReAct-GGUF",
        # model_name="Maverick17/Mistral-7b-V0.3-ReAct",
    # )

    # llm = LangChainLLM(llm=hgf_llm)
    
    #llm = LlamaCPP(
    #    model_url="https://huggingface.co/mradermacher/Mistral-7b-V0.3-ReAct-GGUF/resolve/main/Mistral-7b-V0.3-ReAct.Q8_0.gguf",
    #    temperature=0.1,
    #    model_kwargs={"n_gpu_layers": 1}, 
    #    verbose=True,
    #)

    query_engine_tools = [
        FunctionTool.from_defaults(
            fn=simple_chat_query,
            name="Chat",
            description="A simple chat agent should ONLY be used for simple chatting. It provides its view on the given input. It is designed to be nice and helpful. The input should be the complete message you want to chat about. The response value should be used to answer the question.",
            return_direct=False,
        ),
        QueryEngineTool.from_defaults(
            query_engine=index.as_query_engine(),
            name="Ask",
            description="""
            a tool to help you with retrieving information about provided files.
            It is designed to provide accurate answers to questions based on the provided documents.
            When using this tool only use the response as your only source of information.
            it will provide you with the information you need to answer the question.
            """,
            return_direct=False,
        ),
    ]

    agent = OpenAIAgent.from_llm(
        llm=get_llm(),
        verbose=True,
        tools= query_engine_tools,
        max_iterations=10,
    )

    return agent

agent = build_agent()

# agent.update_prompts({"agent_worker:system_prompt": react_system_prompt})

# response = agent.chat(message='Hello, how are you?')
# response = agent.query('Please tell me which GPUs were utilized for the training of llama2. Please also provide the page and filename you found the information in. Thank you in advance!')
#print(response)

# a loop with input that is passed to the agent and the response is printed
#while True:
    #message = input("You: ")
response = agent.chat_repl()
#print(response)


# agent.query('Please tell me which GPUs were utilized for the training of llama2. Please also provide the page and filename you found the information in. Thank you in advance!')

#query_engine = index.as_query_engine()
#print(query_engine.query("Please tell me Which GPUs were utilized in the training of Llama2."))

# chat_engine = index.as_query_engine()

# response = query_engine.query("You are an expert examiner for AI at a university. Please write 10 exam questions. The questions should be multiple choice, true or false, missing word, or essay-based. Only ask questions related to the papers handed to you. It is important to me that the questions are accurate, thank you.")

# response = chat_engine.chat(chat_history=messages, message="Do you know what the successor of the GPU you just mentioned is?")

# Either way we can now query the index
# chat_engine = index.as_chat_engine()
# response = chat_engine.chat("Can you create a couple of question about llama2 just like a teacher might ask in an exam?", chat_history=messages)
# response = chat_engine.chat("Can you create a couple of question about llama2 just like a teacher might ask in an exam?")

# print(response)