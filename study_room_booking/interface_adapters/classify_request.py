from __future__ import annotations

from study_room_booking.use_cases.classify_request import (
    ClassifyRequest,
    ClassifyRequestOutputBoundary,
    ClassifyRequestRequest,
    ClassifyRequestResponse,
)

from .view_model import ViewModel


class ClassifyRequestPresenter(ClassifyRequestOutputBoundary):
    def __init__(self) -> None:
        self.view_model = ViewModel(True, ())

    def present_intent(self, response: ClassifyRequestResponse) -> None:
        self.view_model = ViewModel(True, (f"That looks like a '{response.intent.value}' request.",))

    def present_error(self, message: str) -> None:
        self.view_model = ViewModel(False, (f"Error: {message}",))

    def present_handoff(self, reason: str) -> None:
        self.view_model = ViewModel(
            False,
            (
                "I couldn't work that out. Please ask library staff at the front desk;"
                " they will help you.",
            ),
        )


class ClassifyRequestController:
    def __init__(self, use_case: ClassifyRequest, presenter: ClassifyRequestPresenter) -> None:
        self._use_case = use_case
        self._presenter = presenter

    def classify(self, text: str) -> ViewModel:
        self._use_case.execute(ClassifyRequestRequest(text))
        return self._presenter.view_model
