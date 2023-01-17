"""Mixin to provide Container create() method."""
import copy
import logging
import re
from contextlib import suppress
from typing import Any, Dict, List, MutableMapping, Union

from podman import api
from podman.domain.containers import Container
from podman.domain.images import Image
from podman.domain.pods import Pod
from podman.errors import ImageNotFound

logger = logging.getLogger("podman.containers")


class CreateMixin:  # pylint: disable=too-few-public-methods
    """Class providing create method for ContainersManager."""

    def create(
        self, image: Union[Image, str], command: Union[str, List[str], None] = None, **kwargs
    ) -> Container:
        """Create a container.

        Args:
            image: Image to run.
            command: Command to run in the container.

        Keyword Args:
            auto_remove (bool): Enable auto-removal of the container on daemon side when the
                container's process exits.
            blkio_weight_device (Dict[str, Any]): Block IO weight (relative device weight)
                in the form of: [{"Path": "device_path", "Weight": weight}].
            blkio_weight (int): Block IO weight (relative weight), accepts a weight value
                between 10 and 1000.
            cap_add (List[str]): Add kernel capabilities. For example: ["SYS_ADMIN", "MKNOD"]
            cap_drop (List[str]): Drop kernel capabilities.
            cgroup_parent (str): Override the default parent cgroup.
            cpu_count (int): Number of usable CPUs (Windows only).
            cpu_percent (int): Usable percentage of the available CPUs (Windows only).
            cpu_period (int): The length of a CPU period in microseconds.
            cpu_quota (int): Microseconds of CPU time that the container can get in a CPU period.
            cpu_rt_period (int): Limit CPU real-time period in microseconds.
            cpu_rt_runtime (int): Limit CPU real-time runtime in microseconds.
            cpu_shares (int): CPU shares (relative weight).
            cpuset_cpus (str): CPUs in which to allow execution (0-3, 0,1).
            cpuset_mems (str): Memory nodes (MEMs) in which to allow execution (0-3, 0,1).
                Only effective on NUMA systems.
            detach (bool): Run container in the background and return a Container object.
            device_cgroup_rules (List[str]): A list of cgroup rules to apply to the container.
            device_read_bps: Limit read rate (bytes per second) from a device in the form of:
                `[{"Path": "device_path", "Rate": rate}]`
            device_read_iops: Limit read rate (IO per second) from a device.
            device_write_bps: Limit write rate (bytes per second) from a device.
            device_write_iops: Limit write rate (IO per second) from a device.
            devices (List[str]): Expose host devices to the container, as a List[str] in the form
                <path_on_host>:<path_in_container>:<cgroup_permissions>.

                For example:
                    /dev/sda:/dev/xvda:rwm allows the container to have read-write access to the
                    host's /dev/sda via a node named /dev/xvda inside the container.

            dns (List[str]): Set custom DNS servers.
            dns_opt (List[str]): Additional options to be added to the container's resolv.conf file.
            dns_search (List[str]): DNS search domains.
            domainname (Union[str, List[str]]): Set custom DNS search domains.
            entrypoint (Union[str, List[str]]): The entrypoint for the container.
            environment (Union[Dict[str, str], List[str]): Environment variables to set inside
                the container, as a dictionary or a List[str] in the format
                ["SOMEVARIABLE=xxx", "SOMEOTHERVARIABLE=xyz"].
            extra_hosts (Dict[str, str]): Additional hostnames to resolve inside the container,
                as a mapping of hostname to IP address.
            group_add (List[str]): List of additional group names and/or IDs that the container
                process will run as.
            healthcheck (Dict[str,Any]): Specify a test to perform to check that the
                container is healthy.
            health_check_on_failure_action (int): Specify an action if a healthcheck fails.
            hostname (str): Optional hostname for the container.
            init (bool): Run an init inside the container that forwards signals and reaps processes
            init_path (str): Path to the docker-init binary
            ipc_mode (str): Set the IPC mode for the container.
            isolation (str): Isolation technology to use. Default: `None`.
            kernel_memory (int or str): Kernel memory limit
            labels (Union[Dict[str, str], List[str]): A dictionary of name-value labels (e.g.
                {"label1": "value1", "label2": "value2"}) or a list of names of labels to set
                with empty values (e.g. ["label1", "label2"])
            links (Optional[Dict[str, str]]): Mapping of links using the {'container': 'alias'}
                format. The alias is optional. Containers declared in this dict will be linked to
                the new container using the provided alias. Default: None.
            log_config (LogConfig): Logging configuration.
            lxc_config (Dict[str, str]): LXC config.
            mac_address (str): MAC address to assign to the container.
            mem_limit (Union[int, str]): Memory limit. Accepts float values (which represent the
                memory limit of the created container in bytes) or a string with a units
                identification char (100000b, 1000k, 128m, 1g). If a string is specified without
                a units character, bytes are assumed as an intended unit.
            mem_reservation (Union[int, str]): Memory soft limit.
            mem_swappiness (int): Tune a container's memory swappiness behavior. Accepts number
                between 0 and 100.
            memswap_limit (Union[int, str]): Maximum amount of memory + swap a container is allowed
                to consume.
            mounts (List[Mount]): Specification for mounts to be added to the container. More
                powerful alternative to volumes. Each item in the list is expected to be a
                Mount object.
                For example :
                 [
                    {
                        "type": "bind",
                        "source": "/a/b/c1",
                        "target" "/d1",
                        "read_only": True,
                        "relabel": "Z"
                    },
                    {
                        "type": "tmpfs",
                        "source": "tmpfs", # If this was not passed, the regular directory
                                           # would be created rather than tmpfs mount !!!
                                           # as this will cause to have invalid entry
                                           # in /proc/self/mountinfo
                        "target" "/d2",
                        "size": "100k",
                        "chown": True
                    }
                ]

            name (str): The name for this container.
            nano_cpus (int):  CPU quota in units of 1e-9 CPUs.
            networks (Dict[str, Dict[str, Union[str, List[str]]):
                Networks which will be connected to container during container creation
                Values of the network configuration can be :
                     - string
                     - list of strings (e.g. Aliases)
            network_disabled (bool): Disable networking.
            network_mode (str): One of:

                - bridge: Create a new network stack for the container
                  on the bridge network.
                - none: No networking for this container.
                - container:<name|id>: Reuse another container's network
                  stack.
                - host: Use the host network stack.

                Incompatible with network.
            oom_kill_disable (bool): Whether to disable OOM killer.
            oom_score_adj (int): An integer value containing the score given to the container in
                order to tune OOM killer preferences.
            pid_mode (str): If set to host, use the host PID namespace
                inside the container.
            pids_limit (int): Tune a container's pids limit. Set -1 for unlimited.
            platform (str): Platform in the format os[/arch[/variant]]. Only used if the method
                needs to pull the requested image.
            ports (Dict[str, Union[int, Tuple[str, int], List[int],
                                   Dict[str, Union[int, Tuple[str, int], List[int]]]]]
                  ): Ports to bind inside the container.

                The keys of the dictionary are the ports to bind inside the container, either as an
                integer or a string in the form port/protocol, where the protocol is either
                tcp, udp, or sctp.

                The values of the dictionary are the corresponding ports to open on the host,
                which can be either:

                - The port number, as an integer.
                    For example: {'2222/tcp': 3333} will expose port 2222 inside the container
                    as port 3333 on the host.
                - None, to assign a random host port.
                    For example: {'2222/tcp': None}.
                - A tuple of (address, port) if you want to specify the host interface.
                    For example: {'1111/tcp': ('127.0.0.1', 1111)}.
                - A list of integers or tuples of (address, port), if you want to bind
                  multiple host ports to a single container port.
                    For example: {'1111/tcp': [1234, ("127.0.0.1", 4567)]}.

                    For example: {'9090': 7878, '10932/tcp': '8781',
                                  "8989/tcp": ("127.0.0.1", 9091)}
                - A dictionary of the options mentioned above except for random host port.
                  The dictionary has additional option "range",
                    which allows binding range of ports.

                    For example:
                        - {'2222/tcp': {"port": 3333, "range": 4}}
                        - {'1111/tcp': {"port": ('127.0.0.1', 1111), "range": 4}}
                        - {'1111/tcp': [
                              {"port": 1234, "range": 4},
                              {"ip": "127.0.0.1", "port": 4567}
                            ]
                          }

            privileged (bool): Give extended privileges to this container.
            publish_all_ports (bool): Publish all ports to the host.
            read_only (bool): Mount the container's root filesystem as read only.
            remove (bool): Remove the container when it has finished running. Default: False.
            restart_policy (Dict[str, Union[str, int]]): Restart the container when it exits.
                Configured as a dictionary with keys:

                - Name: One of on-failure, or always.
                - MaximumRetryCount: Number of times to restart the container on failure.

                For example: {"Name": "on-failure", "MaximumRetryCount": 5}

            runtime (str): Runtime to use with this container.
            security_opt (List[str]): A List[str]ing values to customize labels for MLS systems,
                such as SELinux.
            shm_size (Union[str, int]): Size of /dev/shm (e.g. 1G).
            stdin_open (bool): Keep STDIN open even if not attached.
            stdout (bool): Return logs from STDOUT when detach=False. Default: True.
            stderr (bool): Return logs from STDERR when detach=False. Default: False.
            stop_signal (str): The stop signal to use to stop the container (e.g. SIGINT).
            storage_opt (Dict[str, str]): Storage driver options per container as a
                key-value mapping.
            stream (bool): If true and detach is false, return a log generator instead of a string.
                Ignored if detach is true. Default: False.
            sysctls (Dict[str, str]): Kernel parameters to set in the container.
            tmpfs (Dict[str, str]): Temporary filesystems to mount, as a dictionary mapping a
                path inside the container to options for that path.

                For example: {'/mnt/vol2': '', '/mnt/vol1': 'size=3G,uid=1000'}

            tty (bool): Allocate a pseudo-TTY.
            ulimits (List[Ulimit]): Ulimits to set inside the container.
            use_config_proxy (bool): If True, and if the docker client configuration
                file (~/.config/containers/config.json by default) contains a proxy configuration,
                the corresponding environment variables will be set in the container being built.
            user (Union[str, int]): Username or UID to run commands as inside the container.
            userns_mode (str): Sets the user namespace mode for the container when user namespace
                remapping option is enabled. Supported values are: host
            uts_mode (str): Sets the UTS namespace mode for the container.
                Supported values are: host
            version (str): The version of the API to use. Set to auto to automatically detect
                the server's version. Default: 3.0.0
            volume_driver (str): The name of a volume driver/plugin.
            volumes (Dict[str, Dict[str, Union[str, list]]]): A dictionary to configure
                volumes mounted inside the container.
                The key is either the host path or a volume name, and the value is
                a dictionary with the keys:

                - bind: The path to mount the volume inside the container
                - mode: Either rw to mount the volume read/write, or ro to mount it read-only.
                        Kept for docker-py compatibility
                - extended_mode: List of options passed to volume mount.

                For example:

                    {
                        'test_bind_1':
                            {'bind': '/mnt/vol1', 'mode': 'rw'},
                        'test_bind_2':
                            {'bind': '/mnt/vol2', 'extended_mode': ['ro', 'noexec']},
                         'test_bind_3':
                            {'bind': '/mnt/vol3', 'extended_mode': ['noexec'], 'mode': 'rw'}
                    }

            volumes_from (List[str]): List of container names or IDs to get volumes from.
            working_dir (str): Path to the working directory.

        Returns:
            A Container object.

        Raises:
            ImageNotFound: when Image not found by Podman service
            APIError: when Podman service reports an error
        """
        if isinstance(image, Image):
            image = image.id

        payload = {"image": image, "command": command}
        payload.update(kwargs)
        payload = self._render_payload(payload)
        payload = api.prepare_body(payload)

        response = self.client.post(
            "/containers/create", headers={"content-type": "application/json"}, data=payload
        )
        response.raise_for_status(not_found=ImageNotFound)

        container_id = response.json()["Id"]

        return self.get(container_id)

    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    @staticmethod
    def _render_payload(kwargs: MutableMapping[str, Any]) -> Dict[str, Any]:
        """Map create/run kwargs into body parameters."""
        args = copy.copy(kwargs)

        if "links" in args:
            if len(args["links"]) > 0:
                raise ValueError("'links' are not supported by Podman service.")
            del args["links"]

        # Ignore these keywords
        for key in (
            "cpu_count",
            "cpu_percent",
            "nano_cpus",
            "platform",  # used by caller
            "remove",  # used by caller
            "stderr",  # used by caller
            "stdout",  # used by caller
            "stream",  # used by caller
            "detach",  # used by caller
            "volume_driver",
        ):
            with suppress(KeyError):
                del args[key]

        # These keywords are not supported for various reasons.
        unsupported_keys = set(args.keys()).intersection(
            (
                "blkio_weight",
                "blkio_weight_device",  # FIXME In addition to device Major/Minor include path
                "device_cgroup_rules",  # FIXME Where to map for Podman API?
                "device_read_bps",  # FIXME In addition to device Major/Minor include path
                "device_read_iops",  # FIXME In addition to device Major/Minor include path
                "device_requests",  # FIXME In addition to device Major/Minor include path
                "device_write_bps",  # FIXME In addition to device Major/Minor include path
                "device_write_iops",  # FIXME In addition to device Major/Minor include path
                "domainname",
                "network_disabled",  # FIXME Where to map for Podman API?
                "storage_opt",  # FIXME Where to map for Podman API?
                "tmpfs",  # FIXME Where to map for Podman API?
            )
        )
        if len(unsupported_keys) > 0:
            raise TypeError(
                f"""Keyword(s) '{" ,".join(unsupported_keys)}' are"""
                f""" currently not supported by Podman API."""
            )

        def pop(k):
            return args.pop(k, None)

        def to_bytes(size: Union[int, str, None]) -> Union[int, None]:
            """
            Converts str or int to bytes.
            Input can be in the following forms :
            0) None - e.g. None -> returns None
            1) int - e.g. 100 == 100 bytes
            2) str - e.g. '100' == 100 bytes
            3) str with suffix - available suffixes:
               b | B - bytes
               k | K = kilobytes
               m | M = megabytes
               g | G = gigabytes
               e.g. '100m' == 104857600 bytes
            """
            size_type = type(size)
            if size is None:
                return size
            if size_type is int:
                return size
            if size_type is str:
                try:
                    return int(size)
                except ValueError as bad_size:
                    mapping = {'b': 0, 'k': 1, 'm': 2, 'g': 3}
                    mapping_regex = ''.join(mapping.keys())
                    search = re.search(rf'^(\d+)([{mapping_regex}])$', size.lower())
                    if search:
                        return int(search.group(1)) * (1024 ** mapping[search.group(2)])
                    raise TypeError(
                        f"Passed string size {size} should be in format\\d+[bBkKmMgG] (e.g. '100m')"
                    ) from bad_size
            else:
                raise TypeError(
                    f"Passed size {size} should be a type of unicode, str "
                    f"or int (found : {size_type})"
                )

        # Transform keywords into parameters
        params = {
            "annotations": pop("annotations"),  # TODO document, podman only
            "apparmor_profile": pop("apparmor_profile"),  # TODO document, podman only
            "cap_add": pop("cap_add"),
            "cap_drop": pop("cap_drop"),
            "cgroup_parent": pop("cgroup_parent"),
            "cgroups_mode": pop("cgroups_mode"),  # TODO document, podman only
            "cni_networks": [pop("network")],
            "command": args.pop("command", args.pop("cmd", None)),
            "conmon_pid_file": pop("conmon_pid_file"),  # TODO document, podman only
            "containerCreateCommand": pop("containerCreateCommand"),  # TODO document, podman only
            "devices": [],
            "dns_options": pop("dns_opt"),
            "dns_search": pop("dns_search"),
            "dns_server": pop("dns"),
            "entrypoint": pop("entrypoint"),
            "env": pop("environment"),
            "env_host": pop("env_host"),  # TODO document, podman only
            "expose": {},
            "groups": pop("group_add"),
            "healthconfig": pop("healthcheck"),
            "health_check_on_failure_action": pop("health_check_on_failure_action"),
            "hostadd": [],
            "hostname": pop("hostname"),
            "httpproxy": pop("use_config_proxy"),
            "idmappings": pop("idmappings"),  # TODO document, podman only
            "image": pop("image"),
            "image_volume_mode": pop("image_volume_mode"),  # TODO document, podman only
            "image_volumes": pop("image_volumes"),  # TODO document, podman only
            "init": pop("init"),
            "init_path": pop("init_path"),
            "isolation": pop("isolation"),
            "labels": pop("labels"),
            "log_configuration": {},
            "lxc_config": pop("lxc_config"),
            "mask": pop("masked_paths"),
            "mounts": [],
            "name": pop("name"),
            "namespace": pop("namespace"),  # TODO What is this for?
            "network_options": pop("network_options"),  # TODO document, podman only
            "networks": pop("networks"),
            "no_new_privileges": pop("no_new_privileges"),  # TODO document, podman only
            "oci_runtime": pop("runtime"),
            "oom_score_adj": pop("oom_score_adj"),
            "overlay_volumes": pop("overlay_volumes"),  # TODO document, podman only
            "portmappings": [],
            "privileged": pop("privileged"),
            "procfs_opts": pop("procfs_opts"),  # TODO document, podman only
            "publish_image_ports": pop("publish_all_ports"),
            "r_limits": [],
            "raw_image_name": pop("raw_image_name"),  # TODO document, podman only
            "read_only_filesystem": pop("read_only"),
            "remove": args.pop("remove", args.pop("auto_remove", None)),
            "resource_limits": {},
            "rootfs": pop("rootfs"),
            "rootfs_propagation": pop("rootfs_propagation"),
            "sdnotifyMode": pop("sdnotifyMode"),  # TODO document, podman only
            "seccomp_policy": pop("seccomp_policy"),  # TODO document, podman only
            "seccomp_profile_path": pop("seccomp_profile_path"),  # TODO document, podman only
            "secrets": pop("secrets"),  # TODO document, podman only
            "selinux_opts": pop("security_opt"),
            "shm_size": to_bytes(pop("shm_size")),
            "static_mac": pop("mac_address"),
            "stdin": pop("stdin_open"),
            "stop_signal": pop("stop_signal"),
            "stop_timeout": pop("stop_timeout"),  # TODO document, podman only
            "sysctl": pop("sysctls"),
            "systemd": pop("systemd"),  # TODO document, podman only
            "terminal": pop("tty"),
            "timezone": pop("timezone"),
            "umask": pop("umask"),  # TODO document, podman only
            "unified": pop("unified"),  # TODO document, podman only
            "unmask": pop("unmasked_paths"),  # TODO document, podman only
            "use_image_hosts": pop("use_image_hosts"),  # TODO document, podman only
            "use_image_resolve_conf": pop("use_image_resolve_conf"),  # TODO document, podman only
            "user": pop("user"),
            "version": pop("version"),
            "volumes": [],
            "volumes_from": pop("volumes_from"),
            "work_dir": pop("working_dir"),
        }

        for device in args.pop("devices", []):
            params["devices"].append({"path": device})

        for item in args.pop("exposed_ports", []):
            port, protocol = item.split("/")
            params["expose"][int(port)] = protocol

        for hostname, ip in args.pop("extra_hosts", {}).items():
            params["hostadd"].append(f"{hostname}:{ip}")

        if "log_config" in args:
            params["log_configuration"]["driver"] = args["log_config"].get("Type")

            if "Config" in args["log_config"]:
                params["log_configuration"]["path"] = args["log_config"]["Config"].get("path")
                params["log_configuration"]["size"] = args["log_config"]["Config"].get("size")
                params["log_configuration"]["options"] = args["log_config"]["Config"].get("options")
            args.pop("log_config")

        for item in args.pop("mounts", []):
            mount_point = {
                "destination": item.get("target"),
                "options": [],
                "source": item.get("source"),
                "type": item.get("type"),
            }

            # some names are different for podman-py vs REST API due to compatibility with docker
            # some (e.g. chown) despite listed in podman-run documentation fails with error
            names_dict = {"read_only": "ro", "chown": "U"}

            options = []
            simple_options = ["propagation", "relabel"]
            bool_options = ["read_only", "U", "chown"]
            regular_options = ["consistency", "mode", "size"]

            for k, v in item.items():
                option_name = names_dict.get(k, k)
                if k in bool_options and v is True:
                    options.append(option_name)
                elif k in regular_options:
                    options.append(f'{option_name}={v}')
                elif k in simple_options:
                    options.append(v)

            mount_point["options"] = options

            params["mounts"].append(mount_point)

        if "pod" in args:
            pod = args.pop("pod")
            if isinstance(pod, Pod):
                pod = pod.id
            params["pod"] = pod  # TODO document, podman only

        def parse_host_port(_container_port, _protocol, _host):
            result = []
            port_map = {"container_port": int(_container_port), "protocol": _protocol}
            if _host is None:
                result.append(port_map)
            elif isinstance(_host, int) or isinstance(_host, str) and _host.isdigit():
                port_map["host_port"] = int(_host)
                result.append(port_map)
            elif isinstance(_host, tuple):
                port_map["host_ip"] = _host[0]
                port_map["host_port"] = int(_host[1])
                result.append(port_map)
            elif isinstance(_host, list):
                for host_list in _host:
                    host_list_result = parse_host_port(_container_port, _protocol, host_list)
                    result.extend(host_list_result)
            elif isinstance(_host, dict):
                _host_port = _host.get("port")
                if _host_port is not None:
                    if (
                        isinstance(_host_port, int)
                        or isinstance(_host_port, str)
                        and _host_port.isdigit()
                    ):
                        port_map["host_port"] = int(_host_port)
                    elif isinstance(_host_port, tuple):
                        port_map["host_ip"] = _host_port[0]
                        port_map["host_port"] = int(_host_port[1])
                if _host.get("range"):
                    port_map["range"] = _host.get("range")
                if _host.get("ip"):
                    port_map["host_ip"] = _host.get("ip")
                result.append(port_map)
            return result

        for container, host in args.pop("ports", {}).items():
            if "/" in container:
                container_port, protocol = container.split("/")
            else:
                container_port, protocol = container, "tcp"

            port_map_list = parse_host_port(container_port, protocol, host)
            params["portmappings"].extend(port_map_list)

        if "restart_policy" in args:
            params["restart_policy"] = args["restart_policy"].get("Name")
            params["restart_tries"] = args["restart_policy"].get("MaximumRetryCount")
            args.pop("restart_policy")

        params["resource_limits"]["pids"] = {"limit": args.pop("pids_limit", None)}

        params["resource_limits"]["cpu"] = {
            "cpus": args.pop("cpuset_cpus", None),
            "mems": args.pop("cpuset_mems", None),
            "period": args.pop("cpu_period", None),
            "quota": args.pop("cpu_quota", None),
            "realtimePeriod": args.pop("cpu_rt_period", None),
            "realtimeRuntime": args.pop("cpu_rt_runtime", None),
            "shares": args.pop("cpu_shares", None),
        }

        params["resource_limits"]["memory"] = {
            "disableOOMKiller": args.pop("oom_kill_disable", None),
            "kernel": to_bytes(args.pop("kernel_memory", None)),
            "kernelTCP": args.pop("kernel_memory_tcp", None),
            "limit": to_bytes(args.pop("mem_limit", None)),
            "reservation": to_bytes(args.pop("mem_reservation", None)),
            "swap": to_bytes(args.pop("memswap_limit", None)),
            "swappiness": args.pop("mem_swappiness", None),
            "useHierarchy": args.pop("mem_use_hierarchy", None),
        }

        for item in args.pop("ulimits", []):
            params["r_limits"].append(
                {
                    "type": item["Name"],
                    "hard": item["Hard"],
                    "soft": item["Soft"],
                }
            )

        for item in args.pop("volumes", {}).items():
            key, value = item
            extended_mode = value.get('extended_mode', [])
            if not isinstance(extended_mode, list):
                raise ValueError("'extended_mode' value should be a list")

            options = extended_mode
            mode = value.get('mode')
            if mode is not None:
                if not isinstance(mode, str):
                    raise ValueError("'mode' value should be a str")
                options.append(mode)

            volume = {"Name": key, "Dest": value["bind"], "Options": options}
            params["volumes"].append(volume)

        if "cgroupns" in args:
            params["cgroupns"] = {"nsmode": args.pop("cgroupns")}

        if "ipc_mode" in args:
            params["ipcns"] = {"nsmode": args.pop("ipc_mode")}

        if "network_mode" in args:
            params["netns"] = {"nsmode": args.pop("network_mode")}

        if "pid_mode" in args:
            params["pidns"] = {"nsmode": args.pop("pid_mode")}

        if "userns_mode" in args:
            params["userns"] = {"nsmode": args.pop("userns_mode")}

        if "uts_mode" in args:
            params["utsns"] = {"nsmode": args.pop("uts_mode")}

        if len(args) > 0:
            raise TypeError(
                "Unknown keyword argument(s): " + " ,".join(f"'{k}'" for k in args.keys())
            )

        return params
