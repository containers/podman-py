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
from podman import networks
from podman.api_connection import ApiConnection
import podman.tests.integration.base as base


@unittest.skipIf(os.geteuid() != 0, 'Skipping, not running as root')
class TestNetworks(base.BaseIntegrationTest):
    """networks call integration test"""

    def setUp(self):
        super().setUp()
        self.api = ApiConnection(self.socket_uri)
        self.addCleanup(self.api.close)

    @unittest.skip('not implemented yet')
    def test_network_create_remove(self):
        """integration: networks create and remove calls"""

    def test_inspect(self):
        """integration: networks inspect call"""
        output = networks.inspect(self.api, 'podman')
        self.assertEqual('', output)

    def test_list_networks(self):
        """integration: networks list_networks call"""
        output = networks.list_networks(self.api)
        self.assertTrue(len(output) > 0)
