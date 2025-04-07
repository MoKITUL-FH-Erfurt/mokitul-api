import logging
from typing import Dict, List, cast
from api.model import Message
from llama_index.core import VectorStoreIndex
from llama_index.core.bridge.pydantic import BaseModel
from llama_index.core.chat_engine.types import AgentChatResponse, ChatMode
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    FilterCondition,
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from core import Result
import torch
from usecases.llm import RAGLLM, LLMResponse
from usecases.llm.init_index import LLamaIndexHolder, LlamaIndexRAGConfig
from usecases.model.dto import Node
from llama_index.llms.ollama import Ollama

logger = logging.getLogger(__name__)


class LLamaIndexRAGLLM(RAGLLM):
    """
    Allows to ask questions to the LLM model using the LlamaIndex
    Uses a vector store to retrieve the documents
    will use the colbert reranker to rerank the documents
    """

    def __init__(
        self,
        config: LlamaIndexRAGConfig,
    ):
        self._config = config
        self._index_holder = LLamaIndexHolder.Instance()

    def ask(
        self, messages: List[Message], model: str, filters: Dict[str, List[str]] = {}
    ) -> Result[LLMResponse]:
        index_holder = LLamaIndexHolder.Instance()

        metadata_filters = MetadataFilters(filters=[])
        for key in filters.keys():
            for value in filters[key]:
                metadata_filters.filters.append(
                    MetadataFilter(key=key, value=value, operator=FilterOperator.EQ)
                )

        llm = Ollama(
            model=self._config.llm_model,
            base_url=self._config.ollama_url,
            request_timeout=self._config.timeout,
            context_window=self._config.context_window,
        )
        metadata_filters.condition = FilterCondition.OR
        index = self._index_holder.get_index()
        self._chat_engine = index.as_chat_engine(
            llm=llm,
            chat_mode=ChatMode.CONDENSE_PLUS_CONTEXT,
            context_prompt=DEFAULT_CONTEXT_PROMPT_TEMPLATE,
            condense_prompt=DEFAULT_CONDENSE_PROMPT_TEMPLATE,
            similarity_top_k=self._config.top_n_count_dens,
            sparse_top_k=self._config.top_n_count_dens,
            node_postprocessors=[index_holder.get_reranker()],
            vector_store_query_mode="hybrid",
            filters=metadata_filters,
            verbose=True,
        )
        last_message = messages[len(messages) - 1]
        messages.remove(last_message)
        chat_history = self.__convert_to_chat_history(messages)

        try:
            response = cast(
                AgentChatResponse,
                self._chat_engine.chat(last_message.content, chat_history=chat_history),
            )

            nodes = [
                Node(
                    id=node.id_,
                    content=node.text,
                    metadata=node.metadata,
                    relations=[],
                    similarity_score=node.get_score(raise_error=False),
                )
                for node in response.source_nodes
            ]
            for node in nodes:
                logging.getLogger(__name__).debug(f"use Node:{node}")

            try:
                torch.cuda.empty_cache()
            except Exception as e:
                logger.error(f"Failed to release cuda cache {e}")
            return Result.Ok(LLMResponse(response=response.response, nodes=nodes))
        except Exception as e:
            return Result.Err(Exception(f"failed to retrive answer from llm {e}"))

    def __convert_to_chat_history(self, messages: list[Message]) -> List[ChatMessage]:
        return [
            ChatMessage(role=MessageRole(message.role), content=message.content)
            for message in messages
        ]


DEFAULT_CONTEXT_PROMPT_TEMPLATE = """
Im Folgenden siehst du ein freundliches Gespräch zwischen einem Benutzer und dir dem KI-Assistenten.
Du bist gesprächig und lieferst viele spezifische Details aus seinem Kontext.
Wenn du die Antwort auf eine Frage nicht weiß, sagst du wahrheitsgemäß, dass du es nicht weißt.

Hier sind die relevanten Dokumente für den Kontext:

{context_str}

Anweisung: Gebe auf Grundlage der oben genannten Dokumente eine ausführliche Antwort auf die nachstehende Benutzerfrage.
Referenziere immer auf welches Dokument du dich beziehst ohne den retrieval_score. Nenne ausschließlich den Dokumentnamen!
Beantworten die Frage mit „weiß nicht“, wenn du nichts in dem Dokument enthalten ist.
"""

DEFAULT_CONDENSE_PROMPT_TEMPLATE = """
Geben die folgende Konversation zwischen einem Benutzer und einem KI-Assistenten und eine Folgefrage des Benutzers an,
formuliere die Folgefrage so um, dass sie eine eigenständige Frage ist. Es wird in eine Vektordatenbank eingespeist um relevante Dokumente zu finden.

Chat-Verlauf:
{chat_history}
Folge-Eingabe: {question}
Eigenständige Frage:"""
