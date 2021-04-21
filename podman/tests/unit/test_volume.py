import unittest

import requests_mock

from podman import PodmanClient, tests
from podman.domain.volumes import Volume, VolumesManager

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

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_id(self):
        actual = Volume(attrs={"Name": "dbase"})
        self.assertEqual(actual.id, "dbase")

    @requests_mock.Mocker()
    def test_remove(self, mock):
        adapter = mock.delete(tests.BASE_URL + "/libpod/volumes/dbase?force=True", status_code=204)
        vol_manager = VolumesManager(self.client.api)
        volume = vol_manager.prepare_model(attrs=FIRST_VOLUME)

        volume.remove(force=True)
        self.assertTrue(adapter.called_once)


if __name__ == '__main__':
    unittest.main()
