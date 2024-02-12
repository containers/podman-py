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

import podman.tests.integration.base as base
from podman import PodmanClient
from podman.errors import APIError


class SystemIntegrationTest(base.IntegrationTest):
    """system call integration test"""

    def setUp(self):
        super().setUp()
        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

    def test_info(self):
        """integration: system info call"""
        output = self.client.info()
        self.assertTrue('host' in output)

    def test_version(self):
        """integration: system version call"""
        output = self.client.version()
        self.assertTrue('Platform' in output)
        self.assertTrue('Version' in output)
        self.assertTrue('ApiVersion' in output)

    def test_show_disk_usage(self):
        """integration: system disk usage call"""
        output = self.client.df()
        self.assertTrue('Images' in output)
        self.assertTrue('Containers' in output)
        self.assertTrue('Volumes' in output)

    def test_login(self):
        """integration: system login call"""
        # here, we just test the sanity of the endpoint
        # confirming that we get through to podman, and get tcp rejected.
        with self.assertRaises(APIError) as e:
            next(
                self.client.login(
                    "fake_user", "fake_password", "fake_email@fake_domain.test", "fake_registry"
                )
            )
        self.assertRegex(
            e.exception.explanation,
            r"lookup fake_registry.+no such host",
        )

    def test_from_env(self):
        """integration: from_env() no error"""
        PodmanClient.from_env()
