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
"""system call integration tests"""

from podman import system
from podman.api_connection import ApiConnection
import podman.tests.integration.base as base


class TestSystem(base.IntegrationTest):
    """system call integration test"""

    def setUp(self):
        super().setUp()
        self.api = ApiConnection(self.socket_uri)
        self.addCleanup(self.api.close)

    def test_info(self):
        """integration: system info call"""
        output = system.info(self.api)
        self.assertTrue('host' in output)

    def test_version(self):
        """integration: system version call"""
        output = system.version(self.api)
        self.assertTrue('Platform' in output)
        self.assertTrue('Version' in output)
        self.assertTrue('ApiVersion' in output)

    def test_show_disk_usage(self):
        """integration: system disk usage call"""
        output = system.show_disk_usage(self.api)
        self.assertTrue('Images' in output)
        self.assertTrue('Containers' in output)
        self.assertTrue('Volumes' in output)
