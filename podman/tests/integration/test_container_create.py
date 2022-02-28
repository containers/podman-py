import unittest

import podman.tests.integration.base as base
from podman import PodmanClient


# @unittest.skipIf(os.geteuid() != 0, 'Skipping, not running as root')


class ContainersIntegrationTest(base.IntegrationTest):
    """Containers Integration tests."""

    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

        self.alpine_image = self.client.images.pull("quay.io/libpod/alpine", tag="latest")
        self.containers = []

    def tearUp(self):
        for container in self.containers:
            container.remove(force=True)

    def test_container_extra_hosts(self):
        """Test Container Extra hosts"""
        extra_hosts = {"host1 host3": "127.0.0.2", "host2": "127.0.0.3"}

        with self.subTest("Check extra hosts in container object"):
            proper_container = self.client.containers.create(
                self.alpine_image, command=["cat", "/etc/hosts"], extra_hosts=extra_hosts
            )
            self.containers.append(proper_container)
            formatted_hosts = [f"{hosts}:{ip}" for hosts, ip in extra_hosts.items()]
            self.assertEqual(
                proper_container.attrs.get('HostConfig', dict()).get('ExtraHosts', list()),
                formatted_hosts,
            )

        with self.subTest("Check extra hosts in running container"):
            proper_container.start()
            proper_container.wait()
            logs = b"\n".join(proper_container.logs()).decode()
            formatted_hosts = [f"{ip} {hosts}" for hosts, ip in extra_hosts.items()]
            for hosts_entry in formatted_hosts:
                self.assertIn(hosts_entry, logs)

    def _test_memory_limit(self, parameter_name, host_config_name):
        """Base for tests which checks memory limits"""
        memory_limit_tests = [
            {'value': 1000, 'expected_value': 1000},
            {'value': '1000', 'expected_value': 1000},
            {'value': '1234b', 'expected_value': 1234},
            {'value': '123k', 'expected_value': 123 * 1024},
            {'value': '44m', 'expected_value': 44 * 1024 * 1024},
            {'value': '2g', 'expected_value': 2 * 1024 * 1024 * 1024},
        ]

        for test in memory_limit_tests:
            container = self.client.containers.create(
                self.alpine_image, **{parameter_name: test['value']}
            )
            self.containers.append(container)
            self.assertEqual(
                container.attrs.get('HostConfig', dict()).get(host_config_name),
                test['expected_value'],
            )

    def test_container_mem_limit(self):
        """Test passing memory limit"""
        self._test_memory_limit('mem_limit', 'Memory')

    def test_container_mem_reservation(self):
        """Test passing memory reservation"""
        self._test_memory_limit('mem_reservation', 'MemoryReservation')

    def test_container_shm_size(self):
        """Test passing shared memory size"""
        self._test_memory_limit('shm_size', 'ShmSize')


if __name__ == '__main__':
    unittest.main()
