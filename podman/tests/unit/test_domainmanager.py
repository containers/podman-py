import unittest

import requests_mock

from podman import PodmanClient, tests


CONTAINER = {
    "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
    "Name": "quay.io/fedora:latest",
    "Image": "eloquent_pare",
    "State": {"Status": "running"},
}


class PodmanResourceTestCase(unittest.TestCase):
    """Test PodmanResource area of concern."""

    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    @requests_mock.Mocker()
    def test_reload_with_compatible_options(self, mock):
        """Test that reload uses the correct endpoint."""

        # Mock the get() call
        mock.get(
            f"{tests.LIBPOD_URL}/"
            f"containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=CONTAINER,
        )

        # Mock the reload() call
        mock.get(
            f"{tests.LIBPOD_URL}/"
            f"containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=CONTAINER,
        )

        # Mock the reload(compatible=False) call
        mock.get(
            f"{tests.LIBPOD_URL}/"
            f"containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=CONTAINER,
        )

        # Mock the reload(compatible=True) call
        mock.get(
            f"{tests.COMPATIBLE_URL}/"
            f"containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=CONTAINER,
        )

        container = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        container.reload()
        container.reload(compatible=False)
        container.reload(compatible=True)

        self.assertEqual(len(mock.request_history), 4)
        for i in range(3):
            self.assertEqual(
                mock.request_history[i].url,
                tests.LIBPOD_URL.lower()
                + "/containers/"
                + "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            )
        self.assertEqual(
            mock.request_history[3].url,
            tests.COMPATIBLE_URL.lower()
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
        )


if __name__ == '__main__':
    unittest.main()
