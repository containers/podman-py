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


class NetworkTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)
        self.addCleanup(self.client.close)

    def test_id(self):
        expected = {"Id": "1cf06390-709d-4ffa-a054-c3083abe367c"}
        actual = Network(attrs=expected)
        self.assertEqual(actual.id, expected["Id"])

        actual = Network(attrs={"name": "database"})
        self.assertEqual(
            actual.id, "3549b0028b75d981cdda2e573e9cb49dedc200185876df299f912b79f69dabd8"
        )

    def test_name(self):
        actual = Network(attrs={"Name": "database"})
        self.assertEqual(actual.name, "database")

        actual = Network({"name": "database"})
        self.assertEqual(actual.name, "database")

    @requests_mock.Mocker()
    def test_remove(self, mock):
        adapter = mock.delete(
            tests.LIBPOD_URL + "/networks/podman?force=True",
            status_code=204,
            json={"Name": "podman", "Err": None},
        )
        net_manager = NetworksManager(client=self.client.api)
        net = net_manager.prepare_model(attrs=FIRST_NETWORK)

        net.remove(force=True)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_connect(self, mock):
        adapter = mock.post(tests.LIBPOD_URL + "/networks/podman/connect")
        net = Network(attrs=FIRST_NETWORK, client=self.client.api)

        net.connect(
            "podman_ctnr",
            aliases=["production"],
            ipv4_address="172.16.0.1",
        )
        self.assertEqual(adapter.call_count, 1)
        self.assertDictEqual(
            adapter.last_request.json(),
            {
                'Container': 'podman_ctnr',
                "EndpointConfig": {
                    'Aliases': ['production'],
                    'IPAMConfig': {'IPv4Address': '172.16.0.1'},
                    'IPAddress': '172.16.0.1',
                    'NetworkID': '2f259bab93aaaaa2542ba43ef33eb990d0999ee1b9924b557b7be53c0b7a1bb9',
                },
            },
        )

    @requests_mock.Mocker()
    def test_disconnect(self, mock):
        adapter = mock.post(tests.LIBPOD_URL + "/networks/podman/disconnect")
        net = Network(attrs=FIRST_NETWORK, client=self.client.api)

        net.disconnect("podman_ctnr", force=True)
        self.assertEqual(adapter.call_count, 1)
        self.assertDictEqual(
            adapter.last_request.json(),
            {
                'Container': 'podman_ctnr',
                "Force": True,
            },
        )


if __name__ == '__main__':
    unittest.main()
