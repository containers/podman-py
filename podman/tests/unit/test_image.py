import io
import unittest

import requests_mock

from podman import PodmanClient, tests
from podman.domain.images import Image

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
}

SECOND_IMAGE = {
    "Id": "c4b16966ecd94ffa910eab4e630e24f259bf34a87e924cd4b1434f267b0e354e",
    "ParentId": "",
    "RepoDigests": [
        "fedora@sha256:4a877de302c6463cb624ddfe146ad850413724462ec24847832aa6eb1e957746"
    ],
    "Created": 1614033320,
    "Size": 23855104,
    "VirtualSize": 23855104,
    "SharedSize": 0,
    "Containers": 0,
}


class ImageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    @requests_mock.Mocker()
    def test_history(self, mock):
        adapter = mock.get(
            tests.LIBPOD_URL
            + "/images/326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab/history",
            json=[
                {
                    "Id": "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
                    "Comment": "",
                    "Created": 1614208404,
                    "CreatedBy": "2021-02-24T23:13:24+00:00",
                    "Tags": ["latest"],
                    "Size": 1024,
                }
            ],
        )
        image = Image(attrs=FIRST_IMAGE, client=self.client.api)

        history = image.history()
        self.assertEqual(history[0]["Id"], image.id)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_reload(self, mock):
        update = FIRST_IMAGE.copy()
        update["Containers"] = 0

        adapter = mock.get(
            tests.LIBPOD_URL
            + "/images/326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab/json",
            [
                {"json": FIRST_IMAGE},
                {"json": update},
            ],
        )

        image = self.client.images.get(
            "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"
        )
        self.assertEqual(image.attrs["Containers"], 2)

        image.reload()
        self.assertEqual(image.attrs["Containers"], 0)
        self.assertTrue(adapter.call_count, 2)

    @requests_mock.Mocker()
    def test_save(self, mock):
        tarball = b'Yet another weird tarball...'
        body = io.BytesIO(tarball)

        adapter = mock.get(
            tests.LIBPOD_URL
            + "/images/326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab/get",
            body=body,
        )
        image = Image(attrs=FIRST_IMAGE, client=self.client.api)

        with io.BytesIO() as fd:
            for chunk in image.save():
                fd.write(chunk)
            self.assertEqual(fd.getbuffer(), tarball)
        self.assertTrue(adapter.called_once)


if __name__ == '__main__':
    unittest.main()
