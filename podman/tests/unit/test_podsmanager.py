import unittest

from podman import PodmanClient
from podman.domain.pods import PodsManager


class PodsManagerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url="http+unix://localhost:9999")

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_podmanclient(self):
        manager = self.client.pods
        self.assertIsInstance(manager, PodsManager)


if __name__ == '__main__':
    unittest.main()
