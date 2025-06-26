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
"""Integration Test Utils"""

import logging
import os
import shutil
import subprocess
import threading
from contextlib import suppress
from typing import Optional

import time

from podman import PodmanCommand

logger = logging.getLogger("podman.service")


class PodmanLauncher:
    """Podman service launcher"""

    def __init__(
        self,
        socket_uri: str,
        podman_path: Optional[str] = None,
        timeout: int = 0,
        privileged: bool = False,
        log_level: str = "WARNING",
    ) -> None:
        """create a launcher and build podman command"""
        self.podman = PodmanCommand(path=podman_path, privileged=privileged)

        self.timeout = timeout
        self.socket_uri: str = socket_uri
        self.socket_file: str = socket_uri.replace('unix://', '')
        self.log_level = log_level

        self.proc: Optional[subprocess.Popen[bytes]] = None
        self.reference_id = hash(time.monotonic())

        logger.setLevel(logging.getLevelName(log_level))

        # Map from python to go logging levels, FYI trace level breaks cirrus logging
        self.podman.options.log_level = log_level.lower()
        if os.environ.get("container") == "oci":
            self.podman.options.storage_driver = "vfs"

        self.version = self.podman.run(["--version"]).split()[2]

    def start(self, check_socket=True) -> None:
        """start podman service"""

        def consume_lines(pipe, consume_fn):
            with pipe:
                for line in iter(pipe.readline, b""):
                    consume_fn(line.decode("utf-8"))

        def consume(line: str):
            logger.debug(line.strip("\n") + f" refid={self.reference_id}")

        self.proc = self.podman.start_service(
            self.socket_uri,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        logger.info(
            "Launched(%s) %s pid=%s refid=%s",
            self.version,
            ' '.join(self.proc.args),
            self.proc.pid,
            self.reference_id,
        )

        threading.Thread(target=consume_lines, args=[self.proc.stdout, consume]).start()

        if not check_socket:
            return

        # wait for socket to be created
        self.podman.wait_for_service(self.socket_uri, self.proc, timeout=30)

    def stop(self) -> None:
        """stop podman service"""
        if not self.proc:
            return

        return_code = self.podman.stop_service(self.proc, timeout=15)
        with suppress(FileNotFoundError):
            os.remove(self.socket_file)

        logger.info("Command return Code: %d refid=%s", return_code, self.reference_id)
