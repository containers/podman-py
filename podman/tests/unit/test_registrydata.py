import unittest
import urllib.parse

import requests_mock

from podman import PodmanClient, tests
from podman.domain.images_manager import ImagesManager
from podman.domain.registry_data import RegistryData
from podman.errors import APIError, InvalidArgument

FIRST_IMAGE = {
    "Id": "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
    "ParentId": "",
    "RepoTags": ["fedora:latest", "fedora:33", "<none>:<none>"],
    "RepoDigests": [
        "fedora@sha256:9598a10fa72b402db876ccd4b3d240a4061c7d1e442745f1896ba37e1bf38664"
    ],
    "Created": 1614033320,
    "Size": 23855104,
    "VirtualSize": 23855104,
    "SharedSize": 0,
    "Labels": {},
    "Containers": 2,
    "Os": "linux",
    "Architecture": "amd64",
}


MANIFEST_LIST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
    "manifests": [
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "size": 528,
            "digest": "sha256:69704ef328d05a9f806b6b8502915e6a0a4faa4d72018dc42343f511490edf8a",
            "platform": {
                "architecture": "amd64",
                "os": "linux",
            },
        },
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "size": 528,
            "digest": "sha256:2d16c52a0a2df992bb3b137456d95711c4e972ebff1c7a52c3c907a3465bbd69",
            "platform": {
                "architecture": "arm64",
                "os": "linux",
                "variant": "v8",
            },
        },
    ],
}


class RegistryDataTestCase(unittest.TestCase):
    """Test RegistryData.

    Note:
        Mock responses need to be coded for libpod returns.  The python bindings are responsible
            for mapping to compatible output.
    """

    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    @requests_mock.Mocker()
    def test_init(self, mock):
        mock.get(
            tests.LIBPOD_URL
            + "/images/326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab/json",
            json=FIRST_IMAGE,
        )
        actual = RegistryData(
            "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
            client=self.client.api,
            collection=ImagesManager(client=self.client.api),
        )
        self.assertEqual(
            actual.id, "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"
        )

    def test_platform(self):
        rd = RegistryData(
            "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
            attrs=FIRST_IMAGE,
            collection=ImagesManager(client=self.client.api),
        )
        self.assertTrue(rd.has_platform("linux/amd64/fedora"))

    def test_platform_dict(self):
        rd = RegistryData(
            "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
            attrs=FIRST_IMAGE,
            collection=ImagesManager(client=self.client.api),
        )

        self.assertTrue(rd.has_platform({"os": "linux", "architecture": "amd64"}))

    def test_platform_404(self):
        rd = RegistryData(
            "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
            attrs=FIRST_IMAGE,
            collection=ImagesManager(client=self.client.api),
        )

        self.assertFalse(rd.has_platform({"os": "COS", "architecture": "X-MP"}))

    def test_platform_409(self):
        rd = RegistryData(
            "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
            attrs=FIRST_IMAGE,
            collection=ImagesManager(client=self.client.api),
        )

        with self.assertRaises(InvalidArgument):
            rd.has_platform(list())

    def test_platform_500(self):
        rd = RegistryData(
            "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
            attrs=FIRST_IMAGE,
            collection=ImagesManager(client=self.client.api),
        )

        with self.assertRaises(InvalidArgument):
            rd.has_platform("This/is/not/a/legal/image/name")

    @requests_mock.Mocker()
    def test_manifest_list_id_and_short_id(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/version",
            json={"Os": "linux", "Arch": "arm64"},
        )
        rd = RegistryData(
            "quay.io/fedora:latest",
            attrs=MANIFEST_LIST,
            client=self.client.api,
            collection=ImagesManager(client=self.client.api),
        )
        self.assertEqual(
            rd.id, "sha256:2d16c52a0a2df992bb3b137456d95711c4e972ebff1c7a52c3c907a3465bbd69"
        )
        self.assertEqual(rd.short_id, "sha256:2d16c52a0a")

    def test_manifest_list_has_platform(self):
        rd = RegistryData(
            "quay.io/fedora:latest",
            attrs=MANIFEST_LIST,
            collection=ImagesManager(client=self.client.api),
        )
        self.assertTrue(rd.has_platform("linux/amd64"))
        self.assertTrue(rd.has_platform("linux/arm64"))
        self.assertTrue(rd.has_platform("linux/arm64/v8"))
        self.assertTrue(rd.has_platform({"os": "linux", "architecture": "arm64"}))
        self.assertFalse(rd.has_platform("windows/amd64"))
        self.assertFalse(rd.has_platform("linux/arm64/v7"))

    def test_distribution_data(self):
        dist_data = {
            "Descriptor": {
                "digest": (
                    "sha256:dist1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd"
                )
            },
            "Platforms": [
                {"os": "linux", "architecture": "amd64"},
            ],
        }
        rd = RegistryData(
            "quay.io/fedora:latest",
            attrs=dist_data,
            collection=ImagesManager(client=self.client.api),
        )
        self.assertEqual(
            rd.id, "sha256:dist1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd"
        )
        self.assertTrue(rd.has_platform("linux/amd64"))
        self.assertFalse(rd.has_platform("linux/arm64"))

    @requests_mock.Mocker()
    def test_pull_platform(self, mock):
        arm_digest = "sha256:2d16c52a0a2df992bb3b137456d95711c4e972ebff1c7a52c3c907a3465bbd69"
        pull_url = (
            tests.LIBPOD_URL
            + f"/images/pull?policy=always&reference=quay.io%2ffedora%40{arm_digest}"
            + "&tlsVerify=True&compatMode=True&OS=linux&Arch=arm64"
        )
        mock.post(
            pull_url,
            json={"id": arm_digest, "images": [arm_digest], "stream": "", "error": ""},
        )
        mock.get(
            tests.LIBPOD_URL + f"/images/{urllib.parse.quote_plus(arm_digest)}/json",
            json=FIRST_IMAGE,
        )
        rd = RegistryData(
            "quay.io/fedora:latest",
            attrs=MANIFEST_LIST,
            client=self.client.api,
            collection=ImagesManager(client=self.client.api),
        )
        image = rd.pull(platform="linux/arm64")
        self.assertIsNotNone(image)

    @requests_mock.Mocker()
    def test_reload(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/manifests/quay.io%2ffedora%3Alatest/json",
            json=MANIFEST_LIST,
        )
        rd = RegistryData(
            "quay.io/fedora:latest",
            attrs=FIRST_IMAGE,
            client=self.client.api,
            collection=ImagesManager(client=self.client.api),
        )
        rd.reload()
        self.assertEqual(rd.attrs["manifests"], MANIFEST_LIST["manifests"])

    @requests_mock.Mocker()
    def test_single_arch_without_digest(self, mock):
        # Podman returns a single-arch image as manifest list data without entries.
        # The config blob digest must not be used as the image reference.
        single_arch = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "manifests": None,
        }
        pull_adapter = mock.post(
            tests.LIBPOD_URL
            + "/images/pull?policy=always&reference=quay.io%2ffedora%3Alatest"
            + "&tlsVerify=True&compatMode=True",
            json={"id": FIRST_IMAGE["Id"], "images": [FIRST_IMAGE["Id"]], "stream": ""},
        )
        mock.get(tests.LIBPOD_URL + f"/images/{FIRST_IMAGE['Id']}/json", json=FIRST_IMAGE)
        rd = RegistryData(
            "quay.io/fedora:latest",
            attrs=single_arch,
            client=self.client.api,
            collection=ImagesManager(client=self.client.api),
        )
        self.assertIsNone(rd.id)
        self.assertIsNone(rd.short_id)

        rd.pull()
        self.assertTrue(pull_adapter.called_once)

    @requests_mock.Mocker()
    def test_manifest_list_id_version_error(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/version",
            status_code=500,
            json={"cause": "server error", "message": "server error"},
        )
        rd = RegistryData(
            "quay.io/fedora:latest",
            attrs=MANIFEST_LIST,
            client=self.client.api,
            collection=ImagesManager(client=self.client.api),
        )
        with self.assertRaises(APIError):
            _ = rd.id


if __name__ == '__main__':
    unittest.main()
