import json
import pathlib
import unittest
from typing import Any, Optional
from unittest import mock
from unittest.mock import mock_open, patch

from dataclasses import dataclass

from podman import api


class TestUtilsCase(unittest.TestCase):
    def test_format_filters(self):
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

    def test_containerignore_404(self):
        actual = api.prepare_containerignore("/does/not/exists")
        self.assertListEqual([], actual)

    @patch.object(pathlib.Path, "exists", return_value=True)
    def test_containerignore_read(self, patch_exists):
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
    def test_containerignore_empty(self, patch_exists):
        data = r"""# unittest
        """

        patch_exists.return_value = True
        with mock.patch("pathlib.Path.open", mock_open(read_data=data)):
            actual = api.prepare_containerignore(".")

        self.assertListEqual(actual, [])
        patch_exists.assert_called_once_with()

    @mock.patch("pathlib.Path.parent", autospec=True)
    def test_containerfile_1(self, mock_parent):
        mock_parent.samefile.return_value = True
        actual = api.prepare_containerfile("/work", "/work/Dockerfile")
        self.assertEqual(actual, "Dockerfile")
        mock_parent.samefile.assert_called()

    @mock.patch("pathlib.Path.parent", autospec=True)
    def test_containerfile_2(self, mock_parent):
        mock_parent.samefile.return_value = True
        actual = api.prepare_containerfile(".", "Dockerfile")
        self.assertEqual(actual, "Dockerfile")
        mock_parent.samefile.assert_called()

    @mock.patch("shutil.copy2")
    def test_containerfile_copy(self, mock_copy):
        mock_copy.return_value = None

        with mock.patch.object(pathlib.Path, "parent") as mock_parent:
            mock_parent.samefile.return_value = False

            actual = api.prepare_containerfile("/work", "/home/Dockerfile")
            self.assertRegex(actual, r"\.containerfile\..*")

    def test_prepare_body_all_types(self):
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

    def test_prepare_body_none(self):
        payload = {
            "String": "",
            "Integer": None,
            "Boolean": False,
            "Dictionary": dict(),
            "Tuple": tuple(),
            "List": list(),
        }
        actual = api.prepare_body(payload)
        self.assertEqual(actual, '{"Boolean": false}')

    def test_prepare_body_embedded(self):
        payload = {
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

    def test_prepare_body_dict_empty_string(self):
        payload = {"Dictionary": {"key1": "", "key2": {"key3": ""}, "key4": [], "key5": {}}}

        actual = api.prepare_body(payload)
        actual_dict = json.loads(actual)
        payload["Dictionary"].pop("key4")
        payload["Dictionary"].pop("key5")

        self.assertDictEqual(payload, actual_dict)


if __name__ == '__main__':
    unittest.main()
