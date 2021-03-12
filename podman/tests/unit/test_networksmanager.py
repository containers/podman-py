import unittest

import requests_mock

from podman import PodmanClient
from podman.domain.ipam import IPAMConfig, IPAMPool
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

FIRST_NETWORK_LIBPOD = [
    {
        "cniVersion": "0.4.0",
        "name": "podman",
        "plugins": [
            {
                "bridge": "cni-podman0",
                "hairpinMode": True,
                "ipMasq": True,
                "ipam": {
                    "ranges": [[{"gateway": "10.88.0.1", "subnet": "10.88.0.0/16"}]],
                    "routes": [{"dst": "0.0.0.0/0"}],
                    "type": "host-local",
                },
                "isGateway": True,
                "type": "bridge",
            },
            {"capabilities": {"portMappings": True}, "type": "portmap"},
            {"type": "firewall"},
            {"type": "tuning"},
        ],
    }
]

SECOND_NETWORK_LIBPOD = [
    {
        "cniVersion": "0.4.0",
        "name": "database",
        "plugins": [
            {
                "bridge": "cni-podman0",
                "hairpinMode": True,
                "ipMasq": True,
                "ipam": {
                    "ranges": [[{"gateway": "10.88.0.1", "subnet": "10.88.0.0/16"}]],
                    "routes": [{"dst": "0.0.0.0/0"}],
                    "type": "host-local",
                },
                "isGateway": True,
                "type": "bridge",
            },
            {"capabilities": {"portMappings": True}, "type": "portmap"},
            {"type": "firewall"},
            {"type": "tuning"},
        ],
    }
]


class NetworksManagerTestCase(unittest.TestCase):
    """Test NetworksManager area of concern.

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
        manager = self.client.networks
        self.assertIsInstance(manager, NetworksManager)

    @requests_mock.Mocker()
    def test_get(self, mock):
        mock.get(
            "http+unix://localhost:9999/v1.40/networks/podman",
            json=FIRST_NETWORK,
        )

        actual = self.client.networks.get("podman")
        self.assertIsInstance(actual, Network)
        self.assertEqual(
            actual.id, "2f259bab93aaaaa2542ba43ef33eb990d0999ee1b9924b557b7be53c0b7a1bb9"
        )

    @requests_mock.Mocker()
    def test_get_libpod(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/networks/podman/json",
            json=FIRST_NETWORK_LIBPOD,
        )

        actual = self.client.networks.get("podman", compatible=False)
        self.assertIsInstance(actual, Network)
        self.assertEqual(actual.attrs["name"], "podman")

    @requests_mock.Mocker()
    def test_list(self, mock):
        mock.get(
            "http+unix://localhost:9999/v1.40/networks",
            json=[FIRST_NETWORK, SECOND_NETWORK],
        )

        actual = self.client.networks.list()
        self.assertEqual(len(actual), 2)

        self.assertIsInstance(actual[0], Network)
        self.assertEqual(
            actual[0].id, "2f259bab93aaaaa2542ba43ef33eb990d0999ee1b9924b557b7be53c0b7a1bb9"
        )
        self.assertEqual(actual[0].attrs["Name"], "podman")

        self.assertIsInstance(actual[1], Network)
        self.assertEqual(
            actual[1].id, "3549b0028b75d981cdda2e573e9cb49dedc200185876df299f912b79f69dabd8"
        )
        self.assertEqual(actual[1].name, "database")

    @requests_mock.Mocker()
    def test_list_libpod(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/networks/json",
            json=FIRST_NETWORK_LIBPOD + SECOND_NETWORK_LIBPOD,
        )

        actual = self.client.networks.list(compatible=False)
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
    def test_create(self, mock):
        adapter = mock.post("http+unix://localhost:9999/v3.0.0/libpod/networks/create?name=podman")
        mock.get(
            "http+unix://localhost:9999/v1.40/networks/podman",
            json=FIRST_NETWORK,
        )

        pool = IPAMPool(subnet="172.16.0.0/12", iprange="172.16.0.0/16", gateway="172.31.255.254")
        ipam = IPAMConfig(pool_configs=[pool])

        network = self.client.networks.create(
            "podman", disabled_dns=True, enable_ipv6=False, ipam=ipam
        )

        self.assertEqual(adapter.call_count, 1)
        self.assertDictEqual(
            adapter.last_request.json(),
            {
                'DisabledDNS': True,
                'Gateway': '172.31.255.254',
                'IPv6': False,
                'Range': {'IP': '172.16.0.0', 'Mask': '255.255.0.0'},
                'Subnet': {'IP': '172.16.0.0', 'Mask': '255.240.0.0'},
            },
        )

        self.assertEqual(network.name, "podman")

    @requests_mock.Mocker()
    def test_create_defaults(self, mock):
        adapter = mock.post("http+unix://localhost:9999/v3.0.0/libpod/networks/create?name=podman")
        mock.get(
            "http+unix://localhost:9999/v1.40/networks/podman",
            json=FIRST_NETWORK,
        )

        network = self.client.networks.create("podman")
        self.assertEqual(adapter.call_count, 1)
        self.assertEqual(network.name, "podman")
        self.assertEqual(len(adapter.last_request.json()), 0)

    @requests_mock.Mocker()
    def test_prune(self, mock):
        mock.post(
            "http+unix://localhost:9999/v1.40/networks/prune",
            json={"NetworksDeleted": ["podman", "database"]},
        )

        actual = self.client.networks.prune()
        self.assertListEqual(actual["NetworksDeleted"], ["podman", "database"])

    @requests_mock.Mocker()
    def test_prune_libpod(self, mock):
        mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/networks/prune",
            json=[
                {"Name": "podman", "Error": None},
                {"Name": "database", "Error": None},
            ],
        )

        actual = self.client.networks.prune(compatible=False)
        self.assertListEqual(actual["NetworksDeleted"], ["podman", "database"])


if __name__ == '__main__':
    unittest.main()
