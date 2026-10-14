import datetime
import ipaddress
import json
import unittest
from dataclasses import dataclass
from typing import Any, Optional
from collections.abc import Iterable
from unittest import mock

from requests import Response

from podman import api


class ParseUtilsTestCase(unittest.TestCase):
    def test_parse_repository(self) -> None:
        @dataclass
        class TestCase:
            name: str
            input: Any
            expected: tuple[str, Optional[str]]

        cases = [
            TestCase(name="empty str", input="", expected=("", None)),
            TestCase(
                name="name",
                input="quay.io/libpod/testimage",
                expected=("quay.io/libpod/testimage", None),
            ),
            TestCase(
                name="@digest",
                input="quay.io/libpod/testimage@sha256:71f1b47263fc",
                expected=("quay.io/libpod/testimage@sha256", "71f1b47263fc"),
            ),
            TestCase(
                name=":tag",
                input="quay.io/libpod/testimage:latest",
                expected=("quay.io/libpod/testimage", "latest"),
            ),
            TestCase(
                name=":tag@digest",
                input="quay.io/libpod/testimage:latest@sha256:71f1b47263fc",
                expected=("quay.io/libpod/testimage:latest@sha256", "71f1b47263fc"),
            ),
            TestCase(
                name=":port",
                input="quay.io:5000/libpod/testimage",
                expected=("quay.io:5000/libpod/testimage", None),
            ),
            TestCase(
                name=":port@digest",
                input="quay.io:5000/libpod/testimage@sha256:71f1b47263fc",
                expected=("quay.io:5000/libpod/testimage@sha256", "71f1b47263fc"),
            ),
            TestCase(
                name=":port:tag",
                input="quay.io:5000/libpod/testimage:latest",
                expected=("quay.io:5000/libpod/testimage", "latest"),
            ),
            TestCase(
                name=":port:tag:digest",
                input="quay.io:5000/libpod/testimage:latest@sha256:71f1b47263fc",
                expected=("quay.io:5000/libpod/testimage:latest@sha256", "71f1b47263fc"),
            ),
        ]

        for case in cases:
            actual = api.parse_repository(case.input)
            self.assertEqual(
                case.expected,
                actual,
                f"failed test {case.name} expected {case.expected}, actual {actual}",
            )

    def test_decode_header(self) -> None:
        actual = api.decode_header("eyJIZWFkZXIiOiJ1bml0dGVzdCJ9")
        self.assertDictEqual(actual, {"Header": "unittest"})

        self.assertDictEqual(api.decode_header(None), {})

    def test_prepare_timestamp(self) -> None:
        time = datetime.datetime(2022, 1, 24, 12, 0, 0)
        self.assertEqual(api.prepare_timestamp(time), 1643025600)
        self.assertEqual(api.prepare_timestamp(2), 2)

        self.assertEqual(api.prepare_timestamp(None), None)
        with self.assertRaises(ValueError):
            api.prepare_timestamp("bad input")  # type: ignore

    def test_prepare_cidr(self) -> None:
        net = ipaddress.IPv4Network("127.0.0.0/24")
        self.assertEqual(api.prepare_cidr(net), ("127.0.0.0", "////AA=="))

    def test_stream_helper(self) -> None:
        streamed_results = [b'{"test":"val1"}', b'{"test":"val2"}']
        mock_response = mock.Mock(spec=Response)
        mock_response.iter_lines.return_value = iter(streamed_results)

        streamable = api.stream_helper(mock_response)

        self.assertIsInstance(streamable, Iterable)
        for expected, actual in zip(streamed_results, streamable):
            self.assertIsInstance(actual, bytes)
            self.assertEqual(expected, actual)

    def test_stream_helper_with_decode(self) -> None:
        streamed_results = [b'{"test":"val1"}', b'{"test":"val2"}']
        mock_response = mock.Mock(spec=Response)
        mock_response.iter_lines.return_value = iter(streamed_results)

        streamable = api.stream_helper(mock_response, decode_to_json=True)

        self.assertIsInstance(streamable, Iterable)
        for expected, actual in zip(streamed_results, streamable):
            self.assertIsInstance(actual, dict)
            self.assertDictEqual(json.loads(expected), actual)  # type: ignore[arg-type]


class PrepareDurationNsTestCase(unittest.TestCase):
    """Test prepare_duration_ns utility."""

    def test_none_returns_none(self):
        self.assertIsNone(api.prepare_duration_ns(None))

    def test_int_passthrough(self):
        self.assertEqual(api.prepare_duration_ns(0), 0)
        self.assertEqual(api.prepare_duration_ns(1), 1)
        self.assertEqual(api.prepare_duration_ns(30_000_000_000), 30_000_000_000)

    def test_seconds(self):
        self.assertEqual(api.prepare_duration_ns("1s"), 1_000_000_000)
        self.assertEqual(api.prepare_duration_ns("30s"), 30_000_000_000)
        self.assertEqual(api.prepare_duration_ns("120s"), 120_000_000_000)

    def test_minutes(self):
        self.assertEqual(api.prepare_duration_ns("1m"), 60_000_000_000)
        self.assertEqual(api.prepare_duration_ns("5m"), 300_000_000_000)

    def test_hours(self):
        self.assertEqual(api.prepare_duration_ns("1h"), 3_600_000_000_000)
        self.assertEqual(api.prepare_duration_ns("2h"), 7_200_000_000_000)

    def test_milliseconds(self):
        self.assertEqual(api.prepare_duration_ns("1ms"), 1_000_000)
        self.assertEqual(api.prepare_duration_ns("500ms"), 500_000_000)

    def test_microseconds_us(self):
        self.assertEqual(api.prepare_duration_ns("1us"), 1_000)
        self.assertEqual(api.prepare_duration_ns("100us"), 100_000)

    def test_microseconds_mu(self):
        self.assertEqual(api.prepare_duration_ns("1µs"), 1_000)
        self.assertEqual(api.prepare_duration_ns("100µs"), 100_000)

    def test_nanoseconds(self):
        self.assertEqual(api.prepare_duration_ns("1ns"), 1)
        self.assertEqual(api.prepare_duration_ns("999ns"), 999)

    def test_compound_duration(self):
        self.assertEqual(api.prepare_duration_ns("1h30m"), 5_400_000_000_000)
        self.assertEqual(api.prepare_duration_ns("1m30s"), 90_000_000_000)
        self.assertEqual(api.prepare_duration_ns("2h30m15s"), 9_015_000_000_000)
        self.assertEqual(api.prepare_duration_ns("1s500ms"), 1_500_000_000)

    def test_bare_zero(self):
        self.assertEqual(api.prepare_duration_ns("0"), 0)

    def test_fractional_raises(self):
        with self.assertRaises(ValueError):
            api.prepare_duration_ns("1.5s")
        with self.assertRaises(ValueError):
            api.prepare_duration_ns("0.5s")

    def test_whitespace_stripped(self):
        self.assertEqual(api.prepare_duration_ns("  30s  "), 30_000_000_000)
        self.assertEqual(api.prepare_duration_ns(" 1m "), 60_000_000_000)

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            api.prepare_duration_ns("invalid")

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            api.prepare_duration_ns("")

    def test_whitespace_only_raises(self):
        with self.assertRaises(ValueError):
            api.prepare_duration_ns("   ")

    def test_number_without_unit_raises(self):
        with self.assertRaises(ValueError):
            api.prepare_duration_ns("30")

    def test_unit_without_number_raises(self):
        with self.assertRaises(ValueError):
            api.prepare_duration_ns("s")

    def test_wrong_type_raises(self):
        with self.assertRaises(TypeError):
            api.prepare_duration_ns(3.14)  # type: ignore
        with self.assertRaises(TypeError):
            api.prepare_duration_ns([30])  # type: ignore


class HealthOnFailureActionTestCase(unittest.TestCase):
    """Test HEALTH_ON_FAILURE_ACTION mapping."""

    def test_none_maps_to_zero(self):
        self.assertEqual(api.HEALTH_ON_FAILURE_ACTION["none"], 0)

    def test_kill_maps_to_two(self):
        self.assertEqual(api.HEALTH_ON_FAILURE_ACTION["kill"], 2)

    def test_restart_maps_to_three(self):
        self.assertEqual(api.HEALTH_ON_FAILURE_ACTION["restart"], 3)

    def test_stop_maps_to_four(self):
        self.assertEqual(api.HEALTH_ON_FAILURE_ACTION["stop"], 4)

    def test_invalid_value_one_not_exposed(self):
        self.assertNotIn(1, api.HEALTH_ON_FAILURE_ACTION.values())

    def test_all_values_are_ints(self):
        for key, value in api.HEALTH_ON_FAILURE_ACTION.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, int)


if __name__ == '__main__':
    unittest.main()
