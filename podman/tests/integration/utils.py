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

import atexit
import functools
import logging
import os
import shutil
import socket
import subprocess
import tempfile
import threading
from contextlib import suppress

import time

from podman.tests import errors

logger = logging.getLogger("podman.service")


@functools.lru_cache(maxsize=1)
def get_shared_data_path() -> str:
    override = os.environ.get("PODMAN_PY_TEST_DATA")
    if override:
        os.makedirs(override, exist_ok=True)
        return override

    path = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, path, ignore_errors=True)
    return path


class PodmanLauncher:
    """Podman service launcher"""

    def __init__(
        self,
        socket_uri: str,
        podman_path: str | None = None,
        timeout: int = 0,
        privileged: bool = False,
        log_level: str = "WARNING",
        data_path: str | None = None,
    ) -> None:
        """create a launcher and build podman command"""
        podman_exe: str | None = podman_path
        if not podman_exe:
            podman_exe = shutil.which('podman')
        if podman_exe is None:
            raise errors.PodmanNotInstalled()

        self.socket_file: str = socket_uri.replace('unix://', '')
        self.log_level = log_level

        self.proc: subprocess.Popen[bytes] | None = None
        self.reference_id = hash(time.monotonic())

        self.cmd: list[str] = []
        if privileged:
            self.cmd.append('sudo')

        self.cmd.append(podman_exe)

        logger.setLevel(logging.getLevelName(log_level))

        # Map from python to go logging levels, FYI trace level breaks cirrus logging
        self.cmd.append(f"--log-level={log_level.lower()}")

        if os.environ.get("container") == "oci":
            self.cmd.append("--storage-driver=vfs")

        if data_path:
            self.cmd.extend(
                [
                    "--runroot",
                    os.path.join(data_path, "run"),
                    "--root",
                    os.path.join(data_path, "storage"),
                ]
            )

        self.cmd.extend(
            [
                "system",
                "service",
                f"--time={timeout}",
                socket_uri,
            ]
        )

        process = subprocess.run(
            [podman_exe, "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        self.version = str(process.stdout.decode("utf-8")).strip().split()[2]

    def start(self, check_socket=True) -> None:
        """start podman service"""
        logger.info(
            "Launching(%s) %s refid=%s",
            self.version,
            ' '.join(self.cmd),
            self.reference_id,
        )

        def consume_lines(pipe, consume_fn):
            with pipe:
                for line in iter(pipe.readline, b""):
                    consume_fn(line.decode("utf-8"))

        def consume(line: str):
            logger.debug(line.strip("\n") + f" refid={self.reference_id}")

        self.proc = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  # pylint: disable=consider-using-with
        threading.Thread(target=consume_lines, args=[self.proc.stdout, consume]).start()

        if not check_socket:
            return

        # wait for socket to be created and accepting connections
        timeout = time.monotonic() + 30
        while not os.path.exists(self.socket_file):
            if time.monotonic() > timeout:
                raise subprocess.TimeoutExpired("podman service ", timeout)
            time.sleep(0.2)

        while time.monotonic() < timeout:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect(self.socket_file)
                break
            except OSError:
                time.sleep(0.2)
            finally:
                sock.close()
        else:
            raise subprocess.TimeoutExpired("podman service (accepting)", timeout)

    def stop(self) -> None:
        """stop podman service"""
        if not self.proc:
            return

        self.proc.terminate()
        try:
            return_code = self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            return_code = self.proc.wait()
        self.proc = None

        with suppress(FileNotFoundError):
            os.remove(self.socket_file)

        logger.info("Command return Code: %d refid=%s", return_code, self.reference_id)
