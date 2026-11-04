from __future__ import annotations

from abc import ABC, abstractmethod


class ModelGateway(ABC):
    """What a use case needs from a language model: text in, text out.

    The reply is untrusted. The use case that calls this must parse it and
    check guardrails (shape, topic, limits) before acting on it.
    """

    @abstractmethod
    def complete(self, prompt: str) -> str: ...
