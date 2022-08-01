import unittest

import re

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
            formatted_hosts = [f"{ip}\t{hosts}" for hosts, ip in extra_hosts.items()]
            for hosts_entry in formatted_hosts:
                self.assertIn(hosts_entry, logs)

    def _test_memory_limit(self, parameter_name, host_config_name, set_mem_limit=False):
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
            parameters = {parameter_name: test['value']}
            if set_mem_limit:
                parameters['mem_limit'] = test['expected_value'] - 100

            container = self.client.containers.create(self.alpine_image, **parameters)
            self.containers.append(container)
            self.assertEqual(
                container.attrs.get('HostConfig', dict()).get(host_config_name),
                test['expected_value'],
            )

    def test_container_mem_limit(self):
        """Test passing memory limit"""
        self._test_memory_limit('mem_limit', 'Memory')

    def test_container_memswap_limit(self):
        """Test passing memory swap limit"""
        self._test_memory_limit('memswap_limit', 'MemorySwap', set_mem_limit=True)

    def test_container_mem_reservation(self):
        """Test passing memory reservation"""
        self._test_memory_limit('mem_reservation', 'MemoryReservation')

    def test_container_shm_size(self):
        """Test passing shared memory size"""
        self._test_memory_limit('shm_size', 'ShmSize')

    def test_container_mounts(self):
        """Test passing mounts"""
        with self.subTest("Check bind mount"):
            mount = {
                "type": "bind",
                "source": "/etc/hosts",
                "target": "/test",
                "read_only": True,
                "relabel": "Z",
            }
            container = self.client.containers.create(
                self.alpine_image, command=["cat", "/test"], mounts=[mount]
            )
            self.containers.append(container)
            self.assertIn(
                f"{mount['source']}:{mount['target']}:ro,Z,rprivate,rbind",
                container.attrs.get('HostConfig', {}).get('Binds', list()),
            )

            # check if container can be started and exits with EC == 0
            container.start()
            container.wait()

            self.assertEqual(container.attrs.get('State', dict()).get('ExitCode', 256), 0)

        with self.subTest("Check tmpfs mount"):
            mount = {"type": "tmpfs", "source": "tmpfs", "target": "/test", "size": "456k"}
            container = self.client.containers.create(
                self.alpine_image, command=["df", "-h"], mounts=[mount]
            )
            self.containers.append(container)
            self.assertEqual(
                container.attrs.get('HostConfig', {}).get('Tmpfs', {}).get(mount['target']),
                f"size={mount['size']},rw,rprivate,nosuid,nodev,tmpcopyup",
            )

            container.start()
            container.wait()

            logs = b"\n".join(container.logs()).decode()

            self.assertTrue(
                re.search(
                    rf"{mount['size'].replace('k', '.0K')}.*?{mount['target']}",
                    logs,
                    flags=re.MULTILINE,
                )
            )

    def test_container_devices(self):
        devices = ["/dev/null:/dev/foo", "/dev/zero:/dev/bar"]
        container = self.client.containers.create(self.alpine_image, devices=devices)
        self.containers.append(container)

        container_devices = container.attrs.get('HostConfig', {}).get('Devices', [])
        for device in devices:
            path_on_host, path_in_container = device.split(':', 1)
            self.assertTrue(
                any(
                    [
                        c.get('PathOnHost') == path_on_host
                        and c.get('PathInContainer') == path_in_container
                        for c in container_devices
                    ]
                )
            )


if __name__ == '__main__':
    unittest.main()
