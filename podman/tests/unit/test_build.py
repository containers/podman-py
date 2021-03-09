import io
import json
import unittest
from collections import Iterable

import requests_mock

from podman import PodmanClient
from podman.domain.images import Image
from podman.errors.exceptions import BuildError, DockerException, PodmanError


class TestBuildCase(unittest.TestCase):
    """Test ImagesManager build().

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

    @requests_mock.Mocker()
    def test_build(self, mock):
        stream = [
            {"stream": " ---\u003e a9eb17255234"},
            {"stream": "Step 1 : VOLUME /data"},
            {"stream": " ---\u003e Running in abdc1e6896c6"},
            {"stream": " ---\u003e 713bca62012e"},
            {"stream": "Removing intermediate container abdc1e6896c6"},
            {"stream": "Step 2 : CMD [\"/bin/sh\"]"},
            {"stream": " ---\u003e Running in dba30f2a1a7e"},
            {"stream": " ---\u003e 032b8b2855fc"},
            {"stream": "Removing intermediate container dba30f2a1a7e"},
            {"stream": "Successfully built 032b8b2855fc"},
        ]

        buffer = io.StringIO()
        for entry in stream:
            buffer.write(json.JSONEncoder().encode(entry))
            buffer.write("\n")

        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/build"
            "?t=latest&cpuperiod=10&extrahosts=%7B%22database%22%3A+%22127.0.0.1%22%7D",
            text=buffer.getvalue(),
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/images/032b8b2855fc/json",
            json={
                "Id":          "032b8b2855fc",
                "ParentId":    "",
                "RepoTags":    ["fedora:latest", "fedora:33", "<none>:<none>"],
                "RepoDigests": [
                    "fedora@sha256:9598a10fa72b402db876ccd4b3d240a4061c7d1e442745f1896ba37e1bf38664"
                ],
                "Created":     1614033320,
                "Size":        23855104,
                "VirtualSize": 23855104,
                "SharedSize":  0,
                "Labels":      {},
                "Containers":  2,
            }
        )

        image, logs = self.client.images.build(
            path="/tmp/context_dir",
            tag="latest",
            buildargs={
                "BUILD_DATE": "January 1, 1970",
            },
            container_limits={
                "cpuperiod": 10,
            },
            extra_hosts={"database": "127.0.0.1"},
            labels={"Unittest": "true"},
        )
        self.assertIsInstance(image, Image)
        self.assertEqual(image.id, "032b8b2855fc")
        self.assertIsInstance(logs, Iterable)

    @requests_mock.Mocker()
    def test_build_logged_error(self, mock):
        stream = [
            {"error": "We do not need any stinking badges."},
        ]

        buffer = io.StringIO()
        for entry in stream:
            buffer.write(json.JSONEncoder().encode(entry))
            buffer.write("\n")

        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/build",
            text=buffer.getvalue(),
        )

        with self.assertRaises(BuildError) as e:
            self.client.images.build(path="/tmp/context_dir")
        self.assertEqual(e.exception.msg, "We do not need any stinking badges.")

    @requests_mock.Mocker()
    def test_build_no_context(self, mock):
        mock.post("http+unix://localhost:9999/v3.0.0/libpod/images/build")
        with self.assertRaises(TypeError):
            self.client.images.build()

    @requests_mock.Mocker()
    def test_build_encoding(self, mock):
        mock.post("http+unix://localhost:9999/v3.0.0/libpod/images/build")
        with self.assertRaises(DockerException):
            self.client.images.build(path="/root", gzip=True, encoding="utf-8")


if __name__ == '__main__':
    unittest.main()
