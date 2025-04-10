import unittest

import requests_mock

from podman import PodmanClient, tests
from podman.domain.pods import Pod
from podman.domain.pods_manager import PodsManager
from podman.errors import NotFound

FIRST_POD = {
    "ID": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
    "Name": "redis-ngnix",
}


class PodTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

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
            tests.LIBPOD_URL
            + "/pods/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/kill",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )

        pod = Pod(attrs=FIRST_POD, client=self.client.api)
        pod.kill()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_kill_404(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/pods/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/kill",
            status_code=404,
            json={
                "cause": "no such pod",
                "message": "no pod with name or ID xyz found: no such pod",
                "response": 404,
            },
        )

        pod = Pod(attrs=FIRST_POD, client=self.client.api)
        with self.assertRaises(NotFound):
            pod.kill()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_pause(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/pods/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/pause",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )

        pod = Pod(attrs=FIRST_POD, client=self.client.api)
        pod.pause()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_pause_404(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/pods/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/pause",
            status_code=404,
            json={
                "cause": "no such pod",
                "message": "no pod with name or ID xyz found: no such pod",
                "response": 404,
            },
        )

        pod = Pod(attrs=FIRST_POD, client=self.client.api)
        with self.assertRaises(NotFound):
            pod.pause()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_remove(self, mock):
        adapter = mock.delete(
            tests.LIBPOD_URL
            + "/pods/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8?force=True",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )
        pod_manager = PodsManager(client=self.client.api)
        pod = pod_manager.prepare_model(attrs=FIRST_POD)

        pod.remove(force=True)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_restart(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/pods/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/restart",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )

        pod = Pod(attrs=FIRST_POD, client=self.client.api)
        pod.restart()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_start(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/pods/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/start",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )

        pod = Pod(attrs=FIRST_POD, client=self.client.api)
        pod.start()
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_stop(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/pods/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/stop?t=70",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )

        pod = Pod(attrs=FIRST_POD, client=self.client.api)
        pod.stop(timeout=70)
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
            tests.LIBPOD_URL + "/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/top"
            "?ps_args=aux&stream=False",
            json=body,
        )

        pod = Pod(attrs=FIRST_POD, client=self.client.api)
        actual = pod.top(ps_args="aux")
        self.assertDictEqual(actual, body)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_unpause(self, mock):
        adapter = mock.post(
            tests.LIBPOD_URL
            + "/pods/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/unpause",
            json={
                "Errs": [],
                "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
            },
        )
        pod = Pod(attrs=FIRST_POD, client=self.client.api)
        pod.unpause()
        self.assertTrue(adapter.called_once)


if __name__ == '__main__':
    unittest.main()
