import unittest
import urllib.parse
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

import requests_mock

from podman import PodmanClient, tests
from podman.api.path_utils import get_runtime_dir, get_xdg_config_home


class PodmanClientTestCase(unittest.TestCase):
    """Test the PodmanClient() object."""

    opener = mock.mock_open(
        read_data="""
[containers]
  log_size_max = -1
  pids_limit = 2048
  userns_size = 65536

[engine]
  num_locks = 2048
  active_service = "testing"
  stop_timeout = 10
  [engine.service_destinations]
    [engine.service_destinations.production]
      uri = "ssh://root@localhost:22/run/podman/podman.sock"
      identity = "/home/root/.ssh/id_rsa"
    [engine.service_destinations.testing]
      uri = "ssh://qe@localhost:2222/run/podman/podman.sock"
      identity = "/home/qe/.ssh/id_rsa"

[network]
"""
    )

    def setUp(self) -> None:
        super().setUp()
        self.client = PodmanClient(base_url=tests.BASE_SOCK)

        def mocked_open(self, *args, **kwargs):
            return PodmanClientTestCase.opener(self, *args, **kwargs)

        self.mocked_open = mocked_open

    @mock.patch('requests.Session.close')
    def test_close(self, mock_close):
        self.client.close()

        mock_close.assert_called_once_with()

    @requests_mock.Mocker()
    def test_contextmanager(self, mock):
        body = {
            "host": {
                "arch": "amd65",
                "os": "linux",
            }
        }
        adapter = mock.get(tests.LIBPOD_URL + "/info", json=body)  # noqa: F841

        with PodmanClient(base_url=tests.BASE_SOCK) as client:
            actual = client.info()
        self.assertDictEqual(actual, body)
        self.assertIn("User-Agent", mock.last_request.headers)
        self.assertIn(
            "PodmanPy/", mock.last_request.headers["User-Agent"], mock.last_request.headers
        )

    def test_swarm(self):
        with PodmanClient(base_url=tests.BASE_SOCK) as client:
            with self.assertRaises(NotImplementedError):
                # concrete property
                _ = client.swarm

            with self.assertRaises(NotImplementedError):
                # aliased property
                _ = client.nodes

    def test_connect(self):
        with mock.patch.multiple(Path, open=self.mocked_open, exists=MagicMock(return_value=True)):
            with PodmanClient(connection="testing") as client:
                self.assertEqual(
                    client.api.base_url.geturl(),
                    "http+ssh://qe@localhost:2222/run/podman/podman.sock",
                )

            # Build path to support tests running as root or a user
            expected = Path(get_xdg_config_home()) / "containers" / "containers.conf"
            PodmanClientTestCase.opener.assert_called_with(expected, encoding="utf-8")

    def test_connect_404(self):
        with mock.patch.multiple(Path, open=self.mocked_open, exists=MagicMock(return_value=True)):
            with self.assertRaises(KeyError):
                _ = PodmanClient(connection="not defined")

    def test_connect_default(self):
        with mock.patch.multiple(Path, open=self.mocked_open, exists=MagicMock(return_value=True)):
            with PodmanClient() as client:
                expected = "http+unix://" + urllib.parse.quote_plus(
                    str(Path(get_runtime_dir()) / "podman" / "podman.sock")
                )
                self.assertEqual(client.api.base_url.geturl(), expected)

            # Build path to support tests running as root or a user
            expected = Path(get_xdg_config_home()) / "containers" / "containers.conf"
            PodmanClientTestCase.opener.assert_called_with(expected, encoding="utf-8")


if __name__ == '__main__':
    unittest.main()
