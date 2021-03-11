import base64
import io
import json
import unittest
from collections import Iterable

import requests_mock

from podman import PodmanClient
from podman.errors import APIError, NotFound

FIRST_CONTAINER = {
    "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
    "Image": "quay.io/fedora:latest",
    "Name": "evil_ptolemy",
}


class ContainersTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url="http+unix://localhost:9999")

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    @requests_mock.Mocker()
    def test_remove(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.delete(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd?v=True&force=True",
            status_code=204,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        container.remove(v=True, force=True)

    @requests_mock.Mocker()
    def test_rename(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/rename",
            status_code=204,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        container.rename("good_galileo")
        self.assertEqual(container.attrs["Name"], "good_galileo")

    @requests_mock.Mocker()
    def test_rename_409(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/rename",
            status_code=204,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        with self.assertRaises(ValueError):
            container.rename()

    @requests_mock.Mocker()
    def test_restart(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/restart?timeout=10",
            status_code=204,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        container.restart(timeout=10)

    @requests_mock.Mocker()
    def test_start_dkeys(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/start"
            "?detachKeys=%5Ef%5Eu",
            status_code=204,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        container.start(detach_keys="^f^u")

    @requests_mock.Mocker()
    def test_start(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/start",
            status_code=204,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        container.start()

    @requests_mock.Mocker()
    def test_stats(self, mock):
        stream = [
            {
                "Error": None,
                "Stats": [
                    {
                        "ContainerId": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                        "Name": "evil_ptolemy",
                        "CPU": 1000.0,
                    }
                ],
            }
        ]
        buffer = io.StringIO()
        for entry in stream:
            buffer.write(json.JSONEncoder().encode(entry))
            buffer.write("\n")

        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/stats"
            "?containers=87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
            "&stream=True",
            text=buffer.getvalue(),
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        stats = container.stats(decode=True)
        self.assertIsInstance(stats, Iterable)

        for entry in stats:
            self.assertIsInstance(entry, dict)
            for stat in entry["Stats"]:
                self.assertEqual(
                    stat["ContainerId"],
                    "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                )

    @requests_mock.Mocker()
    def test_stop(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/stop"
            "?all=True&timeout=10.0",
            status_code=204,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        container.stop(all=True, timeout=10.0)

    @requests_mock.Mocker()
    def test_stop_304(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/stop",
            json={
                "cause": "container already stopped",
                "message": "container already stopped",
                "response": 304,
            },
            status_code=304,
        )

        with self.assertRaises(APIError):
            container = self.client.containers.get(
                "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
            )
            container.stop()

    @requests_mock.Mocker()
    def test_unpause(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/unpause",
            status_code=204,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        container.unpause()

    @requests_mock.Mocker()
    def test_pause(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/pause",
            status_code=204,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        container.pause()

    @requests_mock.Mocker()
    def test_wait(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/wait",
            status_code=204,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        container.wait()

    @requests_mock.Mocker()
    def test_diff(self, mock):
        payload = [
            {"Path": "modified", "Kind": 0},
            {"Path": "added", "Kind": 1},
            {"Path": "deleted", "Kind": 2},
        ]

        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/changes",
            json=payload,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        actual = container.diff()
        self.assertListEqual(actual, payload)

    @requests_mock.Mocker()
    def test_diff_404(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/changes",
            json={
                "cause": "Container not found.",
                "message": "Container not found.",
                "response": 404,
            },
            status_code=404,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        with self.assertRaises(NotFound):
            container.diff()

    @requests_mock.Mocker()
    def test_export(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        tarball = b'Yet another weird tarball...'
        body = io.BytesIO(tarball)
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/export",
            body=body,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        with io.BytesIO() as fd:
            for chunk in container.export():
                fd.write(chunk)
            self.assertEqual(fd.getbuffer(), tarball)

    @requests_mock.Mocker()
    def test_get_archive(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        tarball = b'Yet another weird tarball...'
        body = io.BytesIO(tarball)

        header_value = {
            "name": "/etc/motd",
            "size": len(tarball),
            "mode": 0o444,
            "mtime": "20210309T12:49:0205:00",
        }
        encoded_value = base64.urlsafe_b64encode(json.dumps(header_value).encode("utf8"))

        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/archive"
            "?path=/etc/motd",
            body=body,
            headers={"x-docker-container-path-stat": encoded_value.decode("utf8")},
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        actual = container.get_archive("/etc/motd")
        self.assertEqual(len(actual), 2)

        self.assertEqual(actual[1]["name"], "/etc/motd")

        with io.BytesIO() as fd:
            for chunk in actual[0]:
                fd.write(chunk)
            self.assertEqual(fd.getbuffer(), tarball)

    @requests_mock.Mocker()
    def test_commit(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/commit"
            "?author=redhat&changes=ADD+%2Fetc%2Fmod&comment=This+is+a+unittest"
            "&container=87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd&format=docker"
            "&pause=True&repo=quay.local&tag=unittest",
            status_code=201,
            json={"ID": "d2459aad75354ddc9b5b23f863786e279637125af6ba4d4a83f881866b3c903f"},
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/images/"
            "d2459aad75354ddc9b5b23f863786e279637125af6ba4d4a83f881866b3c903f/json",
            json={"Id": "d2459aad75354ddc9b5b23f863786e279637125af6ba4d4a83f881866b3c903f"},
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        image = container.commit(
            repository="quay.local",
            tag="unittest",
            author="redhat",
            changes=["ADD /etc/mod"],
            comment="This is a unittest",
            format="docker",
            message="This is a unittest",
            pause=True,
        )
        self.assertEqual(
            image.id, "d2459aad75354ddc9b5b23f863786e279637125af6ba4d4a83f881866b3c903f"
        )

    @requests_mock.Mocker()
    def test_put_archive(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.put(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/archive"
            "?path=%2Fetc%2Fmotd",
            status_code=200,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        tarball = b'Yet another weird tarball...'
        body = io.BytesIO(tarball)
        actual = container.put_archive(path="/etc/motd", data=body.getvalue())
        self.assertTrue(actual)

    @requests_mock.Mocker()
    def test_put_archive_404(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )
        mock.put(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/archive"
            "?path=deadbeef",
            status_code=404,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

        tarball = b'Yet another weird tarball...'
        body = io.BytesIO(tarball)
        actual = container.put_archive(path="deadbeef", data=body.getvalue())
        self.assertFalse(actual)

    @requests_mock.Mocker()
    def test_top(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        body = {
            "Processes": [
                [
                    'jhonce',
                    '2417',
                    '2274',
                    '0',
                    'Mar01',
                    '?',
                    '00:00:01',
                    '/usr/bin/ssh-agent /bin/sh -c exec -l /bin/bash -c "/usr/bin/gnome-session"',
                ],
                ['jhonce', '5544', '3522', '0', 'Mar01', 'pts/1', '00:00:02', '-bash'],
                ['jhonce', '6140', '3522', '0', 'Mar01', 'pts/2', '00:00:00', '-bash'],
            ],
            "Titles": ["UID", "PID", "PPID", "C", "STIME", "TTY", "TIME CMD"],
        }
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/top",
            json=body,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        actual = container.top()
        self.assertDictEqual(actual, body)


if __name__ == '__main__':
    unittest.main()
