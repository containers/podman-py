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
        adapter = mock.delete(tests.LIBPOD_URL + "/volumes/dbase?force=True", status_code=204)
        vol_manager = VolumesManager(self.client.api)
        volume = vol_manager.prepare_model(attrs=FIRST_VOLUME)

        volume.remove(force=True)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_inspect(self, mock):
        mock.get(tests.LIBPOD_URL + "/volumes/dbase/json?tlsVerify=False", json=FIRST_VOLUME)
        vol_manager = VolumesManager(self.client.api)
        actual = vol_manager.prepare_model(attrs=FIRST_VOLUME)
        self.assertEqual(actual.inspect(tls_verify=False)["Mountpoint"], "/var/database")


if __name__ == '__main__':
    unittest.main()
