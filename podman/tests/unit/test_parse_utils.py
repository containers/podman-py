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
    def test_parse_repository(self):
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
                input="quay.io/libpod/testimage@71f1b47263fc",
                expected=("quay.io/libpod/testimage", "71f1b47263fc"),
            ),
            TestCase(
                name=":tag",
                input="quay.io/libpod/testimage:latest",
                expected=("quay.io/libpod/testimage", "latest"),
            ),
        ]

        for case in cases:
            actual = api.parse_repository(case.input)
            self.assertEqual(
                case.expected,
                actual,
                f"failed test {case.name} expected {case.expected}, actual {actual}",
            )

    def test_decode_header(self):
        actual = api.decode_header("eyJIZWFkZXIiOiJ1bml0dGVzdCJ9")
        self.assertDictEqual(actual, {"Header": "unittest"})

        self.assertDictEqual(api.decode_header(None), {})

    def test_prepare_timestamp(self):
        time = datetime.datetime(2022, 1, 24, 12, 0, 0)
        self.assertEqual(api.prepare_timestamp(time), 1643025600)
        self.assertEqual(api.prepare_timestamp(2), 2)

        self.assertEqual(api.prepare_timestamp(None), None)
        with self.assertRaises(ValueError):
            api.prepare_timestamp("bad input")  # type: ignore

    def test_prepare_cidr(self):
        net = ipaddress.IPv4Network("127.0.0.0/24")
        self.assertEqual(api.prepare_cidr(net), ("127.0.0.0", "////AA=="))

    def test_stream_helper(self):
        streamed_results = [b'{"test":"val1"}', b'{"test":"val2"}']
        mock_response = mock.Mock(spec=Response)
        mock_response.iter_lines.return_value = iter(streamed_results)

        streamable = api.stream_helper(mock_response)

        self.assertIsInstance(streamable, Iterable)
        for expected, actual in zip(streamed_results, streamable):
            self.assertIsInstance(actual, bytes)
            self.assertEqual(expected, actual)

    def test_stream_helper_with_decode(self):
        streamed_results = [b'{"test":"val1"}', b'{"test":"val2"}']
        mock_response = mock.Mock(spec=Response)
        mock_response.iter_lines.return_value = iter(streamed_results)

        streamable = api.stream_helper(mock_response, decode_to_json=True)

        self.assertIsInstance(streamable, Iterable)
        for expected, actual in zip(streamed_results, streamable):
            self.assertIsInstance(actual, dict)
            self.assertDictEqual(json.loads(expected), actual)


if __name__ == '__main__':
    unittest.main()
