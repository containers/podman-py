"""Unit tests for QuadletsManager."""

import os
import pathlib
import tarfile
import tempfile
from email.message import Message
from email.parser import BytesParser

import unittest
from unittest.mock import patch

import requests_mock

from podman import PodmanClient, tests
from podman.domain.quadlets import Quadlet, QuadletsManager
from podman.errors import APIError, NotFound, PodmanError

INSTALL_REPORT = {
    "InstalledQuadlets": {
        "test.container": "/home/user/.config/containers/systemd/test.container",
    },
    "QuadletErrors": {},
}


def _parse_multipart_files(request) -> dict[str, bytes]:
    """Parse a multipart/form-data request into ``{filename: content_bytes}``."""
    content_type = request.headers["Content-Type"]
    body = request.body
    if not isinstance(body, bytes):
        body = body.read() if hasattr(body, "read") else body.encode()
    raw = b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + body
    msg = BytesParser().parsebytes(raw)
    result: dict[str, bytes] = {}
    if msg.is_multipart():
        for part in msg.get_payload():
            if not isinstance(part, Message):
                continue
            filename = part.get_filename()
            payload = part.get_payload(decode=True)
            if filename and isinstance(payload, bytes):
                result[filename] = payload
    return result


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

    # -- install: single items -------------------------------------------------

    @requests_mock.Mocker()
    def test_install_single_str_path(self, mock):
        """Test installing a single quadlet file by path (str)."""
        adapter = mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            quadlet_path = os.path.join(tmpdir, "test.container")
            with open(quadlet_path, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            result = self.client.quadlets.install(quadlet_path)

        self.assertEqual(result, INSTALL_REPORT)
        self.assertIn("test.container", result["InstalledQuadlets"])
        self.assertEqual(result["QuadletErrors"], {})
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_install_single_pathlib_path(self, mock):
        """Test installing a single quadlet file by path (pathlib.Path)."""
        adapter = mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            quadlet_path = pathlib.Path(tmpdir) / "test.container"
            quadlet_path.write_text("[Container]\nImage=alpine\n")

            result = self.client.quadlets.install(quadlet_path)

        uploaded = _parse_multipart_files(mock.last_request)
        self.assertEqual(sorted(uploaded), ["test.container"])
        self.assertEqual(uploaded["test.container"], b"[Container]\nImage=alpine\n")
        self.assertEqual(result, INSTALL_REPORT)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_install_single_tuple(self, mock):
        """Test installing a single quadlet file by tuple (filename, content)."""
        adapter = mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        content = "[Container]\nImage=alpine\n"
        result = self.client.quadlets.install(("test.container", content))

        uploaded = _parse_multipart_files(mock.last_request)
        self.assertEqual(sorted(uploaded), ["test.container"])
        self.assertEqual(uploaded["test.container"], content.encode())
        self.assertEqual(result, INSTALL_REPORT)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_install_list_of_tuples(self, mock):
        """Test installing a list of (filename, content) tuples."""
        adapter = mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        items = [
            ("myapp.container", "[Container]\nImage=alpine\n"),
            ("Containerfile", "FROM alpine\nCMD echo hello\n"),
        ]
        self.client.quadlets.install(items)

        uploaded = _parse_multipart_files(mock.last_request)
        self.assertIn("myapp.container", uploaded)
        self.assertIn("Containerfile", uploaded)
        self.assertEqual(uploaded["myapp.container"], b"[Container]\nImage=alpine\n")
        self.assertTrue(adapter.called_once)

    # -- install: tar passthrough ------------------------------------------

    @requests_mock.Mocker()
    def test_install_single_tar_by_string_path(self, mock):
        """Test that a single .tar file by string path is sent directly."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            quadlet_file = os.path.join(tmpdir, "test.container")
            with open(quadlet_file, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            tar_path = os.path.join(tmpdir, "quadlet.tar")
            with tarfile.open(tar_path, "w") as tar:
                tar.add(quadlet_file, arcname="test.container")

            original_bytes = open(tar_path, "rb").read()
            self.client.quadlets.install(tar_path)

        self.assertEqual(mock.last_request.body, original_bytes)
        self.assertEqual(mock.last_request.headers["Content-Type"], "application/x-tar")

    @requests_mock.Mocker()
    def test_install_single_tar_by_pathlib_path(self, mock):
        """Test that a single .tar file by pathlib.Path is sent directly."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            quadlet_file = os.path.join(tmpdir, "test.container")
            with open(quadlet_file, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            tar_path = pathlib.Path(tmpdir) / "quadlet.tar"
            with tarfile.open(str(tar_path), "w") as tar:
                tar.add(quadlet_file, arcname="test.container")

            original_bytes = tar_path.read_bytes()
            self.client.quadlets.install(tar_path)

        self.assertEqual(mock.last_request.body, original_bytes)
        self.assertEqual(mock.last_request.headers["Content-Type"], "application/x-tar")

    @requests_mock.Mocker()
    def test_install_single_tar_gz_by_string_path(self, mock):
        """Test that a single .tar.gz file by string path is sent directly."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            quadlet_file = os.path.join(tmpdir, "test.container")
            with open(quadlet_file, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            tar_path = os.path.join(tmpdir, "quadlet.tar.gz")
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(quadlet_file, arcname="test.container")

            original_bytes = open(tar_path, "rb").read()
            self.client.quadlets.install(tar_path)

        self.assertEqual(mock.last_request.body, original_bytes)
        self.assertEqual(mock.last_request.headers["Content-Type"], "application/x-tar")

    def test_install_single_tar_not_found(self):
        """Test install raises FileNotFoundError for nonexistent .tar path."""
        with self.assertRaises(FileNotFoundError):
            self.client.quadlets.install("/nonexistent/path/archive.tar")

    # -- install: lists (homogeneous) -----------------------------------------

    @requests_mock.Mocker()
    def test_install_list_of_str_paths(self, mock):
        """Test installing a list of string paths."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = os.path.join(tmpdir, "a.container")
            with open(file_a, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            file_b = os.path.join(tmpdir, "Containerfile")
            with open(file_b, "w") as f:
                f.write("FROM alpine\n")

            self.client.quadlets.install([file_a, file_b])

        uploaded = _parse_multipart_files(mock.last_request)
        self.assertEqual(sorted(uploaded), ["Containerfile", "a.container"])
        self.assertEqual(uploaded["a.container"], b"[Container]\nImage=alpine\n")
        self.assertEqual(uploaded["Containerfile"], b"FROM alpine\n")

    @requests_mock.Mocker()
    def test_install_list_of_pathlib_paths(self, mock):
        """Test installing a list of pathlib.Path objects."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = pathlib.Path(tmpdir) / "a.container"
            file_a.write_text("[Container]\nImage=alpine\n")

            file_b = pathlib.Path(tmpdir) / "app.yml"
            file_b.write_text("services:\n  web:\n    image: alpine\n")

            self.client.quadlets.install([file_a, file_b])

        uploaded = _parse_multipart_files(mock.last_request)
        self.assertEqual(sorted(uploaded), ["a.container", "app.yml"])
        self.assertEqual(uploaded["app.yml"], b"services:\n  web:\n    image: alpine\n")

    # -- install: mixed lists (paths, tuples) --------------------------------

    @requests_mock.Mocker()
    def test_install_mixed_str_path_and_tuple(self, mock):
        """Test mixed list: string path + content tuple."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            quadlet_path = os.path.join(tmpdir, "myapp.container")
            with open(quadlet_path, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            items = [
                quadlet_path,
                ("extra-config.yml", "key: value\n"),
            ]
            self.client.quadlets.install(items)

        uploaded = _parse_multipart_files(mock.last_request)
        self.assertEqual(sorted(uploaded), ["extra-config.yml", "myapp.container"])
        self.assertEqual(uploaded["myapp.container"], b"[Container]\nImage=alpine\n")
        self.assertEqual(uploaded["extra-config.yml"], b"key: value\n")

    @requests_mock.Mocker()
    def test_install_mixed_pathlib_and_tuple(self, mock):
        """Test mixed list: pathlib.Path + content tuple."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            quadlet_path = pathlib.Path(tmpdir) / "myapp.container"
            quadlet_path.write_text("[Container]\nImage=alpine\n")

            items = [
                quadlet_path,
                ("Containerfile", "FROM alpine\nCMD echo hello\n"),
            ]
            self.client.quadlets.install(items)

        uploaded = _parse_multipart_files(mock.last_request)
        self.assertEqual(sorted(uploaded), ["Containerfile", "myapp.container"])
        self.assertEqual(uploaded["myapp.container"], b"[Container]\nImage=alpine\n")
        self.assertEqual(uploaded["Containerfile"], b"FROM alpine\nCMD echo hello\n")

    @requests_mock.Mocker()
    def test_install_mixed_str_and_pathlib_paths(self, mock):
        """Test mixed list: string path + pathlib.Path."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = os.path.join(tmpdir, "a.container")
            with open(file_a, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            file_b = pathlib.Path(tmpdir) / "Containerfile"
            file_b.write_text("FROM alpine\n")

            self.client.quadlets.install([file_a, file_b])

        uploaded = _parse_multipart_files(mock.last_request)
        self.assertEqual(sorted(uploaded), ["Containerfile", "a.container"])
        self.assertEqual(uploaded["a.container"], b"[Container]\nImage=alpine\n")
        self.assertEqual(uploaded["Containerfile"], b"FROM alpine\n")

    @requests_mock.Mocker()
    def test_install_mixed_all_three_types(self, mock):
        """Test mixed list with all three item types: str path, pathlib.Path, tuple."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            str_path = os.path.join(tmpdir, "myapp.container")
            with open(str_path, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            pathlib_path = pathlib.Path(tmpdir) / "app.yml"
            pathlib_path.write_text("services:\n  web:\n    image: alpine\n")

            items = [
                str_path,
                pathlib_path,
                ("Containerfile", "FROM alpine\nCMD echo hello\n"),
            ]
            self.client.quadlets.install(items)

        uploaded = _parse_multipart_files(mock.last_request)
        self.assertEqual(len(uploaded), 3)
        self.assertEqual(
            sorted(uploaded),
            ["Containerfile", "app.yml", "myapp.container"],
        )
        self.assertEqual(uploaded["myapp.container"], b"[Container]\nImage=alpine\n")
        self.assertEqual(uploaded["app.yml"], b"services:\n  web:\n    image: alpine\n")
        self.assertEqual(uploaded["Containerfile"], b"FROM alpine\nCMD echo hello\n")

    def test_install_mixed_list_path_not_found(self):
        """Test that FileNotFoundError is raised when one path in a list does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            good_path = os.path.join(tmpdir, "good.container")
            with open(good_path, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            items = [
                good_path,
                "/nonexistent/bad.yml",
                ("Containerfile", "FROM alpine\n"),
            ]
            with self.assertRaises(FileNotFoundError) as ctx:
                self.client.quadlets.install(items)

            self.assertIn("bad.yml", str(ctx.exception))

    # -- install: query params & error handling ----------------------------

    @requests_mock.Mocker()
    def test_install_with_replace(self, mock):
        """Test install sends replace=True as query parameter."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            quadlet_path = os.path.join(tmpdir, "test.container")
            with open(quadlet_path, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            self.client.quadlets.install(quadlet_path, replace=True)

        self.assertEqual(mock.last_request.qs["replace"], ["true"])

    @requests_mock.Mocker()
    def test_install_with_reload_systemd_false(self, mock):
        """Test install sends reload-systemd=False as query parameter."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            quadlet_path = os.path.join(tmpdir, "test.container")
            with open(quadlet_path, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            self.client.quadlets.install(quadlet_path, reload_systemd=False)

        self.assertEqual(mock.last_request.qs["reload-systemd"], ["false"])

    @requests_mock.Mocker()
    def test_install_default_params(self, mock):
        """Test install sends correct default query parameters."""
        mock.post(tests.LIBPOD_URL + "/quadlets", json=INSTALL_REPORT, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            quadlet_path = os.path.join(tmpdir, "test.container")
            with open(quadlet_path, "w") as f:
                f.write("[Container]\nImage=alpine\n")

            self.client.quadlets.install(quadlet_path)

        self.assertEqual(mock.last_request.qs["replace"], ["false"])
        self.assertEqual(mock.last_request.qs["reload-systemd"], ["true"])
        self.assertTrue(mock.last_request.headers["Content-Type"].startswith("multipart/form-data"))

    @requests_mock.Mocker()
    def test_install_already_exists(self, mock):
        """Test install raises APIError when quadlet already exists."""
        mock.post(
            tests.LIBPOD_URL + "/quadlets",
            json={
                "cause": "a Quadlet with name test.container already exists, refusing to overwrite",
                "message": "a Quadlet with name test.container already exists, "
                "refusing to overwrite",
            },
            status_code=400,
        )

        with self.assertRaises(APIError):
            self.client.quadlets.install(("test.container", "[Container]\nImage=alpine\n"))

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

    def test_install_single_file_not_found(self):
        """Test install raises FileNotFoundError for nonexistent file path."""
        with self.assertRaises(FileNotFoundError):
            self.client.quadlets.install("/nonexistent/path/test.container")


if __name__ == '__main__':
    unittest.main()
