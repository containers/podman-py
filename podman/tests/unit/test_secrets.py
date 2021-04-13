import unittest

from podman import PodmanClient
from podman.domain.secrets import SecretsManager


class SecretsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url="http+unix://localhost:9999")

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_podmanclient(self):
        manager = self.client.secrets
        self.assertIsInstance(manager, SecretsManager)


if __name__ == '__main__':
    unittest.main()
