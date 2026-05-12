from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class LLMUsage:
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0


@dataclass
class LLMResponse:
    text: str
    usage: LLMUsage


class LLMClient(Protocol):
    def complete(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> LLMResponse: ...
