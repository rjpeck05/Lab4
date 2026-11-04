from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from .model_gateway import ModelGateway


class Intent(Enum):
    BOOK = "book"
    CANCEL = "cancel"
    AVAILABLE = "available"
    OTHER = "other"


PROMPT = (
    "Classify this message from a student of a study-room booking system. "
    "Answer with exactly one word from: book, cancel, available, other.\n"
    "Message: {text}"
)


@dataclass(frozen=True)
class ClassifyRequestRequest:
    text: str


@dataclass(frozen=True)
class ClassifyRequestResponse:
    intent: Intent


class ClassifyRequestOutputBoundary(ABC):
    @abstractmethod
    def present_intent(self, response: ClassifyRequestResponse) -> None: ...

    @abstractmethod
    def present_error(self, message: str) -> None: ...


class ClassifyRequest:
    """The one AI decision point: which command does a free-text message mean?

    The model's reply is untrusted. Anything that is not exactly one known
    label (malformed, truncated, off-topic) is rejected, never guessed at.
    """

    def __init__(self, model: ModelGateway, output: ClassifyRequestOutputBoundary) -> None:
        self._model = model
        self._output = output

    def execute(self, request: ClassifyRequestRequest) -> None:
        if not request.text.strip():
            self._output.present_error("Please type a message to classify.")
            return
        reply = self._model.complete(PROMPT.format(text=request.text)).strip().lower()
        try:
            intent = Intent(reply)
        except ValueError:
            self._output.present_error("The assistant gave an answer I could not use.")
            return
        self._output.present_intent(ClassifyRequestResponse(intent))
