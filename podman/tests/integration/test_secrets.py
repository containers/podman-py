"""Secrets integration tests."""

import random
import unittest
import uuid

from podman import PodmanClient
from podman.errors import NotFound
from podman.tests.integration import base


class SecretsIntegrationTest(base.IntegrationTest):
    """Secrets call integration test"""

    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

    def test_secret_crud(self):
        """Test Secret CRUD."""

        random_string = f"{random.getrandbits(160):x}"
        secret_payload = uuid.uuid4().bytes

        with self.subTest("Create"):
            secret = self.client.secrets.create(f"secret_{random_string}", secret_payload)
            self.assertGreater(len(secret.id), 0)
            self.assertGreater(len(secret.name), 0)
            self.assertTrue(self.client.secrets.exists(secret.id))

        with self.subTest("Inspect"):
            actual = self.client.secrets.get(secret.id)
            self.assertEqual(secret.id, actual.id)

        self.assertTrue(self.client.secrets.exists(secret.name))

        with self.subTest("List"):
            report = self.client.secrets.list()
            ids = [i.id for i in report]
            self.assertIn(secret.id, ids)

        with self.subTest("Delete"):
            actual.remove()

            with self.assertRaises(NotFound):
                self.client.secrets.get(secret.id)


if __name__ == '__main__':
    unittest.main()
