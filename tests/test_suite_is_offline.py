"""Enforces the suite rule: tests use fakes, never real drivers or network libraries."""
import ast
import unittest
from datetime import datetime
from pathlib import Path

from study_room_booking.interface_adapters.gateways.fake_clock import FakeClock
from study_room_booking.use_cases.clock import Clock

TESTS = Path(__file__).resolve().parent
FORBIDDEN_PREFIXES = (
    "study_room_booking.frameworks_drivers",  # real drivers (SystemClock, shell, main)
    "urllib.request", "http.client", "requests", "httpx", "aiohttp", "ftplib", "smtplib",
)


def imports(path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            yield node.module


class SuiteIsOfflineTest(unittest.TestCase):
    def test_no_test_imports_a_real_driver_or_network_library(self):
        problems = []
        for path in TESTS.glob("test_*.py"):
            if path.name == Path(__file__).name:
                continue
            for module in imports(path):
                if module.startswith(FORBIDDEN_PREFIXES):
                    problems.append(f"{path.name} imports {module}")
        self.assertEqual(problems, [])

    def test_fake_clock_only_moves_when_told(self):
        clock = FakeClock(datetime(2026, 11, 1, 9, 0))
        self.assertIsInstance(clock, Clock)
        self.assertEqual(clock.now(), datetime(2026, 11, 1, 9, 0))
        clock.set(datetime(2026, 11, 2, 9, 0))
        self.assertEqual(clock.now(), datetime(2026, 11, 2, 9, 0))


if __name__ == "__main__":
    unittest.main()
