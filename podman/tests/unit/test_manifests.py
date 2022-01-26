import unittest

from podman import PodmanClient, tests
from podman.domain.manifests import Manifest, ManifestsManager


class ManifestTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)
        self.addCleanup(self.client.close)

    def test_podmanclient(self):
        manager = self.client.manifests
        self.assertIsInstance(manager, ManifestsManager)

    def test_list(self):
        with self.assertRaises(NotImplementedError):
            self.client.manifests.list()

    def test_name(self):
        manifest = Manifest()
        self.assertIsNone(manifest.name)


if __name__ == '__main__':
    unittest.main()
