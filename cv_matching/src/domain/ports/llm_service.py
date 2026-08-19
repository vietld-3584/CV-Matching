from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ILLMService(ABC, Generic[T]):
    @abstractmethod
    async def analyze_text(
        self, system_prompt: str, user_prompt: str, response_model: type[T], **kwargs
    ) -> T:
        pass
