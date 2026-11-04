import json
import socket
import unittest

from study_room_booking.interface_adapters.gateways.fake_model_adapter import (
    FakeModelAdapter,
    Scenario,
)
from study_room_booking.use_cases.model_gateway import ModelGateway
from tests import NetworkAccessError


class FakeModelAdapterTest(unittest.TestCase):
    def test_is_a_model_gateway(self):
        self.assertIsInstance(FakeModelAdapter(), ModelGateway)

    def test_good_scenario_returns_parseable_booking_intent(self):
        data = json.loads(FakeModelAdapter(Scenario.GOOD).complete("book me a room"))
        self.assertEqual(set(data), {"room_id", "start", "end", "group_size"})

    def test_malformed_scenario_is_not_valid_json(self):
        with self.assertRaises(json.JSONDecodeError):
            json.loads(FakeModelAdapter(Scenario.MALFORMED).complete("book me a room"))

    def test_off_topic_scenario_is_text_with_no_booking_fields(self):
        reply = FakeModelAdapter(Scenario.OFF_TOPIC).complete("book me a room")
        with self.assertRaises(json.JSONDecodeError):
            json.loads(reply)
        self.assertNotIn("room_id", reply)

    def test_scenario_can_be_switched_and_prompts_are_recorded(self):
        fake = FakeModelAdapter()
        good = fake.complete("one")
        fake.use(Scenario.OFF_TOPIC)
        self.assertNotEqual(good, fake.complete("two"))
        self.assertEqual(fake.prompts, ["one", "two"])

    def test_custom_scripts_and_missing_scenario(self):
        fake = FakeModelAdapter(Scenario.GOOD, scripts={Scenario.GOOD: "ok"})
        self.assertEqual(fake.complete("x"), "ok")
        fake.use(Scenario.MALFORMED)
        with self.assertRaises(LookupError):
            fake.complete("x")


class SuiteIsOfflineTest(unittest.TestCase):
    def test_connections_and_dns_are_refused(self):
        with self.assertRaises(NetworkAccessError):
            socket.create_connection(("example.com", 80))
        with self.assertRaises(NetworkAccessError):
            socket.getaddrinfo("example.com", 80)
        with socket.socket() as sock, self.assertRaises(NetworkAccessError):
            sock.connect(("127.0.0.1", 80))


if __name__ == "__main__":
    unittest.main()
