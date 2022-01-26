import random
import unittest

from podman import PodmanClient
from podman.errors import NotFound
from podman.tests.integration import base


class PodsIntegrationTest(base.IntegrationTest):
    """Pods Integration tests."""

    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

        self.alpine_image = self.client.images.pull("quay.io/libpod/alpine", tag="latest")
        self.pod_name = f"pod_{random.getrandbits(160):x}"

        for container in self.client.containers.list():
            container.remove(force=True)

    def tearDown(self):
        if self.client.pods.exists(self.pod_name):
            self.client.pods.remove(self.pod_name)
        super().tearDown()

    def test_pod_crud(self):
        """Test Pod CRUD."""
        with self.subTest("Create no_infra"):
            pod = self.client.pods.create(
                self.pod_name,
                labels={
                    "unittest": "true",
                },
                no_infra=True,
            )
            self.assertEqual(self.pod_name, pod.name)
            self.assertTrue(self.client.pods.exists(pod.id))

        with self.subTest("Inspect"):
            actual = self.client.pods.get(pod.id)
            self.assertEqual(actual.name, pod.name)
            self.assertNotIn("Containers", actual.attrs)

        with self.subTest("Exists"):
            self.assertTrue(self.client.pods.exists(self.pod_name))

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

    def test_pod_crud_infra(self):
        """Test Pod CRUD with infra container."""

        with self.subTest("Create with infra"):
            pod = self.client.pods.create(
                self.pod_name,
                labels={
                    "unittest": "true",
                },
            )
            self.assertEqual(self.pod_name, pod.name)

        with self.subTest("Inspect"):
            actual = self.client.pods.get(pod.id)
            self.assertEqual(actual.name, pod.name)
            self.assertIn("Containers", actual.attrs)
            self.assertEqual(actual.attrs["State"], "Created")

        with self.subTest("Add container"):
            container = self.client.containers.create(self.alpine_image, command=["ls"], pod=actual)
            actual = self.client.pods.get(pod.id)

            ids = {c["Id"] for c in actual.attrs["Containers"]}
            self.assertIn(container.id, ids)

        with self.subTest("List"):
            pods = self.client.pods.list()
            self.assertGreaterEqual(len(pods), 1)

            ids = {p.id for p in pods}
            self.assertIn(actual.id, ids)

        with self.subTest("Delete"):
            pod.remove(force=True)
            with self.assertRaises(NotFound):
                pod.reload()

    def test_ps(self):
        pod = self.client.pods.create(
            self.pod_name,
            labels={
                "unittest": "true",
            },
            no_infra=True,
        )
        self.assertTrue(self.client.pods.exists(pod.id))
        self.client.containers.create(
            self.alpine_image, command=["top"], detach=True, tty=True, pod=pod
        )
        pod.start()
        pod.reload()

        with self.subTest("top"):
            # this is the API top call not the
            # top command running in the container
            procs = pod.top()

            self.assertGreater(len(procs["Processes"]), 0)
            self.assertGreater(len(procs["Titles"]), 0)

        with self.subTest("stats"):
            report = self.client.pods.stats(all=True)
            self.assertGreaterEqual(len(report), 1)

        with self.subTest("Stop/Start"):
            pod.stop()
            pod.reload()
            self.assertIn(pod.attrs["State"], ("Stopped", "Exited"))

            pod.start()
            pod.reload()
            self.assertEqual(pod.attrs["State"], "Running")

        with self.subTest("Restart"):
            pod.stop()
            pod.restart()
            pod.reload()
            self.assertEqual(pod.attrs["State"], "Running")

        with self.subTest("Pause/Unpause"):
            pod.pause()
            pod.reload()
            self.assertEqual(pod.attrs["State"], "Paused")

            pod.unpause()
            pod.reload()
            self.assertEqual(pod.attrs["State"], "Running")

        pod.stop()


if __name__ == '__main__':
    unittest.main()
