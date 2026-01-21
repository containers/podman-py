import unittest

import requests_mock

from podman import PodmanClient, tests
from podman.domain.pods import Pod
from podman.domain.pods_manager import PodsManager

TEST_POD = {
    "ID": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
    "Name": "test-pod",
}


class ManagerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_prepare_model(self):
        with self.assertRaisesRegex(Exception, "^Can't create Pod from .*$"):
            PodsManager().prepare_model(attrs=("Sets", "Not", "supported"))

    @requests_mock.Mocker()
    def test_prepare_model_sets_manager_for_reload(self, mock):
        """Test that prepare_model sets manager attribute so reload() works."""
        pod_id = "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"

        mock.get(
            tests.LIBPOD_URL + f"/pods/{pod_id}/json",
            json=TEST_POD,
        )

        pod = Pod({"Id": pod_id})

        self.client.pods.prepare_model(pod)

        self.assertIsNotNone(pod.manager)
        self.assertIsInstance(pod.manager, PodsManager)

        pod.reload()

        self.assertTrue(mock.called)
        self.assertEqual(len(mock.request_history), 1)

    def test_collection_property_aliases_manager(self):
        """Test that collection property is an alias for manager."""
        pod = Pod(attrs={"Id": "12345"}, collection=self.client.pods)
        # collection should be accessible via property
        self.assertTrue(hasattr(pod, "collection"))
        # collection should equal manager
        self.assertIs(pod.collection, pod.manager)


if __name__ == '__main__':
    unittest.main()
