import unittest
import random

from podman import PodmanClient
from podman.errors.exceptions import NotFound
from podman.tests.integration import base


class PodsIntegrationTest(base.IntegrationTest):
    """Pods Integration tests."""

    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

        self.alpine_image = self.client.images.pull("quay.io/libpod/alpine", tag="latest")

        # TODO should this use podman binary instead?
        for container in self.client.containers.list():
            container.remove(force=True)

    def test_pod_crud(self):
        """Test Pod CRUD."""

        pod_name = f"pod_{random.getrandbits(160):x}"

        with self.subTest("Create no_infra"):
            pod = self.client.pods.create(
                pod_name,
                labels={
                    "unittest": "true",
                },
                no_infra=True,
            )
            self.assertEqual(pod_name, pod.name)

        with self.subTest("Inspect"):
            actual = self.client.pods.get(pod.id)
            self.assertEqual(actual.name, pod.name)
            self.assertNotIn("Containers", actual.attrs)

        with self.subTest("Exists"):
            self.assertTrue(self.client.pods.exists(pod_name))

        # TODO Need method for deterministic prune...
        # with self.subTest("Prune"):
        # report = self.client.pods.prune()
        # self.assertIn("PodsDeleted", report)
        # self.assertIn(actual.id, report["PodsDeleted"])
        #
        # with self.assertRaises(NotFound):
        #     pod.reload()
        #
        # For now, delete pod explicitly
        with self.subTest("Delete"):
            pod.remove(force=True)
            with self.assertRaises(NotFound):
                pod.reload()

        with self.subTest("Create with infra"):
            pod = self.client.pods.create(
                pod_name,
                labels={
                    "unittest": "true",
                },
            )
            self.assertEqual(pod_name, pod.name)

        with self.subTest("Inspect"):
            actual = self.client.pods.get(pod.id)
            self.assertEqual(actual.name, pod.name)
            self.assertIn("Containers", actual.attrs)

        with self.subTest("Stop/Start"):
            actual.stop()
            actual.start()

        with self.subTest("Restart"):
            actual.restart()

        with self.subTest("Pause/Unpause"):
            actual.pause()
            actual.reload()
            self.assertEqual(actual.attrs["State"], "Paused")

            actual.unpause()
            actual.reload()
            self.assertEqual(actual.attrs["State"], "Running")

        with self.subTest("Add container"):
            container = self.client.containers.create(self.alpine_image, command=["ls"], pod=actual)
            actual = self.client.pods.get(pod.id)

            ids = {c["Id"] for c in actual.attrs["Containers"]}
            self.assertIn(container.id, ids)

        with self.subTest("Ps"):
            procs = actual.top()

            self.assertGreater(len(procs["Processes"]), 0)
            self.assertGreater(len(procs["Titles"]), 0)

        with self.subTest("List"):
            pods = self.client.pods.list()
            self.assertGreaterEqual(len(pods), 1)

            ids = {p.id for p in pods}
            self.assertIn(actual.id, ids)

        with self.subTest("Stats"):
            report = self.client.pods.stats(all=True)
            self.assertGreaterEqual(len(report), 1)

        with self.subTest("Delete"):
            pod.remove(force=True)
            with self.assertRaises(NotFound):
                pod.reload()


if __name__ == '__main__':
    unittest.main()
