from datetime import datetime

from .view_model import ViewModel

INPUT_FORMAT = "%Y-%m-%dT%H:%M"  # e.g. 2026-11-02T14:00

UNREADABLE_INPUT = ViewModel(
    False,
    ("Error: Could not read the input. Use dates like 2026-11-02T14:00 and a whole-number group size.",),
)


def parse_date_time(text: str) -> datetime:
    return datetime.strptime(text, INPUT_FORMAT)
