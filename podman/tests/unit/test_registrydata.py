import unittest

import requests_mock

from podman import PodmanClient, tests
from podman.domain.images_manager import ImagesManager
from podman.domain.registry_data import RegistryData
from podman.errors import InvalidArgument

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


if __name__ == '__main__':
    unittest.main()
