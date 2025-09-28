import random
import unittest

from podman import PodmanClient
from podman.errors import NotFound
from podman.tests.integration import base
from podman.tests.utils import PODMAN_VERSION


class VolumesIntegrationTest(base.IntegrationTest):
    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

    def test_volume_crud(self):
        """Test Volume CRUD."""
        volume_name = f"volume_{random.getrandbits(160):x}"
        self.assertFalse(
            self.client.volumes.exists(volume_name), "Storage is corrupt from previous run"
        )

        with self.subTest("Create"):
            volume = self.client.volumes.create(volume_name)
            self.assertEqual(volume.name, volume_name)

        with self.subTest("Get"):
            actual = self.client.volumes.get(volume_name)
            self.assertDictEqual(actual.attrs, volume.attrs)

            self.assertTrue(self.client.volumes.exists(volume_name))

        with self.subTest("List"):
            report = self.client.volumes.list()
            names = [i.name for i in report]
            self.assertIn(volume_name, names)

        if PODMAN_VERSION >= (5, 6, 0):
            with self.subTest("Export"):
                archive_bytes = self.client.volumes.export_archive(volume_name)

            with self.subTest("Import"):
                self.client.volumes.import_archive(volume_name, archive_bytes)

        with self.subTest("Remove"):
            self.client.volumes.remove(volume_name, force=True)
            with self.assertRaises(NotFound):
                self.client.volumes.get(volume_name)

    def test_inspect_404(self):
        with self.assertRaises(NotFound):
            self.client.volumes.get("NoSuchVolume")


if __name__ == '__main__':
    unittest.main()
