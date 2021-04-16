import unittest

from podman import PodmanClient, tests
from podman.domain.secrets import SecretsManager


class SecretsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_podmanclient(self):
        manager = self.client.secrets
        self.assertIsInstance(manager, SecretsManager)


if __name__ == '__main__':
    unittest.main()
