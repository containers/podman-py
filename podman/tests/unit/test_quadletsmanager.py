"""Unit tests for QuadletsManager."""

import pytest
import unittest
from unittest.mock import patch

import requests_mock

from podman import PodmanClient, tests
from podman.domain.quadlets import Quadlet, QuadletsManager
from podman.errors import NotFound

FIRST_QUADLET = {
    "Name": "myapp.container",
    "UnitName": "myapp.service",
    "Path": "/home/user/.config/containers/systemd/myapp.container",
    "Status": "Active",
    "App": "",
}

SECOND_QUADLET = {
    "Name": "mydb.container",
    "UnitName": "mydb.service",
    "Path": "/home/user/.config/containers/systemd/mydb.container",
    "Status": "Not loaded",
    "App": "mystack",
}


@pytest.mark.pnext
class QuadletsManagerTestCase(unittest.TestCase):
    """Test QuadletsManager area of concern.

    Note:
        Mock responses need to be coded for libpod returns. The python bindings are responsible
        for mapping to compatible output.
    """

    def setUp(self) -> None:
        super().setUp()
        self.client = PodmanClient(base_url=tests.BASE_SOCK)
        self.addCleanup(self.client.close)

    def test_podmanclient(self):
        """Test that PodmanClient.quadlets returns QuadletsManager."""
        manager = self.client.quadlets
        self.assertIsInstance(manager, QuadletsManager)

    @requests_mock.Mocker()
    def test_exists_true(self, mock):
        """Test exists returns True when quadlet exists."""
        mock.get(
            tests.LIBPOD_URL + "/quadlets/myapp.container/exists",
            status_code=204,
        )
        actual = self.client.quadlets.exists("myapp.container")
        self.assertTrue(actual)

    @requests_mock.Mocker()
    def test_exists_false(self, mock):
        """Test exists returns False when quadlet does not exist."""
        mock.get(
            tests.LIBPOD_URL + "/quadlets/myapp.container/exists",
            status_code=404,
        )
        actual = self.client.quadlets.exists("myapp.container")
        self.assertFalse(actual)

    @requests_mock.Mocker()
    def test_exists_error_status(self, mock):
        """Test exists raises exception for server errors.

        When the server returns an error status code (not 404),
        the method should raise an exception instead of returning False.
        """

        mock.get(
            tests.LIBPOD_URL + "/quadlets/myapp.container/exists",
            text="Internal Server Error",
            status_code=500,
        )

    @requests_mock.Mocker()
    def test_get(self, mock):
        """Test get returns a Quadlet object."""
        # get() now uses quadlets/json with filters
        mock.get(
            tests.LIBPOD_URL + "/quadlets/json",
            json=[FIRST_QUADLET],
        )

        actual = self.client.quadlets.get("myapp.container")
        self.assertIsInstance(actual, Quadlet)
        self.assertEqual(actual.name, "myapp.container")

    @requests_mock.Mocker()
    def test_get_404(self, mock):
        """Test get raises NotFound when quadlet does not exist."""
        mock.get(
            tests.LIBPOD_URL + "/quadlets/json",
            text="Not Found",
            status_code=404,
        )

        with self.assertRaises(NotFound):
            self.client.quadlets.get("myapp.container")

    @requests_mock.Mocker()
    def test_get_empty_list(self, mock):
        """Test get raises NotFound when API returns an empty list."""
        mock.get(
            tests.LIBPOD_URL + "/quadlets/json",
            json=[],
            status_code=200,
        )

        with self.assertRaises(NotFound) as context:
            self.client.quadlets.get("nonexistent.container")

        self.assertIn("nonexistent.container", str(context.exception))

    @requests_mock.Mocker()
    def test_list(self, mock):
        """Test list returns list of Quadlet objects."""
        mock.get(tests.LIBPOD_URL + "/quadlets/json", json=[FIRST_QUADLET, SECOND_QUADLET])

        actual = self.client.quadlets.list()
        self.assertEqual(len(actual), 2)

        self.assertIsInstance(actual[0], Quadlet)
        self.assertEqual(actual[0].name, "myapp.container")

        self.assertIsInstance(actual[1], Quadlet)
        self.assertEqual(actual[1].name, "mydb.container")

    @requests_mock.Mocker()
    def test_list_with_filters(self, mock):
        """Test list with filters."""
        mock.get(tests.LIBPOD_URL + "/quadlets/json", json=[FIRST_QUADLET])

        actual = self.client.quadlets.list(filters={"name": "myapp*"})
        self.assertEqual(len(actual), 1)
        self.assertEqual(actual[0].name, "myapp.container")

    @requests_mock.Mocker()
    def test_list_404(self, mock):
        """Test list returns empty list on 404."""
        mock.get(tests.LIBPOD_URL + "/quadlets/json", text="Not Found", status_code=404)

        actual = self.client.quadlets.list()
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), 0)

    @requests_mock.Mocker()
    def test_get_contents(self, mock):
        """Test get_contents returns file contents."""
        expected_content = "[Container]\nImage=alpine\nExec=echo hello"
        mock.get(
            tests.LIBPOD_URL + "/quadlets/myapp.container/file",
            text=expected_content,
        )

        actual = self.client.quadlets.get_contents("myapp.container")
        self.assertEqual(actual, expected_content)

    @requests_mock.Mocker()
    def test_print_contents(self, mock):
        """Test print_contents prints to stdout and returns None."""
        expected_content = "[Container]\nImage=alpine\nExec=echo hello\n"
        mock.get(
            tests.LIBPOD_URL + "/quadlets/myapp.container/file",
            text=expected_content,
        )

        with patch('builtins.print') as mock_print:
            result = self.client.quadlets.print_contents("myapp.container")
            self.assertIsNone(result)
            mock_print.assert_called_once_with(expected_content.strip())


if __name__ == '__main__':
    unittest.main()
