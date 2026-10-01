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

import logging
import os
import shutil
import uuid
from typing import Optional

import fixtures

from podman.tests.integration import utils


class IntegrationTest(fixtures.TestWithFixtures):
    """Base Integration test case.

    Notes:
        - Logging for the Podman service configured here for later capture, this configuration is
          inherited by other libraries like unittest and requests.
        - Logging output will start with stdout from the Podman service events, followed by
          results and logging captured by the unittest module test runner.
        - Each test gets its own Podman service and socket.
        - ``self.data_path`` (via ``utils.get_shared_data_path()``) is shared across every test
          in the run.  Podman's ``--root`` (image/container storage) and ``--runroot`` (runtime
          locks and state) are both derived from this directory.  They must share the same
          lifecycle because Podman's runtime locks coordinate access to the storage graph.
          Use ``self.test_dir`` for anything that should stay isolated to a single test.
    """

    podman: Optional[str] = None

    @classmethod
    def setUpClass(cls) -> None:
        super(fixtures.TestWithFixtures, cls).setUpClass()

        command = os.environ.get("PODMAN_BINARY", "podman")
        if shutil.which(command) is None:
            raise AssertionError(f"'{command}' not found.")
        IntegrationTest.podman = command

        # This log_level is for our python code
        log_level = os.environ.get("PODMAN_LOG_LEVEL", "INFO")
        log_level = logging.getLevelName(log_level)
        logging.basicConfig(level=log_level)

    def setUp(self):
        super().setUp()

        self.log_level = os.environ.get("PODMAN_LOG_LEVEL", "INFO")

        # Prefer /run over /tmp: sshd PrivateTmp can hide /tmp from stream-local forwards.
        try:
            self.test_dir = self.useFixture(fixtures.TempDir("/run")).path
        except OSError:
            self.test_dir = self.useFixture(fixtures.TempDir()).path

        self.socket_file = os.path.join(self.test_dir, uuid.uuid4().hex)
        self.socket_uri = f'unix://{self.socket_file}'
        self.data_path = utils.get_shared_data_path()
        self.service_launcher = utils.PodmanLauncher(
            self.socket_uri,
            podman_path=IntegrationTest.podman,
            log_level=self.log_level,
            data_path=self.data_path,
        )
        self.service_launcher.start()
        self.addCleanup(self.service_launcher.stop)
