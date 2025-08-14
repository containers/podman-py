import unittest
import re
import os
import pytest

import podman.tests.integration.base as base
from podman import PodmanClient
from podman.tests.utils import PODMAN_VERSION

# @unittest.skipIf(os.geteuid() != 0, 'Skipping, not running as root')


class ContainersIntegrationTest(base.IntegrationTest):
    """Containers Integration tests."""

    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

        self.alpine_image = self.client.images.pull("quay.io/libpod/alpine", tag="latest")
        self.containers = []

    def tearDown(self):
        for container in self.containers:
            container.remove(force=True)

    def test_container_named_volume_mount(self):
        with self.subTest("Check volume mount"):
            volumes = {
                'test_bind_1': {'bind': '/mnt/vol1', 'mode': 'rw'},
                'test_bind_2': {'bind': '/mnt/vol2', 'extended_mode': ['ro', 'noexec']},
                'test_bind_3': {'bind': '/mnt/vol3', 'extended_mode': ['noexec'], 'mode': 'rw'},
            }
            container = self.client.containers.create(self.alpine_image, volumes=volumes)
            container_mounts = container.attrs.get('Mounts', {})
            self.assertEqual(len(container_mounts), len(volumes))

            for mount in container_mounts:
                name = mount.get('Name')
                self.assertIn(name, volumes)
                test_mount = volumes.get(name)
                test_mode = test_mount.get('mode', '')
                test_extended_mode = test_mount.get('extended_mode', [])
                # check RO/RW
                if 'ro' in test_mode or 'ro' in test_extended_mode:
                    self.assertEqual(mount.get('RW'), False)

                if 'rw' in test_mode or 'rw' in test_extended_mode:
                    self.assertEqual(mount.get('RW'), True)

                other_options = [o for o in test_extended_mode if o not in ['ro', 'rw']]
                for o in other_options:
                    self.assertIn(o, mount.get('Options'))

    def test_container_directory_volume_mount(self):
        """Test that directories can be mounted with the ``volume`` parameter."""
        with self.subTest("Check bind mount"):
            volumes = {
                "/etc/hosts": dict(bind="/test_ro", mode='ro'),
                "/etc/hosts": dict(bind="/test_rw", mode='rw'),  # noqa: F601
            }
            container = self.client.containers.create(
                self.alpine_image, command=["cat", "/test_ro", "/test_rw"], volumes=volumes
            )
            container_mounts = container.attrs.get('Mounts', {})
            self.assertEqual(len(container_mounts), len(volumes))

            self.containers.append(container)

            for directory, mount_spec in volumes.items():
                self.assertIn(
                    f"{directory}:{mount_spec['bind']}:{mount_spec['mode']},rprivate,rbind",
                    container.attrs.get('HostConfig', {}).get('Binds', list()),
                )

            # check if container can be started and exits with EC == 0
            container.start()
            container.wait()

            self.assertEqual(container.attrs.get('State', dict()).get('ExitCode', 256), 0)

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

    def test_container_environment_variables(self):
        """Test environment variables passed to the container."""
        with self.subTest("Check environment variables as dictionary"):
            env_dict = {"MY_VAR": "123", "ANOTHER_VAR": "456"}
            container = self.client.containers.create(
                self.alpine_image, command=["env"], environment=env_dict
            )
            self.containers.append(container)

            container_env = container.attrs.get('Config', {}).get('Env', [])
            for key, value in env_dict.items():
                self.assertIn(f"{key}={value}", container_env)

            container.start()
            container.wait()
            logs = b"\n".join(container.logs()).decode()

            for key, value in env_dict.items():
                self.assertIn(f"{key}={value}", logs)

        with self.subTest("Check environment variables as list"):
            env_list = ["MY_VAR=123", "ANOTHER_VAR=456"]
            container = self.client.containers.create(
                self.alpine_image, command=["env"], environment=env_list
            )
            self.containers.append(container)

            container_env = container.attrs.get('Config', {}).get('Env', [])
            for env in env_list:
                self.assertIn(env, container_env)

            container.start()
            container.wait()
            logs = b"\n".join(container.logs()).decode()

            for env in env_list:
                self.assertIn(env, logs)

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

    def test_container_ports(self):
        """Test ports binding"""
        port_tests = [
            {
                'input': {'97/tcp': '43'},
                'expected_output': {'97/tcp': [{'HostIp': '', 'HostPort': '43'}]},
            },
            {
                'input': {'2/udp': ('127.0.0.1', '939')},
                'expected_output': {'2/udp': [{'HostIp': '127.0.0.1', 'HostPort': '939'}]},
            },
            {
                'input': {
                    '11123/tcp': [('127.0.0.1', '11123'), ('127.0.0.1', '112'), '1123', '159']
                },
                'expected_output': {
                    '11123/tcp': [
                        {'HostIp': '127.0.0.1', 'HostPort': '11123'},
                        {'HostIp': '', 'HostPort': '112'},
                        {'HostIp': '', 'HostPort': '1123'},
                        {'HostIp': '', 'HostPort': '159'},
                    ]
                },
            },
            {
                'input': {'1111/tcp': {"port": ('127.0.0.1', 1111), "range": 3}},
                'expected_output': {
                    '1111/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '1111'}],
                    '1112/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '1112'}],
                    '1113/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '1113'}],
                },
            },
            {
                'input': {
                    '1222/tcp': [{"port": 1234, "range": 2}, {"ip": "127.0.0.1", "port": 4567}]
                },
                'expected_output': {
                    '1222/tcp': [
                        {'HostIp': '', 'HostPort': '1234'},
                        {'HostIp': '127.0.0.1', 'HostPort': '4567'},
                    ],
                    '1223/tcp': [{'HostIp': '', 'HostPort': '1235'}],
                },
            },
            {
                'input': {
                    2244: 3344,
                },
                'expected_output': {
                    '2244/tcp': [
                        {'HostIp': '', 'HostPort': '3344'},
                    ],
                },
            },
        ]

        for port_test in port_tests:
            container = self.client.containers.create(self.alpine_image, ports=port_test['input'])
            self.containers.append(container)

            self.assertTrue(
                all(
                    [
                        x in port_test['expected_output']
                        for x in container.attrs.get('HostConfig', {}).get('PortBindings')
                    ]
                )
            )

    def test_container_dns_option(self):
        expected_dns_opt = ['edns0']

        container = self.client.containers.create(
            self.alpine_image, command=["cat", "/etc/resolv.conf"], dns_opt=expected_dns_opt
        )
        self.containers.append(container)

        with self.subTest("Check HostConfig"):
            self.assertEqual(
                container.attrs.get('HostConfig', {}).get('DnsOptions'), expected_dns_opt
            )

        with self.subTest("Check content of /etc/resolv.conf"):
            container.start()
            container.wait()
            self.assertTrue(
                all([opt in b"\n".join(container.logs()).decode() for opt in expected_dns_opt])
            )

    def test_container_healthchecks(self):
        """Test passing various healthcheck options"""
        parameters = {
            'healthcheck': {'Test': ['CMD-SHELL curl http://localhost || exit']},
            'health_check_on_failure_action': 1,
        }
        container = self.client.containers.create(self.alpine_image, **parameters)
        self.containers.append(container)

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

    @pytest.mark.skipif(os.geteuid() != 0, reason='Skipping, not running as root')
    @pytest.mark.skipif(
        PODMAN_VERSION >= (5, 6, 0),
        reason="Test against this feature in Podman 5.6.0  or greater https://github.com/containers/podman/pull/25942",
    )
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

        with self.subTest("Check uppercase mount option attributes"):
            mount = {
                "TypE": "bind",
                "SouRce": "/etc/hosts",
                "TarGet": "/test",
                "Read_Only": True,
                "ReLabel": "Z",
            }
            container = self.client.containers.create(
                self.alpine_image, command=["cat", "/test"], mounts=[mount]
            )
            self.containers.append(container)
            self.assertIn(
                f"{mount['SouRce']}:{mount['TarGet']}:ro,Z,rprivate,rbind",
                container.attrs.get('HostConfig', {}).get('Binds', list()),
            )

            # check if container can be started and exits with EC == 0
            container.start()
            container.wait()

            self.assertEqual(container.attrs.get('State', dict()).get('ExitCode', 256), 0)

    @pytest.mark.skipif(os.geteuid() != 0, reason='Skipping, not running as root')
    @pytest.mark.skipif(
        PODMAN_VERSION < (5, 6, 0),
        reason="Test against this feature before Podman 5.6.0 https://github.com/containers/podman/pull/25942",
    )
    def test_container_mounts_without_rw_as_default(self):
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
                f"size={mount['size']},rprivate,nosuid,nodev,tmpcopyup",
            )

    def test_container_devices(self):
        devices = ["/dev/null:/dev/foo", "/dev/zero:/dev/bar"]
        container = self.client.containers.create(
            self.alpine_image, devices=devices, command=["ls", "-l", "/dev/"]
        )
        self.containers.append(container)

        container_devices = container.attrs.get('HostConfig', {}).get('Devices', [])
        with self.subTest("Check devices in container object"):
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

        with self.subTest("Check devices in running container object"):
            container.start()
            container.wait()

            logs = b"\n".join(container.logs()).decode()

            device_regex = r'(\d+, *?\d+).*?{}\n'

            for device in devices:
                # check whether device exists
                source_device, destination_device = device.split(':', 1)
                source_match = re.search(
                    device_regex.format(source_device.rsplit("/", 1)[-1]), logs
                )
                destination_match = re.search(
                    device_regex.format(destination_device.rsplit("/", 1)[-1]), logs
                )

                self.assertIsNotNone(source_match)
                self.assertIsNotNone(destination_match)

                # validate if proper device was added (by major/minor numbers)
                self.assertEqual(source_match.group(1), destination_match.group(1))

    def test_read_write_tmpfs(self):
        test_cases = [
            {"read_write_tmpfs": True, "failed_container": False},
            {
                "read_write_tmpfs": False,
                "failed_container": True,
                "expected_output": "Read-only file system",
            },
            {
                "read_write_tmpfs": None,
                "failed_container": True,
                "expected_output": "Read-only file system",
            },
        ]

        for test in test_cases:
            read_write_tmpfs = test.get('read_write_tmpfs')
            with self.subTest(f"Check read_write_tmpfs set to {read_write_tmpfs}"):
                kwargs = (
                    {"read_write_tmpfs": read_write_tmpfs} if read_write_tmpfs is not None else {}
                )
                container = self.client.containers.create(
                    self.alpine_image,
                    read_only=True,
                    command=["/bin/touch", "/tmp/test_file"],
                    **kwargs,
                )

                self.containers.append(container)

                container.start()
                container.wait()

                inspect = container.inspect()
                logs = b"\n".join(container.logs(stderr=True)).decode()

                if test.get("failed_container") is True:
                    self.assertNotEqual(inspect.get("State", {}).get("ExitCode", -1), 0)
                else:
                    self.assertEqual(inspect.get("State", {}).get("ExitCode", -1), 0)

                expected_output = test.get("expected_output")
                if expected_output:
                    print(inspect)
                    self.assertIn(expected_output, logs)


if __name__ == '__main__':
    unittest.main()
