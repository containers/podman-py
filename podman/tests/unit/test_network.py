import unittest

import requests_mock

from podman import PodmanClient, tests
from podman.domain.networks import Network

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


class NetworkTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

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
            "http+unix://localhost:9999/v1.40/networks/podman",
            status_code=204,
            json={"Name": "podman", "Err": None},
        )
        net = Network(attrs=FIRST_NETWORK, client=self.client.api)

        net.remove(force=True)
        self.assertTrue(adapter.called_once)

    @requests_mock.Mocker()
    def test_connect(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v1.40/networks/podman/connect",
        )
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
        adapter = mock.post(
            "http+unix://localhost:9999/v1.40/networks/podman/disconnect",
        )
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
