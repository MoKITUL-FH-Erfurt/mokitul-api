from functools import lru_cache
from api.storage import get_chroma_index
from api.utils.chains import get_embedding_model, get_llm

from llama_index.core import ChatPromptTemplate

from llama_index.core import (
    Settings,
)

from llama_index.core.chat_engine.types import ChatMode


DEFAULT_CONTEXT_PROMPT_TEMPLATE = """
Im Folgenden siehst du ein freundliches Gespräch zwischen einem Benutzer und dir dem KI-Assistenten.
Du bist gesprächig und lieferst viele spezifische Details aus seinem Kontext.
Wenn du die Antwort auf eine Frage nicht weiß, sagst du wahrheitsgemäß, dass du es nicht weißt.

Hier sind die relevanten Dokumente für den Kontext:

{context_str}

Anweisung: Gebe auf die oben genannten Dokumente eine ausführliche Antwort auf die nachstehende Benutzerfrage.
Referenziere immer auf welches Dokument du dich beziehst ohne den retrieval_score. Nenne ausschließlich den Dokumentnamen!
Beantworten die Frage mit „weiß nicht“, wenn du nichts in dem Dokument enthalten ist.
"""

DEFAULT_CONDENSE_PROMPT_TEMPLATE = """
Geben die folgende Konversation zwischen einem Benutzer und einem KI-Assistenten und eine Folgefrage des Benutzers an,
formuliere die Folgefrage so um, dass sie eine eigenständige Frage ist. 
Es wird in eine Vektordatenbank eingespeist um relevante Dokumente zu finden.

Chat-Verlauf:
{chat_history}
Folge-Eingabe: {question}
Eigenständige Frage:"""

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
    chat_engine = index.as_chat_engine(
        llm=get_llm(),
        chat_mode=ChatMode.CONDENSE_PLUS_CONTEXT,
        system_prompt=system_prompt,
        context_prompt=context_prompt,
    )

    return chat_engine


def get_chat_engine_memoized(path: str):
    print("get_chat_engine_memoized")

    Settings.llm = get_llm()
    Settings.embed_model = get_embedding_model()

    index = get_chroma_storage_for_single_file(path)

    # seems to be MUCH BETTER WITHOUT the llm explicitly passed
    chat_engine = index.as_chat_engine(
        llm=get_llm(), chat_mode=ChatMode.CONDENSE_PLUS_CONTEXT
    )

    return chat_engine
