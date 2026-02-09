"""Unit tests for Quadlet domain class."""

import unittest
from unittest.mock import patch

import requests_mock

from podman import PodmanClient, tests
from podman.domain.quadlets import Quadlet, QuadletsManager

FIRST_QUADLET = {
    "Name": "myapp.container",
    "UnitName": "myapp.service",
    "Path": "/home/user/.config/containers/systemd/myapp.container",
    "Status": "Active",
    "App": "",
}


class QuadletTestCase(unittest.TestCase):
    """Test Quadlet domain class."""

    def setUp(self) -> None:
        super().setUp()
        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()
        self.client.close()

    def test_name(self):
        """Test name property."""
        actual = Quadlet(attrs=FIRST_QUADLET)
        self.assertEqual(actual.name, "myapp.container")

    def test_unit_name(self):
        """Test unit_name property."""
        actual = Quadlet(attrs=FIRST_QUADLET)
        self.assertEqual(actual.unit_name, "myapp.service")

    def test_path(self):
        """Test path property."""
        actual = Quadlet(attrs=FIRST_QUADLET)
        self.assertEqual(actual.path, "/home/user/.config/containers/systemd/myapp.container")

    def test_status(self):
        """Test status property."""
        actual = Quadlet(attrs=FIRST_QUADLET)
        self.assertEqual(actual.status, "Active")

    def test_application(self):
        """Test application property."""
        actual = Quadlet(attrs=FIRST_QUADLET)
        self.assertEqual(actual.application, "")

    def test_application_with_value(self):
        """Test application property with a value."""
        quadlet_with_app = {**FIRST_QUADLET, "App": "mystack"}
        actual = Quadlet(attrs=quadlet_with_app)
        self.assertEqual(actual.application, "mystack")

    def test_repr(self):
        """Test string representation."""
        actual = Quadlet(attrs=FIRST_QUADLET)
        self.assertEqual(repr(actual), "<Quadlet: myapp.container>")

    @requests_mock.Mocker()
    def test_get_contents(self, mock):
        """Test get_contents method returns file contents."""
        expected_content = "[Container]\nImage=alpine\nExec=echo hello"
        mock.get(
            tests.LIBPOD_URL + "/quadlets/myapp.container/file",
            text=expected_content,
        )
        quadlet_manager = QuadletsManager(self.client.api)
        quadlet = quadlet_manager.prepare_model(attrs=FIRST_QUADLET)

        actual = quadlet.get_contents()
        self.assertEqual(actual, expected_content)

    @requests_mock.Mocker()
    def test_print_contents(self, mock):
        """Test print_contents method prints to stdout."""
        expected_content = "[Container]\nImage=alpine\nExec=echo hello\n"
        mock.get(
            tests.LIBPOD_URL + "/quadlets/myapp.container/file",
            text=expected_content,
        )
        quadlet_manager = QuadletsManager(self.client.api)
        quadlet = quadlet_manager.prepare_model(attrs=FIRST_QUADLET)

        with patch('builtins.print') as mock_print:
            result = quadlet.print_contents()
            self.assertIsNone(result)
            mock_print.assert_called_once_with(expected_content.strip())

    @requests_mock.Mocker()
    def test_delete(self, mock):
        """Test Quadlet instance delete delegates to manager correctly."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets/myapp.container",
            json={"Removed": ["myapp.container"]},
            status_code=200,
        )
        quadlet_manager = QuadletsManager(self.client.api)
        quadlet = quadlet_manager.prepare_model(attrs=FIRST_QUADLET)

        result = quadlet.delete()
        self.assertEqual(result, ["myapp.container"])

    @requests_mock.Mocker()
    def test_delete_with_kwargs(self, mock):
        """Test Quadlet delete passes kwargs (force, ignore, reload_systemd) through."""
        adapter = mock.delete(
            tests.LIBPOD_URL + "/quadlets/myapp.container",
            json={"Removed": ["myapp.container"]},
            status_code=200,
        )
        quadlet_manager = QuadletsManager(self.client.api)
        quadlet = quadlet_manager.prepare_model(attrs=FIRST_QUADLET)

        result = quadlet.delete(force=True, ignore=True, reload_systemd=False)
        self.assertEqual(result, ["myapp.container"])

        # Verify all parameters were passed correctly
        url_lower = adapter.last_request.url.lower()
        self.assertIn("force=true", url_lower)
        self.assertIn("ignore=true", url_lower)
        self.assertIn("reload-systemd=false", url_lower)


if __name__ == '__main__':
    unittest.main()
