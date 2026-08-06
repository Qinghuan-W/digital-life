from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.llm.openai_provider import OpenAIProvider
from app.llm.provider import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    return OpenAIProvider()


CurrentLLMProvider = Annotated[LLMProvider, Depends(get_llm_provider)]
