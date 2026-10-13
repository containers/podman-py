import getpass
import os
import socket
import unittest

import time

from podman import PodmanClient
from podman.tests.integration import base, utils


class AdapterIntegrationTest(base.IntegrationTest):
    def setUp(self):
        super().setUp()

    def _ssh_client_kwargs(self) -> dict:
        identity = os.environ.get("PODMAN_SSH_IDENTITY")
        if identity and os.path.isfile(identity):
            return {"identity": identity}
        return {}

    @staticmethod
    def _free_tcp_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    def test_ssh_ping(self):
        # Stream-local SSH forwards often cannot reach test sockets on CI (sshd/SELinux).
        # Forward to a local TCP podman service instead (ssh -L localsock:127.0.0.1:port).
        ssh_kwargs = self._ssh_client_kwargs()
        port = self._free_tcp_port()
        podman = utils.PodmanLauncher(
            f"tcp:127.0.0.1:{port}",
            podman_path=base.IntegrationTest.podman,
            log_level=self.log_level,
        )
        user = getpass.getuser()
        try:
            podman.start(check_socket=False)
            time.sleep(0.5)

            with PodmanClient(
                base_url=f"http+ssh://{user}@localhost:22?tcp_port={port}",
                **ssh_kwargs,
            ) as client:
                self.assertTrue(client.ping())

            with PodmanClient(
                base_url=f"ssh://{user}@localhost:22?tcp_port={port}",
                **ssh_kwargs,
            ) as client:
                self.assertTrue(client.ping())
        finally:
            podman.stop()

    def test_unix_ping(self):
        with PodmanClient(base_url=f"unix://{self.socket_file}") as client:
            self.assertTrue(client.ping())

        with PodmanClient(base_url=f"http+unix://{self.socket_file}") as client:
            self.assertTrue(client.ping())

    def test_tcp_ping(self):
        podman = utils.PodmanLauncher(
            "tcp:localhost:8889",
            podman_path=base.IntegrationTest.podman,
            log_level=self.log_level,
        )
        try:
            podman.start(check_socket=False)
            time.sleep(0.5)

            with PodmanClient(base_url="tcp:localhost:8889") as client:
                self.assertTrue(client.ping())

            with PodmanClient(base_url="http://localhost:8889") as client:
                self.assertTrue(client.ping())
        finally:
            podman.stop()


if __name__ == '__main__':
    unittest.main()
