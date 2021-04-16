import unittest
from contextlib import suppress

from podman import PodmanClient
from podman.errors import APIError, ImageNotFound
from podman.tests.integration import base

# @unittest.skipIf(os.geteuid() != 0, 'Skipping, not running as root')


class ManifestsIntegrationTest(base.IntegrationTest):
    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

        self.alpine_image = self.client.images.pull("quay.io/libpod/alpine", tag="latest")

    def tearDown(self) -> None:
        self.client.images.remove(self.alpine_image, force=True)
        with suppress(ImageNotFound):
            self.client.images.remove("quay.io/unittest/alpine:latest", force=True)

    def test_manifest_crud(self):
        """Test Manifest CRUD."""

        self.assertFalse(
            self.client.manifests.exists("quay.io/unittest/alpine:latest"),
            "Image store is corrupt from previous run",
        )

        with self.subTest("Create"):
            manifest = self.client.manifests.create(["quay.io/unittest/alpine:latest"])
            self.assertEqual(len(manifest.attrs["manifests"]), 0)

            with self.assertRaises(APIError):
                self.client.manifests.create(["123456!@#$%^"])

        with self.subTest("Add"):
            manifest.add([self.alpine_image])
            self.assertIsNotNone(manifest.attrs["manifests"])
            self.assertIsInstance(manifest.attrs["manifests"], list)

            self.assertTrue(
                any([d for d in self.alpine_image.attrs["RepoDigests"] if manifest.id in d]),
                f'{manifest.id} not in any {self.alpine_image.attrs["RepoDigests"]}',
            )

        with self.subTest("Inspect"):
            actual = self.client.manifests.get("quay.io/unittest/alpine:latest")
            self.assertEqual(actual.id, manifest.id)

            actual = self.client.manifests.get(manifest.name)
            self.assertEqual(actual.id, manifest.id)

        with self.subTest("Remove digest"):
            manifest.remove(self.alpine_image.attrs["RepoDigests"][0])
            self.assertEqual(len(manifest.attrs["manifests"]), 0)

    def test_create_409(self):
        """Test that invalid Image names are caught and not corrupt storage."""
        with self.assertRaises(APIError):
            self.client.manifests.create(["InvalidManifestName"])


if __name__ == '__main__':
    unittest.main()
