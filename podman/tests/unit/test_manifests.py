import unittest

import requests_mock

from podman import PodmanClient, tests
from podman.domain.manifests import Manifest, ManifestsManager

FIRST_MANIFEST = {
    "Id": "326dd9d7add24646a389e8eaa82125294027db2332e49c5828d96312c5d773ab",
    "names": "quay.io/fedora:latest",
}


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

    @requests_mock.Mocker()
    def test_push(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL + "/manifests/quay.io%2Ffedora%3Alatest/registry/quay.io%2Ffedora%3Av1"
        )

        manifest = Manifest(attrs=FIRST_MANIFEST, client=self.client.api)
        manifest.push(destination="quay.io/fedora:v1")

        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_push_with_auth(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/manifests/quay.io%2Ffedora%3Alatest/registry/quay.io%2Ffedora%3Av1",
            request_headers={
                "X-Registry-Auth": b"eyJ1c2VybmFtZSI6ICJ1c2VyIiwgInBhc3N3b3JkIjogInBhc3MifQ=="
            },
        )

        manifest = Manifest(attrs=FIRST_MANIFEST, client=self.client.api)
        manifest.push(
            destination="quay.io/fedora:v1", auth_config={"username": "user", "password": "pass"}
        )

        self.assertTrue(adapter.called_once)


if __name__ == '__main__':
    unittest.main()
