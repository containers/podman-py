import unittest
from unittest import mock

import requests_mock

from podman import PodmanClient, tests


class TestPodmanClient(unittest.TestCase):
    """Test the PodmanClient() object."""

    def setUp(self) -> None:
        super().setUp()
        self.client = PodmanClient(base_url=tests.BASE_SOCK)

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
        adapter = mock.get(tests.LIBPOD_URL + "/info", json=body)

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


if __name__ == '__main__':
    unittest.main()
