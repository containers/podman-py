import getpass
import unittest

import time

from podman import PodmanClient
from podman.tests.integration import base, utils


class AdapterIntegrationTest(base.IntegrationTest):
    def setUp(self):
        super().setUp()

    def test_ssh_ping(self):
        with PodmanClient(
            base_url=f"http+ssh://{getpass.getuser()}@localhost:22{self.socket_file}"
        ) as client:
            self.assertTrue(client.ping())

        with PodmanClient(
            base_url=f"ssh://{getpass.getuser()}@localhost:22{self.socket_file}"
        ) as client:
            self.assertTrue(client.ping())

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
