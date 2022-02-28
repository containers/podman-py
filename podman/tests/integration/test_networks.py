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
"""Network integration tests."""
import os
import random
import unittest
from contextlib import suppress

import podman.tests.integration.base as base
from podman import PodmanClient
from podman.domain.ipam import IPAMConfig, IPAMPool
from podman.errors import NotFound


class NetworksIntegrationTest(base.IntegrationTest):
    """networks call integration test"""

    pool = IPAMPool(subnet="10.11.13.0/24", iprange="10.11.13.0/26", gateway="10.11.13.1")

    ipam = IPAMConfig(pool_configs=[pool])

    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

    def tearDown(self):
        with suppress(NotFound):
            self.client.networks.get("integration_test").remove(force=True)

        super().tearDown()

    def test_network_crud(self):
        """integration: networks create and remove calls"""

        with self.subTest("Create Network"):
            network = self.client.networks.create(
                "integration_test",
                dns_enabled=False,
                ipam=NetworksIntegrationTest.ipam,
            )
            self.assertEqual(network.name, "integration_test")
            self.assertTrue(self.client.networks.exists(network.name))

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

    @unittest.skip("Skipping, libpod endpoint does not report container count")
    def test_network_connect(self):
        self.alpine_image = self.client.images.pull("quay.io/libpod/alpine", tag="latest")

        random_string = f"{random.getrandbits(160):x}"
        container = self.client.containers.create(
            self.alpine_image, command=["echo", random_string]
        )

        with self.subTest("Create Network"):
            network = self.client.networks.create(
                "integration_test",
                disabled_dns=True,
                enable_ipv6=False,
                ipam=NetworksIntegrationTest.ipam,
            )
            self.assertEqual(network.name, "integration_test")

        with self.subTest("Connect container to Network"):
            pre_count = network.containers
            network.connect(container=container)
            network.reload()

            post_count = network.containers
            self.assertLess(pre_count, post_count)

        with self.subTest("Disconnect container from Network"):
            pre_count = network.containers
            network.disconnect(container=container)
            network.reload()

            post_count = network.containers
            self.assertGreater(pre_count, post_count)

    @unittest.skip("Requires Podman 3.1")
    def test_network_prune(self):
        network = self.client.networks.create(
            "integration_test",
            disabled_dns=True,
            enable_ipv6=False,
            ipam=NetworksIntegrationTest.ipam,
        )
        self.assertEqual(network.name, "integration_test")

        report = self.client.networks.prune()
        self.assertIn(network.name, report["NetworksDeleted"])
