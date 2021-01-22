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
"""Base integration test code"""


import unittest
import shutil
import uuid
import os
import fixtures
import podman.tests.integration.utils as utils


@unittest.skipIf(
    shutil.which('podman') is None, "podman is not installed, skipping integration tests"
)
class BaseIntegrationTest(fixtures.TestWithFixtures):
    """Base Integration test case"""

    def setUp(self):
        super().setUp()
        self.test_dir = self.useFixture(fixtures.TempDir()).path
        self.socket_file = os.path.join(self.test_dir, uuid.uuid4().hex)
        self.socket_uri = 'unix://{}'.format(self.socket_file)
        self.service_launcher = utils.PodmanLauncher(self.socket_uri)
        self.service_launcher.start()
        self.addCleanup(self.service_launcher.stop)
