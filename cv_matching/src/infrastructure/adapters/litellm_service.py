import logging
from typing import Any, TypeVar, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from cv_matching.src.domain.ports.llm_service import ILLMService

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LiteLLMService(ILLMService[T]):
    def __init__(self, settings):
        self.settings = settings

    def _get_client(self, response_model: type[T], **kwargs) -> Any:
        temperature = kwargs.get("temperature", 0)
        extra_kwargs = {}
        if self.settings.reasoning_effort:
            extra_kwargs["reasoning_effort"] = self.settings.reasoning_effort
            temperature = None
        client = ChatOpenAI(
            model=self.settings.model,
            base_url=self.settings.url,
            api_key=self.settings.api_key,
            temperature=temperature,
            timeout=self.settings.timeout,
            max_retries=self.settings.max_retries,
            **extra_kwargs,
        )
        return client.with_structured_output(response_model)

    async def analyze_text(
        self, system_prompt: str, user_prompt: str, response_model: type[T], **kwargs
    ) -> T:
        llm = self._get_client(response_model, **kwargs)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        logger.info(
            "[analyze_text] Sending request to LLM (schema=%s, system_prompt_len=%d, user_prompt_len=%d)",
            response_model.__name__,
            len(system_prompt),
            len(user_prompt),
        )
        return cast(T, await llm.ainvoke(messages))
