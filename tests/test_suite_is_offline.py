"""Enforces the suite rule: tests use fakes, never real drivers or the network."""
import ast
import socket
import unittest
from datetime import datetime
from pathlib import Path

from study_room_booking.interface_adapters.gateways.fake_clock import FakeClock
from study_room_booking.use_cases.clock import Clock
from tests import NetworkAccessError

TESTS = Path(__file__).resolve().parent
FORBIDDEN = (
    "study_room_booking.frameworks_drivers",  # real drivers (SystemClock, shell, main)
    "urllib.request", "urllib3", "http.client", "requests", "httpx", "aiohttp",
    "ftplib", "smtplib", "telnetlib", "xmlrpc.client", "websockets",
    "ssl", "asyncio", "subprocess", "ctypes", "webbrowser",
    "_socket",  # the raw C socket type cannot be patched by tests/__init__.py
)


def forbidden_imports(source: str):
    """Every forbidden module a piece of source imports, whatever the spelling."""
    found = []
    for node in ast.walk(ast.parse(source)):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            # `from urllib import request` really imports urllib.request
            names = [node.module] + [f"{node.module}.{alias.name}" for alias in node.names]
        found += [n for n in names if any(n == f or n.startswith(f + ".") for f in FORBIDDEN)]
    return found


class ImportCheckTest(unittest.TestCase):
    def test_no_test_imports_a_real_driver_or_network_library(self):
        problems = []
        for path in TESTS.glob("test_*.py"):
            if path.name == Path(__file__).name:
                continue
            problems += [f"{path.name} imports {m}" for m in forbidden_imports(path.read_text())]
        self.assertEqual(problems, [])

    def test_every_spelling_of_a_forbidden_import_is_caught(self):
        for source in (
            "import urllib.request",
            "from urllib import request",
            "from http import client",
            "from study_room_booking import frameworks_drivers",
            "from study_room_booking.frameworks_drivers.system_clock import SystemClock",
            "import subprocess",
            "import _socket",
        ):
            with self.subTest(source=source):
                self.assertTrue(forbidden_imports(source))

    def test_harmless_imports_are_not_flagged(self):
        self.assertEqual(forbidden_imports("import json\nfrom urllib import parse"), [])


class NetworkGuardTest(unittest.TestCase):
    def test_every_way_out_of_the_process_is_refused(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
            attempts = {
                "tcp connect": lambda: socket.create_connection(("127.0.0.1", 9)),
                "udp sendto": lambda: udp.sendto(b"x", ("127.0.0.1", 9)),
                "gethostbyname": lambda: socket.gethostbyname("localhost"),
                "getaddrinfo": lambda: socket.getaddrinfo("localhost", 80),
            }
            for label, attempt in attempts.items():
                with self.subTest(label), self.assertRaises(NetworkAccessError):
                    attempt()


class FakeClockTest(unittest.TestCase):
    def test_fake_clock_only_moves_when_told(self):
        clock = FakeClock(datetime(2026, 11, 1, 9, 0))
        self.assertIsInstance(clock, Clock)
        self.assertEqual(clock.now(), datetime(2026, 11, 1, 9, 0))
        clock.set(datetime(2026, 11, 2, 9, 0))
        self.assertEqual(clock.now(), datetime(2026, 11, 2, 9, 0))


if __name__ == "__main__":
    unittest.main()
