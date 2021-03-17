#   Copyright 2020 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#
"""networks calls integration tests"""


import unittest
import os
from podman import networks, PodmanClient
from podman.api_connection import ApiConnection
import podman.tests.integration.base as base
from podman.domain.containers import Container
from podman.domain.ipam import IPAMPool, IPAMConfig
from podman.errors import NotFound


class TestNetworks(base.IntegrationTest):
    """networks call integration test"""

    pool = IPAMPool(subnet="172.16.0.0/12", iprange="172.16.0.0/16", gateway="172.31.255.254")

    ipam = IPAMConfig(pool_configs=[pool])

    def setUp(self):
        super().setUp()
        self.client = PodmanClient(base_url=self.socket_uri, log_level=self.log_level)
        self.addCleanup(self.client.close)

    def test_network_crud(self):
        """integration: networks create and remove calls"""

        with self.subTest("Create Network"):
            network = self.client.networks.create(
                "integration_test",
                disabled_dns=True,
                enable_ipv6=False,
                ipam=TestNetworks.ipam,
            )
            self.assertEqual(network.name, "integration_test")

        with self.subTest("Inspect Network"):
            network = self.client.networks.get("integration_test")
            self.assertEqual(network.name, "integration_test")

        with self.subTest("List Networks"):
            nets = self.client.networks.list()
            names = [i.name for i in nets]
            self.assertIn("integration_test", names)

        with self.subTest("Delete network"):
            network = self.client.networks.get("integration_test")
            network.remove(force=True)

            with self.assertRaises(NotFound):
                self.client.networks.get("integration_test")

    # @unittest.skipIf(os.geteuid() != 0, 'Skipping, not running as root')
    @unittest.skip("Additionally network tests need to segregate by network")
    def test_network_connect(self):
        alpine_container = Container()

        with self.subTest("Create Network"):
            network = self.client.networks.create(
                "integration_test",
                disabled_dns=True,
                enable_ipv6=False,
                ipam=TestNetworks.ipam,
            )
            self.assertEqual(network.name, "integration_test")

        # TODO implement network.containers
        with self.subTest("Connect container to Network"):
            pre_count = network.containers
            network.connect(container=alpine_container)
            network.reload()

            post_count = network.containers
            self.assertLess(pre_count, post_count)

        with self.subTest("Disconnect container from Network"):
            pre_count = network.containers
            network.disconnect(container=alpine_container)
            network.reload()

            post_count = network.containers
            self.assertGreater(pre_count, post_count)

    @unittest.skip("Requires Podman 3.1")
    def test_network_prune(self):
        network = self.client.networks.create(
            "integration_test",
            disabled_dns=True,
            enable_ipv6=False,
            ipam=TestNetworks.ipam,
        )
        self.assertEqual(network.name, "integration_test")

        report = self.client.networks.prune()
        self.assertIn(network.name, report["NetworksDeleted"])
