"""Mixin to provide Container create() method."""
import copy
import logging
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
            devices (List[str): Expose host devices to the container, as a List[str] in the form
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
            name (str): The name for this container.
            nano_cpus (int):  CPU quota in units of 1e-9 CPUs.
            network (str): Name of the network this container will be connected to at creation time.
                You can connect to additional networks using Network.connect.
                Incompatible with network_mode.
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
            ports (Dict[str, Union[int, Tuple[str, int], List[int]]]): Ports to bind inside
                the container.

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
                - A list of integers, if you want to bind multiple host ports to a single container
                    port.
                    For example: {'1111/tcp': [1234, 4567]}.

                    For example: {'9090': 7878, '10932/tcp': '8781',
                                  "8989/tcp": ("127.0.0.1", 9091)}

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
            volumes (Dict[str, Dict[str, str]]): A dictionary to configure volumes mounted inside
                the container. The key is either the host path or a volume name, and the value is
                a dictionary with the keys:

                - bind: The path to mount the volume inside the container
                - mode: Either rw to mount the volume read/write, or ro to mount it read-only.

                For example:

                    {'/home/user1/': {'bind': '/mnt/vol2', 'mode': 'rw'},
                     '/var/www': {'bind': '/mnt/vol1', 'mode': 'ro'}}

            volumes_from (List[str]): List of container names or IDs to get volumes from.
            working_dir (str): Path to the working directory.

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

        body = response.json()
        return self.get(body["Id"])

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
                "devices",  # FIXME In addition to device Major/Minor include path
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

        # Transform keywords into parameters
        params = {
            "aliases": pop("aliases"),  # TODO document, podman only
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
            "dns_options": pop("dns_opt"),
            "dns_search": pop("dns_search"),
            "dns_server": pop("dns"),
            "entrypoint": pop("entrypoint"),
            "env": pop("environment"),
            "env_host": pop("env_host"),  # TODO document, podman only
            "expose": dict(),
            "groups": pop("group_add"),
            "healthconfig": pop("healthcheck"),
            "hostadd": pop("extra_hosts"),
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
            "log_configuration": dict(),
            "lxc_config": pop("lxc_config"),
            "mask": pop("masked_paths"),
            "mounts": list(),
            "name": pop("name"),
            "namespace": pop("namespace"),  # TODO What is this for?
            "network_options": pop("network_options"),  # TODO document, podman only
            "no_new_privileges": pop("no_new_privileges"),  # TODO document, podman only
            "oci_runtime": pop("runtime"),
            "oom_score_adj": pop("oom_score_adj"),
            "overlay_volumes": pop("overlay_volumes"),  # TODO document, podman only
            "portmappings": list(),
            "privileged": pop("privileged"),
            "procfs_opts": pop("procfs_opts"),  # TODO document, podman only
            "publish_image_ports": pop("publish_all_ports"),
            "r_limits": list(),
            "raw_image_name": pop("raw_image_name"),  # TODO document, podman only
            "read_only_filesystem": pop("read_only"),
            "remove": args.pop("remove", args.pop("auto_remove", None)),
            "resource_limits": dict(),
            "rootfs": pop("rootfs"),
            "rootfs_propagation": pop("rootfs_propagation"),
            "sdnotifyMode": pop("sdnotifyMode"),  # TODO document, podman only
            "seccomp_policy": pop("seccomp_policy"),  # TODO document, podman only
            "seccomp_profile_path": pop("seccomp_profile_path"),  # TODO document, podman only
            "secrets": pop("secrets"),  # TODO document, podman only
            "selinux_opts": pop("security_opt"),
            "shm_size": pop("shm_size"),
            "static_ip": pop("static_ip"),  # TODO document, podman only
            "static_ipv6": pop("static_ipv6"),  # TODO document, podman only
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
            "volumes": list(),
            "volumes_from": pop("volumes_from"),
            "work_dir": pop("working_dir"),
        }

        for item in args.pop("exposed_ports", list()):
            port, protocol = item.split("/")
            params["expose"][int(port)] = protocol

        if "log_config" in args:
            params["log_configuration"]["driver"] = args["log_config"].get("Type")

            if "Config" in args["log_config"]:
                params["log_configuration"]["path"] = args["log_config"]["Config"].get("path")
                params["log_configuration"]["size"] = args["log_config"]["Config"].get("size")
                params["log_configuration"]["options"] = args["log_config"]["Config"].get("options")
            args.pop("log_config")

        for item in args.pop("mounts", list()):
            mount_point = {
                "destination": item.get("target"),
                "options": [],
                "source": item.get("source"),
                "type": item.get("type"),
            }

            options = list()
            if "read_only" in item:
                options.append("ro")
            if "consistency" in item:
                options.append(f"consistency={item['consistency']}")
            if "mode" in item:
                options.append(f"mode={item['mode']}")
            if "propagation" in item:
                options.append(item["propagation"])
            if "size" in item:
                options.append(f"size={item['size']}")
            mount_point["options"] = options

            params["mounts"].append(mount_point)

        if "pod" in args:
            pod = args.pop("pod")
            if isinstance(pod, Pod):
                pod = pod.id
            params["pod"] = pod  # TODO document, podman only

        for container, host in args.pop("ports", dict()).items():
            if "/" in container:
                container_port, protocol = container.split("/")
            else:
                container_port, protocol = container, "tcp"

            port_map = {"container_port": int(container_port), "protocol": protocol}
            if host is None:
                pass
            elif isinstance(host, int) or isinstance(host, str) and host.isdigit():
                port_map["host_port"] = int(host)
            elif isinstance(host, tuple):
                port_map["host_ip"] = host[0]
                port_map["host_port"] = int(host[1])
            elif isinstance(host, list):
                raise ValueError(
                    "Podman API does not support multiple port bound to a single host port."
                )
            else:
                raise ValueError(f"'ports' value  of '{host}' is not supported.")

            params["portmappings"].append(port_map)

        if "restart_policy" in args:
            params["restart_policy"] = args["restart_policy"].get("Name")
            params["restart_tries"] = args["restart_policy"].get("MaximumRetryCount")
            args.pop("restart_policy")

        params["resource_limits"]["pids"] = dict()
        params["resource_limits"]["pids"]["limit"] = args.pop("pids_limit", None)

        params["resource_limits"]["cpu"] = dict()
        params["resource_limits"]["cpu"]["cpus"] = args.pop("cpuset_cpus", None)
        params["resource_limits"]["cpu"]["mems"] = args.pop("cpuset_mems", None)
        params["resource_limits"]["cpu"]["period"] = args.pop("cpu_period", None)
        params["resource_limits"]["cpu"]["quota"] = args.pop("cpu_quota", None)
        params["resource_limits"]["cpu"]["realtimePeriod"] = args.pop("cpu_rt_period", None)
        params["resource_limits"]["cpu"]["realtimeRuntime"] = args.pop("cpu_rt_runtime", None)
        params["resource_limits"]["cpu"]["shares"] = args.pop("cpu_shares", None)

        params["resource_limits"]["memory"] = dict()
        params["resource_limits"]["memory"]["disableOOMKiller"] = args.pop("oom_kill_disable", None)
        params["resource_limits"]["memory"]["kernel"] = args.pop("kernel_memory", None)
        params["resource_limits"]["memory"]["kernelTCP"] = args.pop("kernel_memory_tcp", None)
        params["resource_limits"]["memory"]["limit"] = args.pop("mem_limit", None)
        params["resource_limits"]["memory"]["reservation"] = args.pop("mem_reservation", None)
        params["resource_limits"]["memory"]["swap"] = args.pop("memswap_limit", None)
        params["resource_limits"]["memory"]["swappiness"] = args.pop("mem_swappiness", None)
        params["resource_limits"]["memory"]["useHierarchy"] = args.pop("mem_use_hierarchy", None)

        for item in args.pop("ulimits", list()):
            params["r_limits"].append(
                {
                    "type": item["Name"],
                    "hard": item["Hard"],
                    "soft": item["Soft"],
                }
            )

        for item in args.pop("volumes", dict()).items():
            key, value = item
            volume = {
                "Name": key,
                "Dest": value["bind"],
                "Options": [value["mode"]] if "mode" in value else [],
            }
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
