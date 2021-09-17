import unittest

import requests_mock

from podman import PodmanClient, tests


class SystemTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    @requests_mock.Mocker()
    def test_df(self, mock):
        body = {
            "Containers": [
                {"ContainerID": "f1fb3564c202"},
                {"ContainerID": "779afab684c7"},
            ],
            "Images": [
                {"ImageID": "118cc2c68ef5"},
                {"ImageID": "a6b4a8255f9e"},
            ],
            "Volumes": [
                {"VolumeName": "27df59163be8"},
                {"VolumeName": "77a83a10f86e"},
            ],
        }

        mock.get(
            tests.LIBPOD_URL + "/system/df",
            json=body,
        )

        actual = self.client.df()
        self.assertDictEqual(actual, body)

    @requests_mock.Mocker()
    def test_info(self, mock):
        body = {
            "host": {
                "arch": "amd65",
                "os": "linux",
            }
        }
        mock.get(tests.LIBPOD_URL + "/info", json=body)

        actual = self.client.info()
        self.assertDictEqual(actual, body)

    @requests_mock.Mocker()
    def test_ping(self, mock):
        mock.head(tests.LIBPOD_URL + "/_ping")
        self.assertTrue(self.client.ping())

    @requests_mock.Mocker()
    def test_version(self, mock):
        body = {
            "APIVersion": "3.0.0",
            "MinAPIVersion": "3.0.0",
            "Arch": "amd64",
            "Os": "linux",
        }
        mock.get(tests.LIBPOD_URL + "/version", json=body)
        self.assertDictEqual(self.client.version(), body)


if __name__ == '__main__':
    unittest.main()
