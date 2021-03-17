import pathlib
import unittest
from dataclasses import dataclass
from typing import Any, Optional
from unittest import mock
from unittest.mock import Mock, mock_open

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
                name="List[str]", input=["reference=fedora"], expected='{"reference": ["fedora"]}'
            ),
            TestCase(
                name="Dict[str,str]",
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

    def test_dockerignore_404(self):
        actual = api.prepare_dockerignore("/does/not/exists")
        self.assertListEqual([], actual)

    @mock.patch("os.path.exists")
    def test_dockerignore_read(self, patch_exists):
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

        patch_exists.return_value = True
        with mock.patch("builtins.open", mock_open(read_data=data)):
            actual = api.prepare_dockerignore(".")

        self.assertListEqual(
            actual, ["logs/", "passwords.txt", ".git", ".cache", "*.md", "**/*.class"]
        )
        patch_exists.assert_called_once_with("./.dockerignore")

    @mock.patch("os.path.exists")
    def test_dockerignore_empty(self, patch_exists):
        data = r"""# unittest
        """

        patch_exists.return_value = True
        with mock.patch("builtins.open", mock_open(read_data=data)):
            actual = api.prepare_dockerignore(".")

        self.assertListEqual(actual, [])
        patch_exists.assert_called_once_with("./.dockerignore")

    @mock.patch("pathlib.Path", autospec=True)
    def test_dockerfile(self, mock_path):
        mock_parent = mock_path.parent.return_value = Mock()
        mock_parent.samefile.return_value = True

        actual = api.prepare_containerfile("/work", "/work/Dockerfile")
        self.assertEqual(actual, "/work/Dockerfile")
        mock_path.assert_called()

    @mock.patch("pathlib.Path", autospec=True)
    def test_dockerfile(self, mock_path):
        mock_parent = mock_path.parent.return_value = Mock()
        mock_parent.samefile.return_value = True

        actual = api.prepare_containerfile("/work", "/work/Dockerfile")
        self.assertEqual(actual, "/work/Dockerfile")
        mock_path.assert_called()

    @mock.patch("shutil.copy2")
    def test_dockerfile_copy(self, mock_copy):
        mock_copy.return_value = None

        with mock.patch.object(pathlib.Path, "parent") as mock_parent:
            mock_parent.samefile.return_value = False

            actual = api.prepare_containerfile("/work", "/home/Dockerfile")
            self.assertRegex(actual, r"\.containerfile\..*")


if __name__ == '__main__':
    unittest.main()
