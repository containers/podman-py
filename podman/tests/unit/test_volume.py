import unittest

import requests_mock

from podman import PodmanClient
from podman.domain.volumes import Volume

FIRST_VOLUME = {
    "CreatedAt": "1985-04-12T23:20:50.52Z",
    "Driver": "default",
    "Labels": {"BackupRequired": True},
    "Mountpoint": "/var/database",
    "Name": "dbase",
    "Scope": "local",
}


class VolumeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url="http+unix://localhost:9999")

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_id(self):
        actual = Volume(attrs={"Name": "dbase"})
        self.assertEqual(actual.id, "dbase")

    @requests_mock.Mocker()
    def test_remove(self, mock):
        adapter = mock.delete(
            "http+unix://localhost:9999/v3.0.0/libpod/volumes/dbase?force=True", status_code=204
        )

        mock.get("http+unix://localhost:9999/v3.0.0/libpod/volumes/dbase", json=FIRST_VOLUME)
        volume = self.client.volumes.get("dbase")

        volume.remove(force=True)
        self.assertTrue(adapter.called_once)


if __name__ == '__main__':
    unittest.main()
