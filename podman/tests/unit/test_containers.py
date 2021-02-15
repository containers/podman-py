import unittest
from unittest import mock
from unittest.mock import Mock

from podman import PodmanClient


class MockAPIClient:
    pass


class TestClientContainers(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.mock_apiclient = mock.patch('podman.domain.APIClient', MockAPIClient)

    def tearDown(self) -> None:
        self.mock_apiclient.stop()

    def test_podmanclient(self):
        # Exercise __init__() code
        # FIXME haven't found a good assertion to test yet
        client = PodmanClient(base_url='unix://localhost:9999')
        client.containers


if __name__ == '__main__':
    unittest.main()
