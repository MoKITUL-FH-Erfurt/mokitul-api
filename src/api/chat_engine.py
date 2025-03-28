from functools import lru_cache
from api.storage import get_chroma_index
from api.utils.chains import get_embedding_model, get_llm

from llama_index.core import ChatPromptTemplate

from llama_index.core import (
    Settings,
)

from llama_index.core.chat_engine.types import ChatMode

qa_prompt_str = (
    "<s>[INST] <<SYS>>"
    "Use the following context to answer the user's question. If you don't know the answer,"
    "just say that you don't know, don't try to make up an answer."
    "<</SYS>>"
    "<s>[INST] Context: {context_str} Question: {query_str} Only return the helpful"
    " answer below and nothing else. Helpful answer:[/INST]"
)

refine_prompt_str = (
    "We have the opportunity to refine the original answer "
    "(only if needed) with some more context below.\n"
    "------------\n"
    "{context_msg}\n"
    "------------\n"
    "Given the new context, refine the original answer to better "
    "answer the question: {query_str}. "
    "If the context isn't useful, output the original answer again.\n"
    "Original Answer: {existing_answer}"
)

chat_text_qa_msgs = [
    (
        "system",
        "Always answer the question, even if the context isn't helpful.",
    ),
    ("user", qa_prompt_str),
]
text_qa_template = ChatPromptTemplate.from_messages(chat_text_qa_msgs)

chat_refine_msgs = [
    (
        "system",
        "Always answer the question, even if the context isn't helpful.",
    ),
    ("user", refine_prompt_str),
]
refine_template = ChatPromptTemplate.from_messages(chat_refine_msgs)

def get_query_engine(files: list[str] | None = None):
    Settings.llm = get_llm()
    Settings.embed_model = get_embedding_model()

    index = get_chroma_storage(files)

    query_engine = index.as_query_engine(
        text_qa_template=text_qa_template,
        refine_template=refine_template,
    )

    return query_engine

def get_query_engine_memoized(path: str):
    print("get_query_engine_memoized")

    Settings.llm = get_llm()
    Settings.embed_model = get_embedding_model()

    index = get_chroma_storage_for_single_file(path)

    query_engine = index.as_query_engine(
        text_qa_template=text_qa_template,
        refine_template=refine_template,
    )

    return query_engine

# util functions to interact with llama-index
def get_chat_engine(system_prompt: str | None = None, files: list[str] | None = None):
    Settings.llm = get_llm()
    Settings.embed_model = get_embedding_model()

    index = get_chroma_storage(files)

    context_prompt = """
    Ich bin ein freundlicher und hilfsbereiter KI-Assistent, der in die Moodle-Plattform integriert ist, um Studenten bei ihren Fragen und Anliegen zu unterstützen. Mein Ziel ist es, ein angenehmes und produktives Lernerlebnis zu schaffen, indem ich den Studenten mit Rat und Tat zur Seite stehe.
Ich verfüge über umfangreiches Wissen zu den Themen und Kursinhalten in Moodle und kann den Studenten bei einer Vielzahl von Fragen weiterhelfen, z.B.:
Erklärung von Kurskonzepten und -materialien
Tipps zum effektiven Lernen und Zeitmanagement
Motivation und Ermutigung bei Herausforderungen
Dabei gehe ich stets freundlich, geduldig und verständnisvoll auf die individuellen Bedürfnisse der Studenten ein. Meine Antworten sind klar, verständlich und auf den Kontext abgestimmt. Ich bin bestrebt, eine positive und konstruktive Lernatmosphäre zu schaffen.

Ich kann bei Antworten welche in LaTeX Format angegeben werden können folgendes Format verwenden. $$[Inhalt]$$
Ich muss für meine Antworten immer den relevanten Kontext des gesamten Chats verwenden.
Für das beantworten der Anfragen muss ich folgende Inhalte berücksichtigen. Ich muss immer die Inhalte die ich verwende in diesem Format: (Quelle: [Seitenanzahl], [Dokumentpfad]) angeben.
{context_str}

"""

    # seems to be MUCH BETTER WITHOUT the llm explicitly passed
    chat_engine = index.as_chat_engine(llm=get_llm(), chat_mode=ChatMode.CONDENSE_PLUS_CONTEXT, system_prompt=system_prompt, context_prompt=context_prompt)

    return chat_engine

def get_chat_engine_memoized(path: str):
    print("get_chat_engine_memoized")

    Settings.llm = get_llm()
    Settings.embed_model = get_embedding_model()

    index = get_chroma_storage_for_single_file(path)

    # seems to be MUCH BETTER WITHOUT the llm explicitly passed
    chat_engine = index.as_chat_engine(
        llm=get_llm(),
        chat_mode=ChatMode.CONDENSE_PLUS_CONTEXT
    )

    return chat_engine
