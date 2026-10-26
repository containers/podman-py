import json
import pathlib
import unittest
from typing import Any, Optional
from unittest import mock
from unittest.mock import mock_open, patch

from dataclasses import dataclass

from podman import api


class TestUtilsCase(unittest.TestCase):
    def test_format_filters(self) -> None:
        @dataclass
        class TestCase:
            name: str
            input: Any
            expected: Optional[str]

        cases = [
            TestCase(name="empty str", input="", expected=None),
            TestCase(name="str", input="reference=fedora", expected='{"reference": ["fedora"]}'),
            TestCase(
                name="list[str]", input=["reference=fedora"], expected='{"reference": ["fedora"]}'
            ),
            TestCase(
                name="dict[str,str]",
                input={"reference": "fedora"},
                expected='{"reference": ["fedora"]}',
            ),
        ]

        for case in cases:
            actual = api.prepare_filters(case.input)
            self.assertEqual(
                case.expected,
                actual,
                f"failed test {case.name} expected {case.expected}, actual {actual}",
            )

            if actual is not None:
                self.assertIsInstance(actual, str)

    def test_format_list_valued_filters(self) -> None:
        cases: list[tuple[dict[str, Any], Optional[dict[str, list[str]]]]] = [
            ({"label": ["team=platform", "env=test"]}, {"label": ["team=platform", "env=test"]}),
            ({"label": ["enabled"], "exited": 0}, {"label": ["enabled"], "exited": ["0"]}),
            ({"exited": [0, 1]}, {"exited": ["0", "1"]}),
            ({"label": [], "status": "running"}, {"status": ["running"]}),
            ({"label": [None, "enabled"], "status": None}, {"label": ["enabled"]}),
            ({"label": []}, None),
            ({"label": [None]}, None),
        ]
        cases.extend(
            (
                {
                    key: tuple(value) if isinstance(value, list) else value
                    for key, value in filters.items()
                },
                expected,
            )
            for filters, expected in list(cases)
        )
        for filters, expected in cases:
            with self.subTest(filters=filters):
                actual = api.prepare_filters(filters)
                self.assertEqual(json.loads(actual) if actual is not None else None, expected)

    def test_containerignore_404(self) -> None:
        actual = api.prepare_containerignore("/does/not/exists")
        self.assertListEqual([], actual)

    @patch.object(pathlib.Path, "exists", return_value=True)
    def test_containerignore_read(self, patch_exists) -> None:
        data = r"""# unittest

        #Ignore the logs directory
        logs/

        #Ignoring the password file
        passwords.txt

        #Ignoring git and cache folders
        .git
        .cache

        #Ignoring all the markdown and class files
        *.md
        **/*.class
        """

        with mock.patch("pathlib.Path.open", mock_open(read_data=data)):
            actual = api.prepare_containerignore(".")

        self.assertListEqual(
            actual, ["logs/", "passwords.txt", ".git", ".cache", "*.md", "**/*.class"]
        )
        patch_exists.assert_called_once_with()

    @patch.object(pathlib.Path, "exists", return_value=True)
    def test_containerignore_empty(self, patch_exists) -> None:
        data = r"""# unittest
        """

        patch_exists.return_value = True
        with mock.patch("pathlib.Path.open", mock_open(read_data=data)):
            actual = api.prepare_containerignore(".")

        self.assertListEqual(actual, [])
        patch_exists.assert_called_once_with()

    @mock.patch("pathlib.Path.parent", autospec=True)
    def test_containerfile_1(self, mock_parent) -> None:
        mock_parent.samefile.return_value = True
        actual = api.prepare_containerfile("/work", "/work/Dockerfile")
        self.assertEqual(actual, "Dockerfile")
        mock_parent.samefile.assert_called()

    @mock.patch("pathlib.Path.parent", autospec=True)
    def test_containerfile_2(self, mock_parent) -> None:
        mock_parent.samefile.return_value = True
        actual = api.prepare_containerfile(".", "Dockerfile")
        self.assertEqual(actual, "Dockerfile")
        mock_parent.samefile.assert_called()

    @mock.patch("shutil.copy2")
    def test_containerfile_copy(self, mock_copy) -> None:
        mock_copy.return_value = None

        with mock.patch.object(pathlib.Path, "parent") as mock_parent:
            mock_parent.samefile.return_value = False

            actual = api.prepare_containerfile("/work", "/home/Dockerfile")
            self.assertRegex(actual, r"\.containerfile\..*")

    def test_prepare_body_all_types(self) -> None:
        payload = {
            "String": "string",
            "Integer": 42,
            "Boolean": True,
            "Dictionary": {"key": "value"},
            "Tuple": (1, 2),
            "List": [1, 2],
        }
        actual = api.prepare_body(payload)
        self.assertEqual(actual, json.dumps(payload, sort_keys=True))

    def test_prepare_body_none(self) -> None:
        payload: dict[str, Any] = {
            "String": "",
            "Integer": None,
            "Boolean": False,
            "Dictionary": dict(),
            "Tuple": tuple(),
            "List": list(),
        }
        actual = api.prepare_body(payload)
        self.assertEqual(actual, '{"Boolean": false}')

    def test_prepare_body_embedded(self) -> None:
        payload: dict[str, Any] = {
            "String": "",
            "Integer": None,
            "Boolean": False,
            "Dictionary": {"key": "value"},
            "Dictionary2": {"key": {"key2": None}},
            "Tuple": tuple(),
            "List": [None],
            "Set1": {"item1", "item2"},
            "Set2": {None},
        }
        actual = api.prepare_body(payload)
        actual_dict = json.loads(actual)

        # Because of the sets above we have to do some type dances to test results
        self.assertListEqual([*actual_dict], ["Boolean", "Dictionary", "Set1"])
        self.assertEqual(actual_dict["Boolean"], payload["Boolean"])
        self.assertDictEqual(actual_dict["Dictionary"], payload["Dictionary"])
        self.assertEqual(set(actual_dict["Set1"]), {"item1", "item2"})

    def test_prepare_body_dict_empty_string(self) -> None:
        payload = {"Dictionary": {"key1": "", "key2": {"key3": ""}, "key4": [], "key5": {}}}

        actual = api.prepare_body(payload)
        actual_dict = json.loads(actual)
        payload["Dictionary"].pop("key4")
        payload["Dictionary"].pop("key5")

        self.assertDictEqual(payload, actual_dict)

    def test_encode_auth_header(self):
        auth_config = {
            "username": "user",
            "password": "pass",
        }
        expected = b"eyJ1c2VybmFtZSI6ICJ1c2VyIiwgInBhc3N3b3JkIjogInBhc3MifQ=="
        actual = api.encode_auth_header(auth_config)
        self.assertEqual(expected, actual)

    def test_normalize_registry(self):
        """Test registry normalization for equivalent forms."""

        @dataclass
        class TestCase:
            name: str
            input: str
            expected: str

        cases = [
            TestCase(name="with scheme and v2", input="https://quay.io/v2", expected="quay.io"),
            TestCase(name="with scheme", input="https://quay.io", expected="quay.io"),
            TestCase(name="without scheme", input="quay.io", expected="quay.io"),
            TestCase(name="with trailing slash", input="quay.io/", expected="quay.io"),
            TestCase(name="docker.io", input="docker.io", expected="docker.io"),
            TestCase(name="localhost with port", input="localhost:5000", expected="localhost:5000"),
            TestCase(
                name="localhost with port and v2",
                input="https://localhost:5000/v2",
                expected="localhost:5000",
            ),
            TestCase(name="ghcr.io", input="ghcr.io", expected="ghcr.io"),
            TestCase(
                name="custom registry with port",
                input="myregistry.com:8080",
                expected="myregistry.com:8080",
            ),
            TestCase(name="http scheme", input="http://quay.io/v2", expected="quay.io"),
        ]

        for case in cases:
            actual = api.normalize_registry(case.input)
            self.assertEqual(
                case.expected,
                actual,
                f"failed test {case.name}: expected {case.expected}, actual {actual}",
            )

    def test_normalize_registry_preserves_ports(self):
        """Test that different ports are not normalized to the same value."""
        port_5000 = api.normalize_registry("localhost:5000")
        port_6000 = api.normalize_registry("localhost:6000")
        self.assertNotEqual(port_5000, port_6000, "Different ports should not match")

    def test_normalize_registry_empty(self):
        """Test that empty registry raises ValueError."""
        with self.assertRaises(ValueError):
            api.normalize_registry("")


if __name__ == '__main__':
    unittest.main()
