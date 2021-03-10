import unittest

import requests_mock

from podman import PodmanClient
from podman.domain.containers_manager import ContainersManager
from podman.errors import NotFound

FIRST_CONTAINER = {
    "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
    "Image": "quay.io/fedora:latest",
    "Name": "evil_ptolemy",
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

        self.client = PodmanClient(base_url="http+unix://localhost:9999")

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_podmanclient(self):
        manager = self.client.containers
        self.assertIsInstance(manager, ContainersManager)

    @requests_mock.Mocker()
    def test_get(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers"
            "/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
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
            "http+unix://localhost:9999/v3.0.0/libpod/containers"
            "/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
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
            "http+unix://localhost:9999/v3.0.0/libpod/containers/json",
            text="[]",
        )
        actual = self.client.containers.list()
        self.assertListEqual(actual, [])

    @requests_mock.Mocker()
    def test_list(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/containers/json",
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
            "http+unix://localhost:9999/v3.0.0/libpod/containers/json"
            "?all=True"
            "&filters=%7B%22status%22%3A+%5B%22running%22%5D%2C+"
            "%22before%22%3A+%5B%226dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03%22%5D%2C+"
            "%22since%22%3A+%5B%2287e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd%22%5D%7D",
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
            "http+unix://localhost:9999/v3.0.0/libpod/containers/json",
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
            "http+unix://localhost:9999/v3.0.0/libpod/containers/prune",
            json=[
                {
                    "id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                    "space": 1024,
                },
                {
                    "id": "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
                    "space": 1024,
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


if __name__ == '__main__':
    unittest.main()
