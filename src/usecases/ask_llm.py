from core import Result
from core.request_timer import RequestTimer
from core.singelton import SingletonMeta
from usecases.llm import RAGLLM, LLMResponse, Message


class AskLLMUsecase(metaclass=SingletonMeta):
    """
    Interface to ask the LLM for information.
    Used in UseCases to ask the LLM for information.
    """

    _llm: RAGLLM

    def __init__(self, llm: RAGLLM) -> None:
        self._llm = llm

    @classmethod
    def create(cls, llm: RAGLLM):
        if cls not in SingletonMeta._instances:
            return cls(llm)
        else:
            raise RuntimeError("Singleton instance already created.")

    @classmethod
    def Instance(cls) -> "AskLLMUsecase":
        if cls not in SingletonMeta._instances:
            raise RuntimeError(
                "Singleton instance has not been created yet. Call `create` first."
            )
        return SingletonMeta._instances[cls]

    def run(
        self,
        messages: list[Message],
        model: str,
        filters: dict[str, list[str]] = {},
    ) -> Result[LLMResponse]:
        timer = RequestTimer()
        timer.start("Ask LLM")
        result = self._llm.ask(messages=messages, filters=filters, model=model)
        timer.end()
        return result
