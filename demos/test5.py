from api.utils.chains import get_llm
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI

from llama_index.core.settings import Settings

from llama_index.core.tools import QueryEngineTool, FunctionTool, BaseTool


Settings.llm = get_llm()

from llama_index.core.chat_engine import SimpleChatEngine
chat_engine = SimpleChatEngine.from_defaults()
# chat_engine.chat_repl()


query_engine_tools = [
    QueryEngineTool.from_defaults(
        query_engine=chat_engine,
        name="query",
        description="A simple chat agent should ONLY be used for simple chatting. It provides its view on the given input. It is designed to be nice and helpful. The input should be the complete message you want to chat about. The response value should be used to answer the question.",
    ),
]

agent = ReActAgent.from_tools(
    tools=[],
    llm=get_llm(),
    verbose=True,
)

# agent.query("Hey")





from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory  # Import memory

# chat = ChatOpenAI(temperature=0)
llm = get_llm()
# tools = load_tools(llm=llm)


from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.agents.conversational_chat.base import ConversationalChatAgent

from langchain.llms import ollama

# Add memory object
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

llm = ollama.Ollama(model="llama3", base_url="http://localhost:11434")

agent = initialize_agent(llm=llm, tools=[], agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, verbose=True, memory=memory)

#agent = ConversationalChatAgent.from_llm_and_tools(llm=llm,tools=[],)

agent.invoke("Hey")


