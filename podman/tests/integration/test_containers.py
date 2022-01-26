import io
import random
import tarfile
import unittest

try:
    # Python >= 3.10
    from collections.abc import Iterator
except:
    # Python < 3.10
    from collections import Iterator

import podman.tests.integration.base as base
from podman import PodmanClient
from podman.domain.containers import Container
from podman.domain.images import Image
from podman.errors import NotFound


# @unittest.skipIf(os.geteuid() != 0, 'Skipping, not running as root')


class ContainersIntegrationTest(base.IntegrationTest):
    """Containers Integration tests."""

    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

        self.alpine_image = self.client.images.pull("quay.io/libpod/alpine", tag="latest")

        # TODO should this use podman binary instead?
        for container in self.client.containers.list():
            container.remove(force=True)

    def test_container_crud(self):
        """Test Container CRUD."""

        random_string = f"{random.getrandbits(160):x}"

        with self.subTest("Create from Alpine Image"):
            container = self.client.containers.create(
                self.alpine_image, command=["echo", random_string], ports={'2222/tcp': 3333}
            )
            self.assertIsInstance(container, Container)
            self.assertGreater(len(container.attrs), 0)
            self.assertIsNotNone(container.id)
            self.assertIsNotNone(container.name)
            self.assertIsInstance(container.image, Image)
            self.assertTrue(self.client.containers.exists(container.id))

            self.assertIn("quay.io/libpod/alpine:latest", container.image.tags)

        with self.subTest("Inspect Container"):
            actual = self.client.containers.get(container.id)
            self.assertIsInstance(actual, Container)
            self.assertEqual(actual.id, container.id)

            self.assertIn("2222/tcp", container.attrs["NetworkSettings"]["Ports"])
            self.assertEqual(
                "3333", container.attrs["NetworkSettings"]["Ports"]["2222/tcp"][0]["HostPort"]
            )

        file_contents = b"This is an integration test for archive."
        file_buffer = io.BytesIO(file_contents)

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            info = tarfile.TarInfo("/")
            info.type = tarfile.DIRTYPE
            tar.addfile(info)

            info = tarfile.TarInfo("unittest")
            info.size = len(file_buffer.getbuffer())
            tar.addfile(info, file_buffer)
            tarball = tar_buffer.getvalue()

        with self.subTest("Archive /root/unittest"):
            self.assertTrue(container.put_archive("/root", data=tarball))

            actual, stats = container.get_archive("/root")

            with io.BytesIO() as fd:
                for chunk in actual:
                    fd.write(chunk)
                fd.seek(0, 0)

                with tarfile.open(fileobj=fd, mode="r") as tar:
                    contents = tar.extractfile("root/unittest").read()
                self.assertEqual(contents, file_contents)

        with self.subTest("List containers --all"):
            containers = self.client.containers.list(all=True)
            self.assertGreater(len(containers), 0)
            ids = [i.id for i in containers]
            self.assertIn(container.id, ids)

        with self.subTest("Get container's logs"):
            container.start()
            container.wait(condition="exited")

            logs_iter = container.logs(stream=False)
            self.assertIsInstance(logs_iter, Iterator)

            logs = list(logs_iter)
            self.assertIn((random_string + "\n").encode("utf-8"), logs)

        with self.subTest("Delete Container"):
            container.remove()
            with self.assertRaises(NotFound):
                self.client.containers.get(container.id)

        with self.subTest("Run Container"):
            top_ctnr = self.client.containers.run(
                self.alpine_image, "/usr/bin/top", name="TestRunPs", detach=True
            )
            self.assertEqual(top_ctnr.status, "running")

            top_ctnr.pause()
            top_ctnr.reload()
            self.assertEqual(top_ctnr.status, "paused")

            top_ctnr.unpause()
            top_ctnr.reload()
            self.assertEqual(top_ctnr.status, "running")

            report = top_ctnr.top()
            # See https://github.com/containers/podman/pull/9892 for the service
            #   side fix requires podman >= 3.2
            # processes = [i.strip() for i in report["Processes"][0]]
            self.assertIn("/usr/bin/top", report["Processes"][0][-1])

            top_ctnr.stop()
            top_ctnr.reload()
            self.assertIn(top_ctnr.status, ("exited", "stopped"))

        with self.subTest("Prune Containers"):
            report = self.client.containers.prune()
            self.assertIn(top_ctnr.id, report["ContainersDeleted"])

            # SpaceReclaimed is the size of the content created during the running of the container
            self.assertEqual(report["SpaceReclaimed"], 0)

            with self.assertRaises(NotFound):
                self.client.containers.get(top_ctnr.id)


if __name__ == '__main__':
    unittest.main()
