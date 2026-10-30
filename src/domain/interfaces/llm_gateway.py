from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMGateway(Protocol):
    """Contract for LLM text generation."""

    def generate_response(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate response given a user prompt and optional system instructions."""
