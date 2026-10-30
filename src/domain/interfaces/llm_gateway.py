from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMGateway(Protocol):
    """Contract for LLM text generation."""

    def generate_response(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate response given a user prompt and optional system instructions."""


@runtime_checkable
class AsyncLLMGateway(Protocol):
    """Contract for asynchronous LLM text generation."""

    async def agenerate_response(
        self, prompt: str, system_prompt: str | None = None
    ) -> str:
        """
        Generate response asynchronously given prompt and optional system instructions.
        """
