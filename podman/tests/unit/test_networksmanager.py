import unittest

import requests_mock

from podman import PodmanClient, tests
from podman.domain.networks import Network
from podman.domain.networks_manager import NetworksManager

FIRST_NETWORK = {
    "Name": "podman",
    "Id": "2f259bab93aaaaa2542ba43ef33eb990d0999ee1b9924b557b7be53c0b7a1bb9",
    "Created": "2021-03-01T09:18:37.491308364-07:00",
    "Scope": "local",
    "Driver": "bridge",
    "EnableIPv6": False,
    "IPAM": {
        "Driver": "default",
        "Options": {},
        "Config": [{"Subnet": "10.88.0.0/16", "Gateway": "10.88.0.1"}],
    },
    "Internal": False,
    "Attachable": False,
    "Ingress": False,
    "ConfigFrom": {"Network": ""},
    "ConfigOnly": False,
    "Containers": {},
    "Options": {},
    "Labels": {},
}

SECOND_NETWORK = {
    "Name": "database",
    "Id": "3549b0028b75d981cdda2e573e9cb49dedc200185876df299f912b79f69dabd8",
    "Created": "2021-03-01T09:18:37.491308364-07:00",
    "Scope": "local",
    "Driver": "bridge",
    "EnableIPv6": False,
    "IPAM": {
        "Driver": "default",
        "Options": {},
        "Config": [{"Subnet": "10.88.0.0/16", "Gateway": "10.88.0.1"}],
    },
    "Internal": False,
    "Attachable": False,
    "Ingress": False,
    "ConfigFrom": {"Network": ""},
    "ConfigOnly": False,
    "Containers": {},
    "Options": {},
    "Labels": {},
}

FIRST_NETWORK_LIBPOD = {
    "name": "podman",
    "id": "2f259bab93aaaaa2542ba43ef33eb990d0999ee1b9924b557b7be53c0b7a1bb9",
    "driver": "bridge",
    "network_interface": "libpod_veth0",
    "created": "2022-01-28T09:18:37.491308364-07:00",
    "subnets": [
        {
            "subnet": "10.11.12.0/24",
            "gateway": "10.11.12.1",
            "lease_range": {
                "start_ip": "10.11.12.1",
                "end_ip": "10.11.12.63",
            },
        }
    ],
    "ipv6_enabled": False,
    "internal": False,
    "dns_enabled": False,
    "labels": {},
    "options": {},
    "ipam_options": {},
}

SECOND_NETWORK_LIBPOD = {
    "name": "database",
    "id": "3549b0028b75d981cdda2e573e9cb49dedc200185876df299f912b79f69dabd8",
    "created": "2021-03-01T09:18:37.491308364-07:00",
    "driver": "bridge",
    "network_interface": "libpod_veth1",
    "subnets": [
        {
            "subnet": "10.11.12.0/24",
            "gateway": "10.11.12.1",
            "lease_range": {
                "start_ip": "10.11.12.1",
                "end_ip": "10.11.12.63",
            },
        }
    ],
    "ipv6_enabled": False,
    "internal": False,
    "dns_enabled": False,
    "labels": {},
    "options": {},
    "ipam_options": {},
}


class NetworksManagerTestCase(unittest.TestCase):
    """Test NetworksManager area of concern.

    Note:
        Mock responses need to be coded for libpod returns.  The python bindings are responsible
            for mapping to compatible output.
    """

    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)
        self.addCleanup(self.client.close)

    def test_podmanclient(self):
        manager = self.client.networks
        self.assertIsInstance(manager, NetworksManager)

    @requests_mock.Mocker()
    def test_get(self, mock):
        mock.get(tests.LIBPOD_URL + "/networks/podman", json=FIRST_NETWORK)

        actual = self.client.networks.get("podman")
        self.assertIsInstance(actual, Network)
        self.assertEqual(
            actual.id, "2f259bab93aaaaa2542ba43ef33eb990d0999ee1b9924b557b7be53c0b7a1bb9"
        )

    @requests_mock.Mocker()
    def test_list_libpod(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/networks/json",
            json=[FIRST_NETWORK_LIBPOD, SECOND_NETWORK_LIBPOD],
        )

        actual = self.client.networks.list()
        self.assertEqual(len(actual), 2)

        self.assertIsInstance(actual[0], Network)
        self.assertEqual(
            actual[0].id, "2f259bab93aaaaa2542ba43ef33eb990d0999ee1b9924b557b7be53c0b7a1bb9"
        )
        self.assertEqual(actual[0].attrs["name"], "podman")

        self.assertIsInstance(actual[1], Network)
        self.assertEqual(
            actual[1].id, "3549b0028b75d981cdda2e573e9cb49dedc200185876df299f912b79f69dabd8"
        )
        self.assertEqual(actual[1].name, "database")

    @requests_mock.Mocker()
    def test_create_libpod(self, mock):
        adapter = mock.post(tests.LIBPOD_URL + "/networks/create", json=FIRST_NETWORK_LIBPOD)

        network = self.client.networks.create("podman", dns_enabled=True, enable_ipv6=True)
        self.assertIsInstance(network, Network)

        self.assertEqual(adapter.call_count, 1)
        self.assertDictEqual(
            adapter.last_request.json(),
            {
                "name": "podman",
                "ipv6_enabled": True,
                "dns_enabled": True,
            },
        )

    @requests_mock.Mocker()
    def test_create_defaults(self, mock):
        adapter = mock.post(tests.LIBPOD_URL + "/networks/create", json=FIRST_NETWORK_LIBPOD)

        network = self.client.networks.create("podman")
        self.assertEqual(adapter.call_count, 1)
        self.assertDictEqual(
            adapter.last_request.json(),
            {"name": "podman"},
        )

    @requests_mock.Mocker()
    def test_prune_libpod(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/networks/prune",
            json=[
                {"Name": "podman", "Error": None},
                {"Name": "database", "Error": None},
            ],
        )

        actual = self.client.networks.prune()
        self.assertListEqual(actual["NetworksDeleted"], ["podman", "database"])


if __name__ == '__main__':
    unittest.main()
