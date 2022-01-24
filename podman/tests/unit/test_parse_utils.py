import datetime
import ipaddress
import unittest
from typing import Any, Optional

from dataclasses import dataclass

from podman import api


class ParseUtilsTestCase(unittest.TestCase):
    def test_parse_repository(self):
        @dataclass
        class TestCase:
            name: str
            input: Any
            expected: Optional[str]

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
            api.prepare_timestamp("bad input")

    def test_prepare_cidr(self):
        net = ipaddress.IPv4Network("127.0.0.0/24")
        self.assertEqual(api.prepare_cidr(net), ("127.0.0.0", "////AA=="))


if __name__ == '__main__':
    unittest.main()
