from typing import Any, cast

import anthropic
from anthropic.types import MessageParam

from warlock.llm import LLMResponse, LLMUsage


class AnthropicClient:
    def __init__(self):
        self._client = anthropic.Anthropic()

    def complete(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> LLMResponse:
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=cast(list[MessageParam], messages),
        )

        text = next(block.text for block in response.content if block.type == "text")
        usage = LLMUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_read_tokens=getattr(response.usage, "cache_read_input_tokens", 0),
        )

        return LLMResponse(text=text, usage=usage)
