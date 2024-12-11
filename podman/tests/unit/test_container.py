import base64
import io
import json
import unittest

try:
    # Python >= 3.10
    from collections.abc import Iterable
except ImportError:
    # Python < 3.10
    from collections.abc import Iterable

import requests_mock

from podman import PodmanClient, tests
from podman.domain.containers import Container
from podman.domain.containers_manager import ContainersManager
from podman.errors import APIError, NotFound

FIRST_CONTAINER = {
    "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
    "Image": "quay.io/fedora:latest",
    "Name": "evil_ptolemy",
}


class ContainersTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    @requests_mock.Mocker()
    def test_remove(self, mock):
        adapter = mock.delete(
            tests.LIBPOD_URL + "/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd?v=True&force=True",
            status_code=204,
        )
        manager = ContainersManager(self.client.api)
        container = manager.prepare_model(attrs=FIRST_CONTAINER)
        container.remove(v=True, force=True)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_rename(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/rename",
            status_code=204,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        container.rename("good_galileo")
        self.assertEqual(container.attrs["Name"], "good_galileo")
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_rename_type_error(self, mock):
        container = Container(
            attrs={"ID": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"}
        )
        with self.assertRaises(TypeError):
            container.rename()

    @requests_mock.Mocker()
    def test_restart(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL + "/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/restart?timeout=10",
            status_code=204,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        container.restart(timeout=10)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_start_dkeys(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL + "/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/start"
            "?detachKeys=%5Ef%5Eu",
            status_code=204,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        container.start(detach_keys="^f^u")
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_start(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/start",
            status_code=204,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        container.start()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_stats(self, mock):
        stream = [
            {
                "Error": None,
                "Stats": [
                    {
                        "ContainerId": (
                            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
                        ),
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

        adapter = mock.get(
            tests.LIBPOD_URL + "/containers/stats"
            "?containers=87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
            "&stream=True",
            text=buffer.getvalue(),
        )

        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        stats = container.stats(decode=True)
        self.assertIsInstance(stats, Iterable)

        for entry in stats:
            self.assertIsInstance(entry, dict)
            for stat in entry["Stats"]:
                self.assertEqual(
                    stat["ContainerId"],
                    "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                )
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_stop(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL + "/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/stop"
            "?all=True&timeout=10.0",
            status_code=204,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        container.stop(all=True, timeout=10.0)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_stop_304(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/stop",
            json={
                "cause": "container already stopped",
                "message": "container already stopped",
                "response": 304,
            },
            status_code=304,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        with self.assertRaises(APIError):
            container.stop()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_unpause(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL + "/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/unpause",
            status_code=204,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        container.unpause()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_pause(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/pause",
            status_code=204,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        container.pause()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_wait(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/wait",
            status_code=200,
            json={"StatusCode": 0},
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        container.wait()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_wait_condition_interval(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/wait",
            status_code=200,
            json={"StatusCode": 0},
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        container.wait(condition="exited", interval=1)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_diff(self, mock):
        payload = [
            {"Path": "modified", "Kind": 0},
            {"Path": "added", "Kind": 1},
            {"Path": "deleted", "Kind": 2},
        ]
        adapter = mock.get(
            tests.LIBPOD_URL + "/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/changes",
            json=payload,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        actual = container.diff()
        self.assertListEqual(actual, payload)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_diff_404(self, mock):
        adapter = mock.get(
            tests.LIBPOD_URL + "/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/changes",
            json={
                "cause": "Container not found.",
                "message": "Container not found.",
                "response": 404,
            },
            status_code=404,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        with self.assertRaises(NotFound):
            container.diff()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_export(self, mock):
        tarball = b'Yet another weird tarball...'
        body = io.BytesIO(tarball)
        adapter = mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/export",
            body=body,
        )

        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        with io.BytesIO() as fd:
            for chunk in container.export():
                fd.write(chunk)
            self.assertEqual(fd.getbuffer(), tarball)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_get_archive(self, mock):
        tarball = b'Yet another weird tarball...'
        body = io.BytesIO(tarball)

        header_value = {
            "name": "/etc/motd",
            "size": len(tarball),
            "mode": 0o444,
            "mtime": "20210309T12:49:0205:00",
        }
        encoded_value = base64.urlsafe_b64encode(json.dumps(header_value).encode("utf8"))

        adapter = mock.get(
            tests.LIBPOD_URL + "/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/archive"
            "?path=/etc/motd",
            body=body,
            headers={"x-docker-container-path-stat": encoded_value.decode("utf8")},
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        actual = container.get_archive("/etc/motd")
        self.assertEqual(len(actual), 2)

        self.assertEqual(actual[1]["name"], "/etc/motd")

        with io.BytesIO() as fd:
            for chunk in actual[0]:
                fd.write(chunk)
            self.assertEqual(fd.getbuffer(), tarball)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_commit(self, mock):
        post_adapter = mock.post(
            tests.LIBPOD_URL + "/commit"
            "?author=redhat&changes=ADD+%2fetc%2fmod&comment=This+is+a+unittest"
            "&container=87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd&format=docker"
            "&pause=True&repo=quay.local&tag=unittest",
            status_code=201,
            json={"Id": "d2459aad75354ddc9b5b23f863786e279637125af6ba4d4a83f881866b3c903f"},
        )
        get_adapter = mock.get(
            tests.LIBPOD_URL
            + "/images/d2459aad75354ddc9b5b23f863786e279637125af6ba4d4a83f881866b3c903f/json",
            json={"Id": "d2459aad75354ddc9b5b23f863786e279637125af6ba4d4a83f881866b3c903f"},
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)

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
        self.assertTrue(post_adapter.called_once)
        self.assertTrue(get_adapter.called_once)

    @requests_mock.Mocker()
    def test_put_archive(self, mock):
        adapter = mock.put(
            tests.LIBPOD_URL + "/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/archive"
            "?path=%2fetc%2fmotd",
            status_code=200,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)

        tarball = b'Yet another weird tarball...'
        body = io.BytesIO(tarball)
        actual = container.put_archive(path="/etc/motd", data=body.getvalue())
        self.assertTrue(actual)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_put_archive_404(self, mock):
        adapter = mock.put(
            tests.LIBPOD_URL + "/containers/"
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/archive"
            "?path=deadbeef",
            status_code=404,
            json={
                "cause": "Container not found.",
                "message": "Container not found.",
                "response": 404,
            },
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)

        tarball = b'Yet another weird tarball...'
        body = io.BytesIO(tarball)
        actual = container.put_archive(path="deadbeef", data=body.getvalue())
        self.assertFalse(actual)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_top(self, mock):
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
        adapter = mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/top",
            json=body,
        )
        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        actual = container.top()
        self.assertDictEqual(actual, body)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_top_with_streaming(self, mock):
        stream = [
            {
                "Processes": [
                    [
                        'jhonce',
                        '2417',
                        '2274',
                        '0',
                        'Mar01',
                        '?',
                        '00:00:01',
                        '/usr/bin/ssh-agent /bin/sh -c exec -l /bin/bash'
                        + '-c "/usr/bin/gnome-session"',
                    ],
                    ['jhonce', '5544', '3522', '0', 'Mar01', 'pts/1', '00:00:02', '-bash'],
                    ['jhonce', '6140', '3522', '0', 'Mar01', 'pts/2', '00:00:00', '-bash'],
                ],
                "Titles": ["UID", "PID", "PPID", "C", "STIME", "TTY", "TIME CMD"],
            }
        ]

        buffer = io.StringIO()
        for entry in stream:
            buffer.write(json.JSONEncoder().encode(entry))
            buffer.write("\n")

        adapter = mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/top"
            "?stream=True",
            text=buffer.getvalue(),
        )

        container = Container(attrs=FIRST_CONTAINER, client=self.client.api)
        top_stats = container.top(stream=True)

        self.assertIsInstance(top_stats, Iterable)
        for response, actual in zip(top_stats, stream):
            self.assertIsInstance(response, dict)
            self.assertDictEqual(response, actual)

        self.assertTrue(adapter.called_once)


if __name__ == '__main__':
    unittest.main()
