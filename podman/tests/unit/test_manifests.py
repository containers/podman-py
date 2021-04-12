import unittest

from podman import PodmanClient
from podman.domain.manifests import ManifestsManager, Manifest


class ManifestTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url="http+unix://localhost:9999")

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_podmanclient(self):
        manager = self.client.manifests
        self.assertIsInstance(manager, ManifestsManager)

    def test_list(self):
        with self.assertRaises(NotImplementedError):
            self.client.manifests.list()

    def test_name(self):
        with self.assertRaises(ValueError):
            manifest = Manifest(attrs={"names": ""})
            _ = manifest.name

        with self.assertRaises(ValueError):
            manifest = Manifest()
            _ = manifest.name


if __name__ == '__main__':
    unittest.main()
