import types
import unittest
from unittest.mock import patch

try:
    # Python >= 3.10
    from collections.abc import Iterable
except ImportError:
    # Python < 3.10
    from collections.abc import Iterable

import requests_mock

from podman import PodmanClient, tests
from podman.domain.images import Image
from podman.domain.images_manager import ImagesManager
from podman.errors import APIError, ImageNotFound, PodmanError

FIRST_IMAGE = {
    "Id": "sha256:326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
    "ParentId": "",
    "RepoTags": ["fedora:latest", "fedora:33", "<none>:<none>"],
    "RepoDigests": [
        "fedora@sha256:9598a10fa72b402db876ccd4b3d240a4061c7d1e442745f1896ba37e1bf38664"
    ],
    "Created": 1614033320,
    "Size": 23855104,
    "VirtualSize": 23855104,
    "SharedSize": 0,
    "Labels": {"license": " Apache-2.0"},
    "Containers": 2,
}

SECOND_IMAGE = {
    "Id": "c4b16966ecd94ffa910eab4e630e24f259bf34a87e924cd4b1434f267b0e354e",
    "ParentId": "",
    "RepoDigests": [
        "fedora@sha256:4a877de302c6463cb624ddfe146ad850413724462ec24847832aa6eb1e957746"
    ],
    "Created": 1614033320,
    "Size": 23855104,
    "VirtualSize": 23855104,
    "SharedSize": 0,
    "Containers": 0,
}


class ImagesManagerTestCase(unittest.TestCase):
    """Test ImagesManager area of concern.

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
        manager = self.client.images
        self.assertIsInstance(manager, ImagesManager)

    @requests_mock.Mocker()
    def test_list_empty(self, mock):
        """Unit test Images list()."""
        mock.get(
            tests.LIBPOD_URL + "/images/json",
            text="[]",
        )

        images = self.client.images.list()
        self.assertEqual(len(images), 0)

    @requests_mock.Mocker()
    def test_list_1(self, mock):
        """Unit test Images list()."""
        mock.get(
            tests.LIBPOD_URL + "/images/json",
            json=[FIRST_IMAGE],
        )

        images = self.client.images.list()
        self.assertEqual(len(images), 1)

        self.assertIsInstance(images[0], Image)

        self.assertEqual(str(images[0]), "<Image: 'fedora:latest', 'fedora:33'>")

        self.assertEqual(
            images[0].id, "sha256:326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"
        )

        self.assertIsInstance(images[0].labels, dict)
        self.assertEqual(len(images[0].labels), 1)

        self.assertEqual(images[0].short_id, "sha256:326dd9d7ad")

        self.assertIsInstance(images[0].tags, list)
        self.assertEqual(len(images[0].tags), 2)

    @requests_mock.Mocker()
    def test_list_2(self, mock):
        """Unit test Images list()."""
        mock.get(
            tests.LIBPOD_URL + "/images/json",
            json=[FIRST_IMAGE, SECOND_IMAGE],
        )

        images = self.client.images.list()
        self.assertEqual(len(images), 2)

        self.assertIsInstance(images[0], Image)
        self.assertIsInstance(images[1], Image)

        self.assertEqual(images[1].short_id, "c4b16966ec")
        self.assertIsInstance(images[1].labels, dict)
        self.assertEqual(len(images[1].labels), 0)

        self.assertIsInstance(images[1].tags, list)
        self.assertEqual(len(images[1].tags), 0)

    @requests_mock.Mocker()
    def test_list_filters(self, mock):
        """Unit test filters param for Images list()."""
        mock.get(
            tests.LIBPOD_URL + "/images/json?filters=%7B%22dangling%22%3A+%5B%22True%22%5D%7D",
            json=[FIRST_IMAGE],
        )

        images = self.client.images.list(filters={"dangling": True})
        self.assertEqual(
            images[0].id, "sha256:326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"
        )

    @requests_mock.Mocker()
    def test_list_all(self, mock):
        """Unit test filters param for Images list()."""
        mock.get(
            tests.LIBPOD_URL + "/images/json?all=true",
            json=[FIRST_IMAGE],
        )

        images = self.client.images.list(all=True)
        self.assertEqual(
            images[0].id, "sha256:326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"
        )

    @requests_mock.Mocker()
    def test_prune(self, mock):
        """Unit test Images prune()."""
        mock.post(
            tests.LIBPOD_URL + "/images/prune",
            json=[
                {
                    "Id": "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
                    "Err": None,
                    "Size": 1024,
                }
            ],
        )

        results = self.client.images.prune()
        self.assertIn("ImagesDeleted", results)
        self.assertIn("SpaceReclaimed", results)

        self.assertEqual(
            results["ImagesDeleted"][0]["Deleted"],
            "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
        )
        self.assertEqual(results["SpaceReclaimed"], 1024)

    @requests_mock.Mocker()
    def test_prune_filters(self, mock):
        """Unit test filters param for Images prune()."""
        mock.post(
            tests.LIBPOD_URL + "/images/prune?filters=%7B%22dangling%22%3A+%5B%22True%22%5D%7D",
            json=[
                {
                    "Id": "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
                    "Size": 1024,
                },
                {
                    "Id": "c4b16966ecd94ffa910eab4e630e24f259bf34a87e924cd4b1434f267b0e354e",
                    "Size": 1024,
                },
            ],
        )

        report = self.client.images.prune(filters={"dangling": True})
        self.assertIn("ImagesDeleted", report)
        self.assertIn("SpaceReclaimed", report)

        self.assertEqual(report["SpaceReclaimed"], 2048)

        deleted = [r["Deleted"] for r in report["ImagesDeleted"] if "Deleted" in r]
        self.assertEqual(len(deleted), 2)
        self.assertIn("326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab", deleted)
        self.assertGreater(len("".join(deleted)), 0)

        untagged = [r["Untagged"] for r in report["ImagesDeleted"] if "Untagged" in r]
        self.assertEqual(len(untagged), 2)
        self.assertEqual(len("".join(untagged)), 0)

    @requests_mock.Mocker()
    def test_prune_filters_label(self, mock):
        """Unit test filters param label for Images prune()."""
        mock.post(
            tests.LIBPOD_URL
            + "/images/prune?filters=%7B%22label%22%3A+%5B%22%7B%27license%27%3A+"
            + "%27Apache-2.0%27%7D%22%5D%7D",
            json=[
                {
                    "Id": "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
                    "Size": 1024,
                },
            ],
        )

        report = self.client.images.prune(filters={"label": {"license": "Apache-2.0"}})
        self.assertIn("ImagesDeleted", report)
        self.assertIn("SpaceReclaimed", report)

        self.assertEqual(report["SpaceReclaimed"], 1024)

        deleted = [r["Deleted"] for r in report["ImagesDeleted"] if "Deleted" in r]
        self.assertEqual(len(deleted), 1)
        self.assertIn("326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab", deleted)
        self.assertGreater(len("".join(deleted)), 0)

        untagged = [r["Untagged"] for r in report["ImagesDeleted"] if "Untagged" in r]
        self.assertEqual(len(untagged), 1)
        self.assertEqual(len("".join(untagged)), 0)

    @requests_mock.Mocker()
    def test_prune_filters_not_label(self, mock):
        """Unit test filters param NOT-label for Images prune()."""
        mock.post(
            tests.LIBPOD_URL
            + "/images/prune?filters=%7B%22label%21%22%3A+%5B%22%7B%27license%27%3A+"
            + "%27Apache-2.0%27%7D%22%5D%7D",
            json=[
                {
                    "Id": "c4b16966ecd94ffa910eab4e630e24f259bf34a87e924cd4b1434f267b0e354e",
                    "Size": 1024,
                },
            ],
        )

        report = self.client.images.prune(filters={"label!": {"license": "Apache-2.0"}})
        self.assertIn("ImagesDeleted", report)
        self.assertIn("SpaceReclaimed", report)

        self.assertEqual(report["SpaceReclaimed"], 1024)

        deleted = [r["Deleted"] for r in report["ImagesDeleted"] if "Deleted" in r]
        self.assertEqual(len(deleted), 1)
        self.assertIn("c4b16966ecd94ffa910eab4e630e24f259bf34a87e924cd4b1434f267b0e354e", deleted)
        self.assertGreater(len("".join(deleted)), 0)

        untagged = [r["Untagged"] for r in report["ImagesDeleted"] if "Untagged" in r]
        self.assertEqual(len(untagged), 1)
        self.assertEqual(len("".join(untagged)), 0)

    @requests_mock.Mocker()
    def test_prune_failure(self, mock):
        """Unit test to report error carried in response body."""
        mock.post(
            tests.LIBPOD_URL + "/images/prune",
            json=[
                {
                    "Err": "Test prune failure in response body.",
                }
            ],
        )

        with self.assertRaises(APIError) as e:
            self.client.images.prune()
        self.assertEqual(e.exception.explanation, "Test prune failure in response body.")

    @requests_mock.Mocker()
    def test_prune_empty(self, mock):
        """Unit test if prune API responses null (None)."""
        mock.post(tests.LIBPOD_URL + "/images/prune", text="null")

        report = self.client.images.prune()
        self.assertEqual(report["ImagesDeleted"], [])
        self.assertEqual(report["SpaceReclaimed"], 0)

    @requests_mock.Mocker()
    def test_get(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/images/fedora%3Alatest/json",
            json=FIRST_IMAGE,
        )

        image = self.client.images.get("fedora:latest")
        self.assertIsInstance(image, Image)
        self.assertDictEqual(FIRST_IMAGE["Labels"], image.attrs["Labels"])

    @requests_mock.Mocker()
    def test_get_oserror(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/images/bad_image/json",
            exc=OSError,
        )

        with self.assertRaises(APIError) as e:
            _ = self.client.images.get("bad_image")
        self.assertEqual(
            str(e.exception),
            tests.LIBPOD_URL + "/images/bad_image/json (GET operation failed)",
        )

    @requests_mock.Mocker()
    def test_get_404(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/images/bad_image/json",
            status_code=404,
            json={
                "cause": "Image not found",
                "message": "Image not found",
                "response": 404,
            },
        )

        with self.assertRaises(ImageNotFound):
            _ = self.client.images.get("bad_image")

    @requests_mock.Mocker()
    def test_get_500(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/images/bad_image/json",
            status_code=500,
            json={
                "cause": "Server error",
                "message": "Server error",
                "response": 500,
            },
        )

        with self.assertRaises(APIError):
            _ = self.client.images.get("bad_image")

    @requests_mock.Mocker()
    def test_remove(self, mock):
        mock.delete(
            tests.LIBPOD_URL + "/images/fedora:latest",
            json={
                "Untagged": ["326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"],
                "Deleted": [
                    "326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
                    "c4b16966ecd94ffa910eab4e630e24f259bf34a87e924cd4b1434f267b0e354e",
                ],
                "Errors": [],
                "ExitCode": 0,
            },
        )

        report = self.client.images.remove("fedora:latest")
        self.assertEqual(len(report), 4)

        deleted = [r["Deleted"] for r in report if "Deleted" in r]
        self.assertEqual(len(deleted), 2)

        untagged = [r["Untagged"] for r in report if "Untagged" in r]
        self.assertEqual(len(untagged), 1)

        errors = [r["Errors"] for r in report if "Errors" in r]
        self.assertEqual(len(errors), 0)

        codes = [r["ExitCode"] for r in report if "ExitCode" in r]
        self.assertEqual(len(codes), 1)
        self.assertEqual(codes[0], 0)

    @requests_mock.Mocker()
    def test_load(self, mock):
        with self.assertRaises(PodmanError):
            self.client.images.load()

        with self.assertRaises(PodmanError):
            self.client.images.load(b'data', b'file_path')

        with self.assertRaises(PodmanError):
            self.client.images.load(data=b'data', file_path=b'file_path')

        # Patch Path.read_bytes to mock the file reading behavior
        with patch("pathlib.Path.read_bytes", return_value=b"mock tarball data"):
            mock.post(
                tests.LIBPOD_URL + "/images/load",
                json={"Names": ["quay.io/fedora:latest"]},
            )
            mock.get(
                tests.LIBPOD_URL + "/images/quay.io%2ffedora%3Alatest/json",
                json=FIRST_IMAGE,
            )

            # 3a. Test the case where only 'file_path' is provided
            gntr = self.client.images.load(file_path="mock_file.tar")
            self.assertIsInstance(gntr, types.GeneratorType)

            report = list(gntr)
            self.assertEqual(len(report), 1)
            self.assertEqual(
                report[0].id,
                "sha256:326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab",
            )

        mock.post(
            tests.LIBPOD_URL + "/images/load",
            json={"Names": ["quay.io/fedora:latest"]},
        )
        mock.get(
            tests.LIBPOD_URL + "/images/quay.io%2ffedora%3Alatest/json",
            json=FIRST_IMAGE,
        )

        gntr = self.client.images.load(b'This is a weird tarball...')
        self.assertIsInstance(gntr, types.GeneratorType)

        report = list(gntr)
        self.assertEqual(len(report), 1)
        self.assertEqual(
            report[0].id, "sha256:326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"
        )

    @requests_mock.Mocker()
    def test_search(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/images/search?term=fedora&noTrunc=true",
            json=[
                {
                    "description": "mock term=fedora search",
                    "is_official": False,
                    "is_automated": False,
                    "name": "quay.io/libpod/fedora",
                    "star_count": 0,
                },
            ],
        )

        report = self.client.images.search("fedora")
        self.assertEqual(len(report), 1)

        self.assertEqual(report[0]["name"], "quay.io/libpod/fedora")

    @requests_mock.Mocker()
    def test_search_oserror(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/images/search?term=fedora&noTrunc=true",
            exc=OSError,
        )

        with self.assertRaises(OSError):
            self.client.images.search("fedora")

    @requests_mock.Mocker()
    def test_search_500(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/images/search?term=fedora&noTrunc=true",
            status_code=500,
            json={
                "cause": "Server error",
                "message": "Server error",
                "response": 500,
            },
        )

        with self.assertRaises(OSError):
            self.client.images.search("fedora")

    @requests_mock.Mocker()
    def test_search_limit(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/images/search?term=fedora&noTrunc=true&limit=5",
            json=[
                {
                    "description": "mock term=fedora search",
                    "is_official": False,
                    "is_automated": False,
                    "name": "quay.io/libpod/fedora",
                    "star_count": 0,
                },
            ],
        )

        report = self.client.images.search("fedora", limit=5)
        self.assertEqual(len(report), 1)

        self.assertEqual(report[0]["name"], "quay.io/libpod/fedora")

    @requests_mock.Mocker()
    def test_search_filters(self, mock):
        mock.get(
            tests.LIBPOD_URL
            + "/images/search?filters=%7B%22stars%22%3A+%5B%225%22%5D%7D&noTrunc=True&term=fedora",
            json=[
                {
                    "description": "mock term=fedora search",
                    "is_official": False,
                    "is_automated": False,
                    "name": "quay.io/libpod/fedora",
                    "star_count": 0,
                },
            ],
        )

        report = self.client.images.search("fedora", filters={"stars": 5})
        self.assertEqual(len(report), 1)

        self.assertEqual(report[0]["name"], "quay.io/libpod/fedora")

    @requests_mock.Mocker()
    def test_search_listTags(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/images/search?term=fedora&noTrunc=true&listTags=true",
            json=[
                {
                    "description": "mock term=fedora search",
                    "is_official": False,
                    "is_automated": False,
                    "name": "quay.io/libpod/fedora",
                    "star_count": 0,
                    "tag": "1.0.0",
                },
            ],
        )

        report = self.client.images.search("fedora", listTags=True)
        self.assertEqual(len(report), 1)

        self.assertEqual(report[0]["name"], "quay.io/libpod/fedora")
        self.assertEqual(report[0]["tag"], "1.0.0")

    @requests_mock.Mocker()
    def test_push(self, mock):
        mock.post(tests.LIBPOD_URL + "/images/quay.io%2Ffedora%3Alatest/push")

        report = self.client.images.push("quay.io/fedora", "latest")

        expected = r"""{"status": "Pushing repository quay.io/fedora (1 tags)"}
{"status": "Pushing", "progressDetail": {}, "id": "quay.io/fedora"}
"""
        self.assertEqual(report, expected)

    @requests_mock.Mocker()
    def test_pull(self, mock):
        image_id = "sha256:326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"
        mock.post(
            tests.LIBPOD_URL + "/images/pull?reference=quay.io%2ffedora%3Alatest",
            json={
                "error": "",
                "id": image_id,
                "images": [image_id],
                "stream": "",
            },
        )
        mock.get(
            tests.LIBPOD_URL + "/images"
            "/sha256%3A326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab/json",
            json=FIRST_IMAGE,
        )

        image = self.client.images.pull("quay.io/fedora", "latest")
        self.assertEqual(image.id, image_id)

    @requests_mock.Mocker()
    def test_pull_enhanced(self, mock):
        image_id = "sha256:326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"
        mock.post(
            tests.LIBPOD_URL + "/images/pull?reference=quay.io%2ffedora%3Alatest",
            json={
                "error": "",
                "id": image_id,
                "images": [image_id],
                "stream": "",
            },
        )
        mock.get(
            tests.LIBPOD_URL + "/images"
            "/sha256%3A326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab/json",
            json=FIRST_IMAGE,
        )

        image = self.client.images.pull("quay.io/fedora:latest")
        self.assertEqual(image.id, image_id)

    @requests_mock.Mocker()
    def test_pull_platform(self, mock):
        image_id = "sha256:326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"
        adapter = mock.post(
            tests.LIBPOD_URL + "/images/pull?reference=quay.io%2ffedora%3Alatest&OS=linux",
            json={
                "error": "",
                "id": image_id,
                "images": [image_id],
                "stream": "",
            },
        )
        mock.get(
            tests.LIBPOD_URL + "/images"
            "/sha256%3A326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab/json",
            json=FIRST_IMAGE,
        )

        image = self.client.images.pull("quay.io/fedora:latest", platform="linux")
        self.assertEqual(image.id, image_id)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_pull_2x(self, mock):
        image_id = "sha256:326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab"
        mock.post(
            tests.LIBPOD_URL + "/images/pull?reference=quay.io%2ffedora&allTags=True",
            json={
                "error": "",
                "id": image_id,
                "images": [
                    image_id,
                    "c4b16966ecd94ffa910eab4e630e24f259bf34a87e924cd4b1434f267b0e354e",
                ],
                "stream": "",
            },
        )
        mock.get(
            tests.LIBPOD_URL + "/images"
            "/sha256%3A326dd9d7add24646a325e8eaa82125294027db2332e49c5828d96312c5d773ab/json",
            json=FIRST_IMAGE,
        )
        mock.get(
            tests.LIBPOD_URL
            + "/images/c4b16966ecd94ffa910eab4e630e24f259bf34a87e924cd4b1434f267b0e354e/json",
            json=SECOND_IMAGE,
        )

        images = self.client.images.pull("quay.io/fedora", "latest", all_tags=True)
        self.assertIsInstance(images, Iterable)
        self.assertIsInstance(images[0], Image)
        self.assertIsInstance(images[1], Image)

        self.assertEqual(images[0].id, image_id)
        self.assertEqual(
            images[1].id, "c4b16966ecd94ffa910eab4e630e24f259bf34a87e924cd4b1434f267b0e354e"
        )

    @requests_mock.Mocker()
    def test_list_with_name_parameter(self, mock):
        """Test that name parameter is correctly converted to a reference filter"""
        mock.get(
            tests.LIBPOD_URL + "/images/json?filters=%7B%22reference%22%3A+%5B%22fedora%22%5D%7D",
            json=[FIRST_IMAGE],
        )

        images = self.client.images.list(name="fedora")

        self.assertEqual(len(images), 1)
        self.assertIsInstance(images[0], Image)
        self.assertEqual(images[0].tags, ["fedora:latest", "fedora:33"])

    @requests_mock.Mocker()
    def test_list_with_name_and_existing_filters(self, mock):
        """Test that name parameter works alongside other filters"""
        mock.get(
            tests.LIBPOD_URL
            + (
                "/images/json?filters=%7B%22dangling%22%3A+%5B%22True%22%5D%2C+"
                "%22reference%22%3A+%5B%22fedora%22%5D%7D"
            ),
            json=[FIRST_IMAGE],
        )

        images = self.client.images.list(name="fedora", filters={"dangling": True})

        self.assertEqual(len(images), 1)
        self.assertIsInstance(images[0], Image)

    @requests_mock.Mocker()
    def test_list_with_name_overrides_reference_filter(self, mock):
        """Test that name parameter takes precedence over existing reference filter"""
        mock.get(
            tests.LIBPOD_URL + "/images/json?filters=%7B%22reference%22%3A+%5B%22fedora%22%5D%7D",
            json=[FIRST_IMAGE],
        )

        # The name parameter should override the reference filter
        images = self.client.images.list(
            name="fedora",
            filters={"reference": "ubuntu"},  # This should be overridden
        )

        self.assertEqual(len(images), 1)
        self.assertIsInstance(images[0], Image)

    @requests_mock.Mocker()
    def test_list_with_all_and_name(self, mock):
        """Test that all parameter works alongside name filter"""
        mock.get(
            tests.LIBPOD_URL
            + "/images/json?all=true&filters=%7B%22reference%22%3A+%5B%22fedora%22%5D%7D",
            json=[FIRST_IMAGE],
        )

        images = self.client.images.list(all=True, name="fedora")

        self.assertEqual(len(images), 1)
        self.assertIsInstance(images[0], Image)

    @requests_mock.Mocker()
    def test_list_with_empty_name(self, mock):
        """Test that empty name parameter doesn't add a reference filter"""
        mock.get(tests.LIBPOD_URL + "/images/json", json=[FIRST_IMAGE])

        images = self.client.images.list(name="")

        self.assertEqual(len(images), 1)
        self.assertIsInstance(images[0], Image)

    @requests_mock.Mocker()
    def test_list_with_none_name(self, mock):
        """Test that None name parameter doesn't add a reference filter"""
        mock.get(tests.LIBPOD_URL + "/images/json", json=[FIRST_IMAGE])

        images = self.client.images.list(name=None)

        self.assertEqual(len(images), 1)
        self.assertIsInstance(images[0], Image)


if __name__ == '__main__':
    unittest.main()
