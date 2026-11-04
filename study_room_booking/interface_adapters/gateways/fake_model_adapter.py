from __future__ import annotations

from enum import Enum
from typing import Mapping, Optional

from study_room_booking.use_cases.model_gateway import ModelGateway


class Scenario(Enum):
    GOOD = "good"
    MALFORMED = "malformed"
    OFF_TOPIC = "off_topic"  # guardrail-tripping: well-formed text, wrong subject


DEFAULT_SCRIPTS: Mapping[Scenario, str] = {
    Scenario.GOOD: (
        '{"room_id": "R1", "start": "2026-11-02T10:00", '
        '"end": "2026-11-02T12:00", "group_size": 3}'
    ),
    # Truncated mid-object, the way a cut-off completion looks.
    Scenario.MALFORMED: '{"room_id": "R1", "start": "2026-11-02T10:00", "end": ',
    Scenario.OFF_TOPIC: (
        "Sure! Here is a short poem about the ocean: the waves roll in, "
        "the gulls cry out, the tide forgets the shore."
    ),
}


class FakeModelAdapter(ModelGateway):
    """Scripted, offline stand-in for a real model. Never opens a connection."""

    def __init__(
        self,
        scenario: Scenario = Scenario.GOOD,
        scripts: Optional[Mapping[Scenario, str]] = None,
    ) -> None:
        self._scripts = dict(DEFAULT_SCRIPTS if scripts is None else scripts)
        self._scenario = scenario
        self.prompts: list[str] = []  # every prompt received, for assertions

    def use(self, scenario: Scenario) -> None:
        self._scenario = scenario

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        try:
            return self._scripts[self._scenario]
        except KeyError:
            raise LookupError(f"No scripted response for scenario {self._scenario}.") from None
