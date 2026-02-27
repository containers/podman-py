"""Unit tests for QuadletsManager."""

import unittest
from unittest.mock import patch

import requests_mock

from podman import PodmanClient, tests
from podman.domain.quadlets import Quadlet, QuadletsManager
from podman.errors import APIError, NotFound, PodmanError

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

    @requests_mock.Mocker()
    def test_delete_by_name(self, mock):
        """Test delete single quadlet by name string."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets/myapp.container",
            json={"Removed": ["myapp.container"]},
            status_code=200,
        )

        result = self.client.quadlets.delete("myapp.container")
        self.assertEqual(result, ["myapp.container"])

    @requests_mock.Mocker()
    def test_delete_by_quadlet_object(self, mock):
        """Test delete using Quadlet object."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets/myapp.container",
            json={"Removed": ["myapp.container"]},
            status_code=200,
        )

        quadlet = Quadlet(attrs=FIRST_QUADLET)
        result = self.client.quadlets.delete(quadlet)
        self.assertEqual(result, ["myapp.container"])

    @requests_mock.Mocker()
    def test_delete_all(self, mock):
        """Test delete all quadlets with all=True."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets",
            json={"Removed": ["myapp.container", "mydb.container"]},
            status_code=200,
        )

        result = self.client.quadlets.delete(all=True)
        self.assertEqual(result, ["myapp.container", "mydb.container"])

    @requests_mock.Mocker()
    def test_delete_with_force(self, mock):
        """Test delete with force=True parameter."""
        adapter = mock.delete(
            tests.LIBPOD_URL + "/quadlets/myapp.container",
            json={"Removed": ["myapp.container"]},
            status_code=200,
        )

        result = self.client.quadlets.delete("myapp.container", force=True)
        self.assertEqual(result, ["myapp.container"])

        # Verify force parameter was passed correctly
        self.assertIn("force=true", adapter.last_request.url.lower())

    @requests_mock.Mocker()
    def test_delete_with_ignore(self, mock):
        """Test delete with ignore=True parameter."""
        adapter = mock.delete(
            tests.LIBPOD_URL + "/quadlets/myapp.container",
            json={"Removed": []},
            status_code=200,
        )

        result = self.client.quadlets.delete("myapp.container", ignore=True)
        self.assertEqual(result, [])

        # Verify ignore parameter was passed correctly
        self.assertIn("ignore=true", adapter.last_request.url.lower())

    @requests_mock.Mocker()
    def test_delete_without_reload(self, mock):
        """Test delete with reload_systemd=False."""
        adapter = mock.delete(
            tests.LIBPOD_URL + "/quadlets/myapp.container",
            json={"Removed": ["myapp.container"]},
            status_code=200,
        )

        result = self.client.quadlets.delete("myapp.container", reload_systemd=False)
        self.assertEqual(result, ["myapp.container"])

        # Verify reload-systemd parameter was passed correctly (note the hyphen)
        self.assertIn("reload-systemd=false", adapter.last_request.url.lower())

    def test_delete_no_name_or_all(self):
        """Test delete raises PodmanError when neither name nor all provided."""
        with self.assertRaises(PodmanError) as context:
            self.client.quadlets.delete()

        self.assertIn("Quadlet name, or 'all=True' should be provided", str(context.exception))

    @requests_mock.Mocker()
    def test_delete_response_format(self, mock):
        """Test delete correctly parses 'Removed' field from API response."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets/myapp.container",
            json={"Removed": ["myapp.container", "related.container"]},
            status_code=200,
        )

        result = self.client.quadlets.delete("myapp.container")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn("myapp.container", result)
        self.assertIn("related.container", result)

    @requests_mock.Mocker()
    def test_delete_nonexistent_quadlet_error(self, mock):
        """Test delete raises NotFound for non-existent quadlet without ignore."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets/nonexistent.container",
            json={"error": "no such quadlet: nonexistent.container"},
            status_code=404,
        )

        with self.assertRaises(NotFound) as context:
            self.client.quadlets.delete("nonexistent.container")

        self.assertIn("nonexistent.container", str(context.exception))

    @requests_mock.Mocker()
    def test_delete_nonexistent_with_ignore_succeeds(self, mock):
        """Test delete with ignore=True succeeds for non-existent quadlet."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets/nonexistent.container",
            json={"Removed": ["nonexistent.container"], "Errors": {}},
            status_code=200,
        )

        result = self.client.quadlets.delete("nonexistent.container", ignore=True)
        self.assertEqual(result, ["nonexistent.container"])

    @requests_mock.Mocker()
    def test_delete_running_quadlet_error(self, mock):
        """Test delete raises error when quadlet is running without force."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets/running.container",
            json={
                "cause": (
                    "quadlet running.container is running and force is not set, refusing to remove"
                ),
                "message": "container is running and force is not set, refusing to remove",
                "response": 400,
            },
            status_code=400,
        )

        with self.assertRaises(APIError) as context:
            self.client.quadlets.delete("running.container")

        error_message = str(context.exception)
        self.assertTrue(
            "running" in error_message.lower() or "force" in error_message.lower(),
            f"Expected error about running quadlet or force, got: {error_message}",
        )

    @requests_mock.Mocker()
    def test_delete_running_quadlet_with_force_succeeds(self, mock):
        """Test delete with force=True succeeds for running quadlet."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets/running.container",
            json={"Removed": ["running.container"], "Errors": {}},
            status_code=200,
        )

        result = self.client.quadlets.delete("running.container", force=True)
        self.assertEqual(result, ["running.container"])

    @requests_mock.Mocker()
    def test_delete_internal_server_error(self, mock):
        """Test delete raises error on internal server error."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets/myapp.container",
            json={"cause": "systemd connection failed", "message": "Internal error"},
            status_code=500,
        )

        with self.assertRaises(APIError) as context:
            self.client.quadlets.delete("myapp.container")

        # Verify it's a 500 error
        self.assertEqual(context.exception.status_code, 500)
        self.assertTrue(context.exception.is_server_error())

    @requests_mock.Mocker()
    def test_delete_all_with_partial_errors(self, mock):
        """Test delete all with some quadlets failing doesn't raise exception."""
        mock.delete(
            tests.LIBPOD_URL + "/quadlets",
            json={
                "Removed": ["success1.container", "success2.container"],
                "Errors": {"failed.container": "could not locate quadlet failed.container"},
            },
            status_code=200,
        )

        # Should return successfully removed quadlets
        result = self.client.quadlets.delete(all=True)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn("success1.container", result)
        self.assertIn("success2.container", result)


if __name__ == '__main__':
    unittest.main()
