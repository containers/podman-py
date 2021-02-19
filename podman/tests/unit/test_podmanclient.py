import unittest
from unittest import mock

from podman import PodmanClient


class TestPodmanClient(unittest.TestCase):
    """Test the PodmanClient() object."""

    def setUp(self) -> None:
        super().setUp()
        self.client = PodmanClient(base_url='unix://localhost:9999')

    @mock.patch('requests.Session.close')
    def test_close(self, mock_close):
        self.client.close()

        mock_close.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
