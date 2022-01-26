import unittest

try:
    # Python >= 3.10
    from collections.abc import Iterator
except:
    # Python < 3.10
    from collections import Iterator
from unittest.mock import patch, DEFAULT

import requests_mock

from podman import PodmanClient, tests
from podman.domain.containers import Container
from podman.domain.containers_manager import ContainersManager
from podman.errors import NotFound, ImageNotFound

FIRST_CONTAINER = {
    "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
    "Image": "quay.io/fedora:latest",
    "Name": "evil_ptolemy",
    "HostConfig": {"LogConfig": {"Type": "json-file"}},
}
SECOND_CONTAINER = {
    "Id": "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
    "Image": "quay.io/fedora:rc",
    "Name": "good_galileo",
}


class ContainersManagerTestCase(unittest.TestCase):
    """Test ContainersManager area of concern.

    Note:
        Mock responses need to be coded for libpod returns.  The python bindings are responsible
            for mapping to compatible output.
    """

    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_podmanclient(self):
        manager = self.client.containers
        self.assertIsInstance(manager, ContainersManager)

    @requests_mock.Mocker()
    def test_get(self, mock):
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        actual = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        self.assertEqual(
            actual.id, "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )

    @requests_mock.Mocker()
    def test_get_404(self, mock):
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json={
                "cause": "Container not found.",
                "message": "Container not found.",
                "response": 404,
            },
            status_code=404,
        )

        with self.assertRaises(NotFound):
            self.client.containers.get(
                "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
            )

    @requests_mock.Mocker()
    def test_list_empty(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/containers/json",
            text="[]",
        )
        actual = self.client.containers.list()
        self.assertListEqual(actual, [])

    @requests_mock.Mocker()
    def test_list(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/containers/json",
            json=[FIRST_CONTAINER, SECOND_CONTAINER],
        )
        actual = self.client.containers.list()
        self.assertIsInstance(actual, list)

        self.assertEqual(
            actual[0].id, "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        self.assertEqual(
            actual[1].id, "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03"
        )

    @requests_mock.Mocker()
    def test_list_filtered(self, mock):
        mock.get(
            tests.LIBPOD_URL
            + "/containers/json?"
            "all=True"
            "&filters=%7B"
            "%22before%22%3A"
            "+%5B%226dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03%22%5D%2C"
            "+%22since%22%3A"
            "+%5B%2287e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd%22%5D%2C"
            "+%22status%22%3A+%5B%22running%22%5D%7D",
            json=[FIRST_CONTAINER, SECOND_CONTAINER],
        )
        actual = self.client.containers.list(
            all=True,
            filters={"status": "running"},
            since="87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            before="6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
        )
        self.assertIsInstance(actual, list)

        self.assertEqual(
            actual[0].id, "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        self.assertEqual(
            actual[1].id, "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03"
        )

    @requests_mock.Mocker()
    def test_list_no_filters(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/containers/json",
            json=[FIRST_CONTAINER, SECOND_CONTAINER],
        )
        actual = self.client.containers.list()
        self.assertIsInstance(actual, list)

        self.assertEqual(
            actual[0].id, "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        self.assertEqual(
            actual[1].id, "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03"
        )

    @requests_mock.Mocker()
    def test_prune(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/containers/prune",
            json=[
                {
                    "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                    "Size": 1024,
                },
                {
                    "Id": "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
                    "Size": 1024,
                },
            ],
        )
        actual = self.client.containers.prune()
        self.assertDictEqual(
            actual,
            {
                "ContainersDeleted": [
                    "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                    "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
                ],
                "SpaceReclaimed": 2048,
            },
        )

    @requests_mock.Mocker()
    def test_create(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/containers/create",
            status_code=201,
            json={
                "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                "Warnings": [],
            },
        )
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        actual = self.client.containers.create("fedora", "/usr/bin/ls", cpu_count=9999)
        self.assertIsInstance(actual, Container)

    @requests_mock.Mocker()
    def test_create_404(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/containers/create",
            status_code=404,
            json={
                "cause": "Image not found",
                "message": "Image not found",
                "response": 404,
            },
        )
        with self.assertRaises(ImageNotFound):
            self.client.containers.create("fedora", "/usr/bin/ls", cpu_count=9999)

    def test_create_unsupported_key(self):
        with self.assertRaises(TypeError) as e:
            self.client.containers.create("fedora", "/usr/bin/ls", blkio_weight=100.0)

    def test_create_unknown_key(self):
        with self.assertRaises(TypeError) as e:
            self.client.containers.create("fedora", "/usr/bin/ls", unknown_key=100.0)

    @requests_mock.Mocker()
    def test_run_detached(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/containers/create",
            status_code=201,
            json={
                "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                "Warnings": [],
            },
        )
        mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/start",
            status_code=204,
        )
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        with patch.multiple(Container, logs=DEFAULT, wait=DEFAULT, autospec=True) as mock_container:
            mock_container["logs"].return_value = []
            mock_container["wait"].return_value = {"StatusCode": 0}

            actual = self.client.containers.run("fedora", "/usr/bin/ls", detach=True)
            self.assertIsInstance(actual, Container)

    @requests_mock.Mocker()
    def test_run(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/containers/create",
            status_code=201,
            json={
                "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                "Warnings": [],
            },
        )
        mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/start",
            status_code=204,
        )
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        mock_logs = (
            b"This is a unittest - line 1",
            b"This is a unittest - line 2",
        )

        with patch.multiple(Container, logs=DEFAULT, wait=DEFAULT, autospec=True) as mock_container:
            mock_container["wait"].return_value = {"StatusCode": 0}

            with self.subTest("Results not streamed"):
                mock_container["logs"].return_value = iter(mock_logs)

                actual = self.client.containers.run("fedora", "/usr/bin/ls")
                self.assertIsInstance(actual, bytes)
                self.assertEqual(actual, b'This is a unittest - line 1This is a unittest - line 2')

            # iter() cannot be reset so subtests used to create new instance
            with self.subTest("Stream results"):
                mock_container["logs"].return_value = iter(mock_logs)

                actual = self.client.containers.run("fedora", "/usr/bin/ls", stream=True)
                self.assertNotIsInstance(actual, bytes)
                self.assertIsInstance(actual, Iterator)
                self.assertEqual(next(actual), b"This is a unittest - line 1")
                self.assertEqual(next(actual), b"This is a unittest - line 2")


if __name__ == '__main__':
    unittest.main()
