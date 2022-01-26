import unittest

import requests
import requests_mock

from podman import PodmanClient, tests
from podman.domain.volumes import Volume, VolumesManager
from podman.errors import NotFound

FIRST_VOLUME = {
    "CreatedAt": "1985-04-12T23:20:50.52Z",
    "Driver": "default",
    "Labels": {"BackupRequired": True},
    "Mountpoint": "/var/database",
    "Name": "dbase",
    "Scope": "local",
}

SECOND_VOLUME = {
    "CreatedAt": "1996-12-19T16:39:57-08:00",
    "Driver": "default",
    "Labels": {"BackupRequired": False},
    "Mountpoint": "/var/source",
    "Name": "source",
    "Scope": "local",
}


class VolumesManagerTestCase(unittest.TestCase):
    """Test VolumesManager area of concern.

    Note:
        Mock responses need to be coded for libpod returns.  The python bindings are responsible
            for mapping to compatible output.
    """

    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)
        self.addCleanup(self.client.close)

    def test_podmanclient(self):
        manager = self.client.volumes
        self.assertIsInstance(manager, VolumesManager)

    @requests_mock.Mocker()
    def test_create(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL + "/volumes/create",
            json=FIRST_VOLUME,
            status_code=requests.codes.created,
        )

        actual = self.client.volumes.create(
            "dbase",
            labels={
                "BackupRequired": True,
            },
        )
        self.assertIsInstance(actual, Volume)
        self.assertTrue(adapter.called_once)
        self.assertDictEqual(
            adapter.last_request.json(),
            {
                "Name": "dbase",
                "Labels": {
                    "BackupRequired": True,
                },
            },
        )
        self.assertEqual(actual.id, "dbase")
        self.assertDictEqual(
            actual.attrs["Labels"],
            {
                "BackupRequired": True,
            },
        )

    @requests_mock.Mocker()
    def test_get(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/volumes/dbase/json",
            json=FIRST_VOLUME,
        )

        actual = self.client.volumes.get("dbase")
        self.assertIsInstance(actual, Volume)
        self.assertDictEqual(actual.attrs, FIRST_VOLUME)
        self.assertEqual(actual.id, actual.name)

    @requests_mock.Mocker()
    def test_get_404(self, mock):
        adapter = mock.get(
            tests.LIBPOD_URL + "/volumes/dbase/json",
            text="Not Found",
            status_code=404,
        )

        with self.assertRaises(NotFound):
            self.client.volumes.get("dbase")
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_list(self, mock):
        mock.get(tests.LIBPOD_URL + "/volumes/json", json=[FIRST_VOLUME, SECOND_VOLUME])

        actual = self.client.volumes.list(filters={"driver": "local"})
        self.assertEqual(len(actual), 2)

        self.assertIsInstance(actual[0], Volume)
        self.assertEqual(actual[0].name, "dbase")

        self.assertIsInstance(actual[1], Volume)
        self.assertEqual(actual[1].id, "source")

    @requests_mock.Mocker()
    def test_list_404(self, mock):
        mock.get(tests.LIBPOD_URL + "/volumes/json", text="Not Found", status_code=404)

        actual = self.client.volumes.list()
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), 0)

    @requests_mock.Mocker()
    def test_prune(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/volumes/prune",
            json=[
                {"Id": "dbase", "Size": 1024},
                {"Id": "source", "Size": 1024},
            ],
        )

        actual = self.client.volumes.prune()
        self.assertDictEqual(
            actual, {"VolumesDeleted": ["dbase", "source"], "SpaceReclaimed": 2048}
        )


if __name__ == '__main__':
    unittest.main()
