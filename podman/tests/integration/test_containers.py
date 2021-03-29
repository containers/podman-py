import unittest

import podman.tests.integration.base as base
from podman import PodmanClient
from podman.domain.containers import Container

from podman.domain.images import Image
from podman.errors import NotFound

# @unittest.skipIf(os.geteuid() != 0, 'Skipping, not running as root')


class ContainersIntegrationTest(base.IntegrationTest):
    """Containers Integration tests."""

    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

        self.alpine_image = self.client.images.pull("quay.io/libpod/alpine", tag="latest")

    def test_container_crud(self):
        """Test Container CRUD."""

        with self.subTest("Create from Alpine Image"):
            container = self.client.containers.create(self.alpine_image)
            self.assertIsInstance(container, Container)
            self.assertIsNotNone(container.id)
            self.assertIsInstance(container.image, Image)

            self.assertIn("quay.io/libpod/alpine:latest", container.image.tags)

        with self.subTest("Inspect Container"):
            actual = self.client.containers.get(container.id)
            self.assertIsInstance(actual, Container)
            self.assertEqual(actual.id, container.id)

        with self.subTest("List containers --all"):
            containers = self.client.containers.list(all=True)
            self.assertGreater(len(containers), 0)
            ids = [i.id for i in containers]
            self.assertIn(container.id, ids)

        with self.subTest("Delete Container"):
            container.remove()
            with self.assertRaises(NotFound):
                self.client.containers.get(container.id)


if __name__ == '__main__':
    unittest.main()
