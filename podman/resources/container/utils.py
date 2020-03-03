import copy
import ntpath
from collections import namedtuple

from podman.errors import create_unexpected_kwargs_error
from podman.types import HostConfig

# kwargs to copy straight from run to create
RUN_CREATE_KWARGS = [
    'command',
    'detach',
    'domainname',
    'entrypoint',
    'environment',
    'healthcheck',
    'hostname',
    'image',
    'labels',
    'mac_address',
    'name',
    'network_disabled',
    'stdin_open',
    'stop_signal',
    'tty',
    'use_config_proxy',
    'user',
    'working_dir',
]

# kwargs to copy straight from run to host_config
RUN_HOST_CONFIG_KWARGS = [
    'auto_remove',
    'blkio_weight_device',
    'blkio_weight',
    'cap_add',
    'cap_drop',
    'cgroup_parent',
    'cpu_count',
    'cpu_percent',
    'cpu_period',
    'cpu_quota',
    'cpu_shares',
    'cpuset_cpus',
    'cpuset_mems',
    'cpu_rt_period',
    'cpu_rt_runtime',
    'device_cgroup_rules',
    'device_read_bps',
    'device_read_iops',
    'device_write_bps',
    'device_write_iops',
    'devices',
    'dns_opt',
    'dns_search',
    'dns',
    'extra_hosts',
    'group_add',
    'init',
    'init_path',
    'ipc_mode',
    'isolation',
    'kernel_memory',
    'links',
    'log_config',
    'lxc_conf',
    'mem_limit',
    'mem_reservation',
    'mem_swappiness',
    'memswap_limit',
    'mounts',
    'nano_cpus',
    'network_mode',
    'oom_kill_disable',
    'oom_score_adj',
    'pid_mode',
    'pids_limit',
    'privileged',
    'publish_all_ports',
    'read_only',
    'restart_policy',
    'security_opt',
    'shm_size',
    'storage_opt',
    'sysctls',
    'tmpfs',
    'ulimits',
    'userns_mode',
    'uts_mode',
    'version',
    'volume_driver',
    'volumes_from',
    'runtime'
]


def _create_container_args(kwargs):
    """
    Convert arguments to create() to arguments to create_container().
    """
    # Copy over kwargs which can be copied directly
    create_kwargs = {}
    for key in copy.copy(kwargs):
        if key in RUN_CREATE_KWARGS:
            create_kwargs[key] = kwargs.pop(key)
    host_config_kwargs = {}
    for key in copy.copy(kwargs):
        if key in RUN_HOST_CONFIG_KWARGS:
            host_config_kwargs[key] = kwargs.pop(key)

    # Process kwargs which are split over both create and host_config
    ports = kwargs.pop('ports', {})
    if ports:
        host_config_kwargs['port_bindings'] = ports

    volumes = kwargs.pop('volumes', {})
    if volumes:
        host_config_kwargs['binds'] = volumes

    network = kwargs.pop('network', None)
    if network:
        create_kwargs['networking_config'] = {network: None}
        host_config_kwargs['network_mode'] = network

    # All kwargs should have been consumed by this point, so raise
    # error if any are left
    if kwargs:
        raise create_unexpected_kwargs_error('run', kwargs)

    create_kwargs['host_config'] = HostConfig(**host_config_kwargs)

    # Fill in any kwargs which need processing by create_host_config first
    port_bindings = create_kwargs['host_config'].get('PortBindings')
    if port_bindings:
        # sort to make consistent for tests
        create_kwargs['ports'] = [tuple(p.split('/', 1))
                                  for p in sorted(port_bindings.keys())]
    if volumes:
        if isinstance(volumes, dict):
            create_kwargs['volumes'] = [
                v.get('bind') for v in volumes.values()
            ]
        else:
            create_kwargs['volumes'] = [
                _host_volume_from_bind(v) for v in volumes
            ]
    return create_kwargs


def _host_volume_from_bind(bind):
    drive, rest = ntpath.splitdrive(bind)
    bits = rest.split(':', 1)
    if len(bits) == 1 or bits[1] in ('ro', 'rw'):
        return drive + bits[0]
    else:
        return bits[1].rstrip(':ro').rstrip(':rw')


ExecResult = namedtuple('ExecResult', 'exit_code,output')
""" A result of Container.exec_run with the properties ``exit_code`` and
    ``output``. """
