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
"""images call integration tests"""


from podman import images
from podman.api_connection import ApiConnection
import podman.tests.integration.base as base


# @unittest.skipIf(os.geteuid() != 0, 'Skipping, not running as root')
class TestImages(base.BaseIntegrationTest):
    """images call integration test"""

    def setUp(self):
        super().setUp()
        self.api = ApiConnection(self.socket_uri)
        self.addCleanup(self.api.close)

    def test_list_images(self):
        """integration: images list call"""
        output = images.list_images(self.api)
        self.assertTrue(isinstance(output, list))
