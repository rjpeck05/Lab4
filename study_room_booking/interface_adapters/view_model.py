from dataclasses import dataclass


@dataclass(frozen=True)
class ViewModel:
    """Plain, display-ready data. Any view (shell, web page...) just renders it."""

    ok: bool
    lines: tuple[str, ...]
