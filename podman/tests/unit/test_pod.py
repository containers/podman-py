import unittest

import requests_mock

from podman import PodmanClient
from podman.domain.pods import Pod
from podman.errors import NotFound

FIRST_POD = {
    "ID": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
    "Name": "redis-ngnix",
}


class PodTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url="http+unix://localhost:9999")

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_id(self):
        expected = {"Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"}
        actual = Pod(attrs=expected)
        self.assertEqual(actual.id, expected["Id"])

        expected = {"Name": "redis-ngnix"}
        actual = Pod(attrs=expected)
        self.assertEqual(actual.name, expected["Name"])

    @requests_mock.Mocker()
    def test_kill(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/kill",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )
        pod = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        pod.kill()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_kill_404(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/kill",
            status_code=404,
            json={
                "cause": "no such pod",
                "message": "no pod with name or ID xyz found: no such pod",
                "response": 404,
            },
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )
        pod = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        with self.assertRaises(NotFound):
            pod.kill()

    @requests_mock.Mocker()
    def test_pause(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/pause",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )
        pod = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        pod.pause()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_pause_404(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/pause",
            status_code=404,
            json={
                "cause": "no such pod",
                "message": "no pod with name or ID xyz found: no such pod",
                "response": 404,
            },
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )
        pod = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        with self.assertRaises(NotFound):
            pod.pause()

    @requests_mock.Mocker()
    def test_remove(self, mock):
        adapter = mock.delete(
            "http+unix://localhost:9999/v3.0.0/libpod/pods/"
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8?force=True",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )
        pod = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        pod.remove(force=True)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_restart(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/restart",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )
        pod = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        pod.restart()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_start(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/start",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )
        pod = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        pod.start()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_stop(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/stop?t=70.0",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )
        pod = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        pod.stop(timeout=70.0)
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
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/top"
            "?ps_args=aux&stream=False",
            json=body,
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )
        pod = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        actual = pod.top(ps_args="aux")
        self.assertTrue(adapter.called_once)
        self.assertDictEqual(actual, body)

    @requests_mock.Mocker()
    def test_unpause(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/unpause",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )
        pod = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        pod.unpause()
        self.assertTrue(adapter.called_once)


if __name__ == '__main__':
    unittest.main()
