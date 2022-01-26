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
        self.invalid_manifest_name = "InvalidManifestName"

    def tearDown(self) -> None:
        if self.client.images.exists(self.invalid_manifest_name):
            self.client.images.remove(self.invalid_manifest_name, force=True)

        self.client.images.remove(self.alpine_image, force=True)
        with suppress(ImageNotFound):
            self.client.images.remove("localhost/unittest/alpine", force=True)

    def test_manifest_crud(self):
        """Test Manifest CRUD."""

        self.assertFalse(
            self.client.manifests.exists("localhost/unittest/alpine"),
            "Image store is corrupt from previous run",
        )

        with self.subTest("Create"):
            manifest = self.client.manifests.create(
                "localhost/unittest/alpine", ["quay.io/libpod/alpine:latest"]
            )
            self.assertEqual(len(manifest.attrs["manifests"]), 1, manifest.attrs)
            self.assertTrue(self.client.manifests.exists(manifest.names), manifest.id)

            with self.assertRaises(APIError):
                self.client.manifests.create("123456!@#$%^")

        with self.subTest("Add"):
            manifest.add([self.alpine_image])
            self.assertIsNotNone(manifest.attrs["manifests"])
            self.assertIsInstance(manifest.attrs["manifests"], list)

            self.assertTrue(
                any([d for d in self.alpine_image.attrs["RepoDigests"] if manifest.id in d]),
                f'{manifest.id} not in any {self.alpine_image.attrs["RepoDigests"]}',
            )

        with self.subTest("Inspect"):
            actual = self.client.manifests.get("quay.io/libpod/alpine:latest")
            self.assertEqual(actual.id, manifest.id)

            actual = self.client.manifests.get(manifest.name)
            self.assertEqual(actual.id, manifest.id)

            self.assertEqual(actual.version, 2)

        with self.subTest("Remove digest"):
            manifest.remove(self.alpine_image.attrs["RepoDigests"][0])
            self.assertEqual(len(manifest.attrs["manifests"]), 0)

    def test_create_409(self):
        """Test that invalid Image names are caught and not corrupt storage."""
        with self.assertRaises(APIError):
            self.client.manifests.create(self.invalid_manifest_name)


if __name__ == '__main__':
    unittest.main()
