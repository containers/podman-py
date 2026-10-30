"""Mixin to provide Container create() method."""

# pylint: disable=line-too-long
import copy
import logging
import re
from contextlib import suppress
from typing import Any
from collections.abc import MutableMapping
import requests

from podman import api
from podman.api.parse_utils import HEALTH_ON_FAILURE_ACTION, prepare_duration_ns
from podman.domain.containers import Container
from podman.domain.images import Image
from podman.domain.pods import Pod
from podman.domain.secrets import Secret

logger = logging.getLogger("podman.containers")

# Network modes recognised by `podman run --network`, mirroring ParseNetworkFlag in
# https://github.com/containers/podman/blob/main/pkg/specgen/namespaces.go
# Any other value is the name of a network to attach to.
_NETWORK_MODES = frozenset({"default", "host", "none", "pod", "private"})
# "<mode>" or "<mode>:<options>"
_NETWORK_MODES_WITH_OPTIONS = frozenset({"bridge", "pasta", "slirp4netns"})
# only "<mode>:<value>"
_NETWORK_MODES_WITH_VALUE = frozenset({"container", "ns"})
NAMED_VOLUME_PATTERN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*")


class CreateMixin:  # pylint: disable=too-few-public-methods
    """Class providing create method for ContainersManager."""

    def create(
        self,
        image: Image | str,
        command: str | list[str] | None = None,
        **kwargs,
    ) -> Container:
        """Create a container.

        Args:
            image: Image to run.
            command: Command to run in the container.

        Keyword Args:
            all_tags (bool): Pull all tags from repository. Default: False.
                Only used if the method needs to pull the requested image.
            auth_config (Mapping[str, str]): Override the credentials that are found in the
                config for this request. auth_config should contain the username and password
                keys to be valid.
                Only used if the method needs to pull the requested image.
            auto_remove (bool): Enable auto-removal of the container on daemon side when the
                container's process exits.
            blkio_weight_device (dict[str, Any]): Block IO weight (relative device weight)
                in the form of: [{"Path": "device_path", "Weight": weight}].
            blkio_weight (int): Block IO weight (relative weight), accepts a weight value
                between 10 and 1000.
            cap_add (list[str]): Add kernel capabilities. For example: ["SYS_ADMIN", "MKNOD"]
            cap_drop (list[str]): Drop kernel capabilities.
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
            decode (bool): Decode the JSON data from the server into dicts.
                Only applies with ``stream=True``. Default: False.
                Only used if the method needs to pull the requested image.
            detach (bool): Run container in the background and return a Container object.
            device_cgroup_rules (list[str]): A list of cgroup rules to apply to the container.
            device_read_bps: Limit read rate (bytes per second) from a device in the form of:
                `[{"Path": "device_path", "Rate": rate}]`
            device_read_iops: Limit read rate (IO per second) from a device.
            device_write_bps: Limit write rate (bytes per second) from a device.
            device_write_iops: Limit write rate (IO per second) from a device.
            devices (list[str]): Expose host devices to the container, as a list[str] in the form
                <path_on_host>:<path_in_container>:<cgroup_permissions>.

                For example:
                    /dev/sda:/dev/xvda:rwm allows the container to have read-write access to the
                    host's /dev/sda via a node named /dev/xvda inside the container.

            dns (list[str]): Set custom DNS servers.
            dns_opt (list[str]): Additional options to be added to the container's resolv.conf file.
            dns_search (list[str]): DNS search domains.
            domainname (str | list[str]): Set custom DNS search domains.
            entrypoint (str | list[str]): The entrypoint for the container.
            environment (dict[str, str] | list[str]): Environment variables to set inside
                the container, as a dictionary or a list[str] in the format
                ["SOMEVARIABLE=xxx", "SOMEOTHERVARIABLE=xyz"].
            extra_hosts (dict[str, str]): Additional hostnames to resolve inside the container,
                as a mapping of hostname to IP address.
            group_add (list[str]): List of additional group names and/or IDs that the container
                process will run as.
            healthcheck (dict[str,Any]): Specify a test to perform to check that the
                container is healthy. Mutually exclusive with fine-grained health_* kwargs.
            health_check_on_failure_action (int): Specify an action if a healthcheck fails.
                Mutually exclusive with health_on_failure.
            health_cmd (str): set a healthcheck command for the container ('None' disables the
                existing healthcheck)
            health_interval (str or int): set an interval for the healthcheck. Accepts a
                Go-style duration string (e.g. "30s", "1m") or nanoseconds as int.
                (a value of disable results in no automatic timer setup)
                (Changing this setting resets timer.) (default "30s")
            health_log_destination (str): set the destination of the HealthCheck log. Directory
                path, local or events_logger (local use container state file) (Warning: Changing
                this setting may cause the loss of previous logs.) (default "local")
            health_max_log_count (int): set maximum number of attempts in the HealthCheck log file.
                ('0' value means an infinite number of attempts in the log file) (default 5)
            health_max_logs_size (int): set maximum length in characters of stored HealthCheck log.
                ('0' value means an infinite log length) (default 500)
            health_on_failure (str): action to take once the container turns unhealthy.
                One of: "none" (0), "kill" (2), "restart" (3), "stop" (4). Value 1 is
                reserved as "invalid" in the Go enum. Mutually exclusive with
                health_check_on_failure_action. (default "none")
            health_retries (int): the number of retries allowed before a healthcheck is considered
                to be unhealthy (default 3)
            health_start_period (str or int): the initialization time needed for a container to
                bootstrap. Accepts a Go-style duration string or nanoseconds as int.
                (default "0s")
            health_startup_cmd (str): set a startup healthcheck command for the container
            health_startup_interval (str or int): set an interval for the startup healthcheck.
                Accepts a Go-style duration string or nanoseconds as int. Changing this setting
                resets the timer, depending on the state of the container. (default "30s")
            health_startup_retries (int): set the maximum number of retries before the startup
                healthcheck will restart the container
            health_startup_success (int): set the number of consecutive successes before the
                startup healthcheck is marked as successful and the normal healthcheck begins
                (0 indicates any success will start the regular healthcheck)
            health_startup_timeout (str or int): set the maximum amount of time that the startup
                healthcheck may take before it is considered failed. Accepts a Go-style duration
                string or nanoseconds as int. (default "30s")
            health_timeout (str or int): the maximum time allowed to complete the healthcheck
                before an interval is considered failed. Accepts a Go-style duration string or
                nanoseconds as int. (default "30s")
            no_healthcheck (bool): disable healthchecks for this container. Mutually exclusive
                with health_* kwargs.
            hostname (str): Optional hostname for the container.
            init (bool): Run an init inside the container that forwards signals and reaps processes
            init_path (str): Path to the docker-init binary
            ipc_mode (str): Set the IPC mode for the container, e.g. host, private, shareable,
                none, container:<name|id> or ns:<path>.
            isolation (str): Isolation technology to use. Default: `None`.
            kernel_memory (int or str): Kernel memory limit
            labels (dict[str, str] | list[str]): A dictionary of name-value labels (e.g.
                {"label1": "value1", "label2": "value2"}) or a list of names of labels to set
                with empty values (e.g. ["label1", "label2"])
            links (dict[str, str] | None): Mapping of links using the {'container': 'alias'}
                format. The alias is optional. Containers declared in this dict will be linked to
                the new container using the provided alias. Default: None.
            log_config (LogConfig): Logging configuration.
            lxc_config (dict[str, str]): LXC config.
            mac_address (str): MAC address to assign to the container.
            mem_limit (int | str): Memory limit. Accepts float values (which represent the
                memory limit of the created container in bytes) or a string with a units
                identification char (100000b, 1000k, 128m, 1g). If a string is specified without
                a units character, bytes are assumed as an intended unit.
            mem_reservation (int | str): Memory soft limit.
            mem_swappiness (int): Tune a container's memory swappiness behavior. Accepts number
                between 0 and 100.
            memswap_limit (int | str): Maximum amount of memory + swap a container is allowed
                to consume.
            mounts (list[Mount]): Specification for mounts to be added to the container. More
                powerful alternative to volumes. Each item in the list is expected to be a
                Mount object.
                For example:

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

                        # If this was not passed, the regular directory

                        # would be created rather than tmpfs mount !!!

                        # as this will cause to have invalid entry

                        # in /proc/self/mountinfo

                        "source": "tmpfs",

                        "target" "/d2",

                        "size": "100k",

                        "chown": True

                    }

                ]
            name (str): The name for this container.
            nano_cpus (int):  CPU quota in units of 1e-9 CPUs.
            network (str): Network to connect the container to at creation time, as accepted
                by ``podman create --network``. One of:

                - <name>[:<options>]: Name of a network (shorthand for
                  ``networks={name: {...}}``), with optional per-network options
                  (ip=, ip6=, mac=, alias=, interface_name=, or any other key=value).
                - <name>,<name>,...: Several networks without options.
                - A network mode keyword as accepted by ``network_mode``
                  (e.g. ``host``, ``none``, ``container:<id>``).

                Incompatible with ``network_mode``. Options given for a network that is also
                in ``networks`` (``<name>:<options>``, or ``bridge:<options>`` with a
                ``default`` entry) raise ``ValueError``; a plain name already in ``networks``
                keeps that entry.
            networks (dict[str, dict[str, str | list[str]]]):
                Networks which will be connected to container during container creation
                Values of the network configuration can be :

                - string
                - list of strings (e.g. Aliases)
            network_disabled (bool): Disable networking.
            network_mode (str): One of:

                - bridge[:<options>]: Create a new network stack for the container
                  on the default bridge network, with optional per-network options
                  (e.g. ip=, mac=, alias=, interface_name=).
                - none: No networking for this container.
                - container:<name|id>: Reuse another container's network
                  stack.
                - host: Use the host network stack.
                - ns:<path>: User defined netns path.
                - private / default: Create a new, private network namespace.
                - pod: Join the pod's network namespace.
                - pasta[:<options>]: Use pasta for user-mode networking.
                - slirp4netns[:<options>]: Use slirp4netns for user-mode networking.
                  Only accepted by older Podman versions; newer ones reject it in
                  favour of pasta.

                Incompatible with network.
            oom_kill_disable (bool): Whether to disable OOM killer.
            oom_score_adj (int): An integer value containing the score given to the container in
                order to tune OOM killer preferences.
            pid_mode (str): If set to host, use the host PID namespace
                inside the container. Also accepts private, container:<name|id> and ns:<path>.
            pids_limit (int): Tune a container's pids limit. Set -1 for unlimited.
            platform (str): Platform in the format os[/arch[/variant]]. Only used if the method
                needs to pull the requested image.
            policy (str): Pull policy. "missing" (default for create), "always", "never", "newer".
                Only used if the method needs to pull the requested image.
            ports (
                dict[
                    int | str,
                    int
                    | tuple[str, int]
                    | list[int]
                    | dict[str, int | tuple[str, int] | list[int]],
                ]): Ports to bind inside the container.

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
            progress_bar (bool): Display a progress bar with the image pull progress (uses
                the compat endpoint). Default: False.
                Only used if the method needs to pull the requested image.
            publish_all_ports (bool): Publish all ports to the host.
            pull_stream (bool): When True, the pull progress will be published as received.
                Default: False. Only used if the method needs to pull the requested image.
            read_only (bool): Mount the container's root filesystem as read only.
            read_write_tmpfs (bool): Mount temporary file systems as read write,
                in case of read_only options set to True. Default: False
            remove (bool): Remove the container when it has finished running. Default: False.
            restart_policy (dict[str, str | int]): Restart the container when it exits.
                Configured as a dictionary with keys:

                - Name: One of on-failure, or always.
                - MaximumRetryCount: Number of times to restart the container on failure.

                For example: {"Name": "on-failure", "MaximumRetryCount": 5}
            runtime (str): Runtime to use with this container.
            secrets (list[str | Secret | dict[str, str | int]]): Secrets to
                mount to this container.

                For example:

                - As list of strings, each string representing a secret's ID or name:
                    ['my_secret', 'my_secret2']

                - As list of Secret objects the corresponding IDs are read from:
                    [Secret, Secret]

                - As list of dictionaries:
                    [

                        {

                            "source": "my_secret",  # A string representing the ID or name of
                                                    # a secret

                            "target": "/my_secret", # An optional target to mount source to,
                                                    # falls back to /run/secrets/source

                            "uid": 1000,            # An optional UID that falls back to 0
                                                    # if not given

                            "gid": 1000,            # An optional GID that falls back to 0
                                                    # if not given

                            "mode": 0o400,          # An optional mode to apply to the target,
                                                    # use an 0o prefix for octal integers

                        },

                    ]
            secret_env (dict[str, str]): Secrets to add as environment variables available in the
                container.

                For example: {"VARIABLE1": "NameOfSecret", "VARIABLE2": "NameOfAnotherSecret"}

            security_opt (list[str]): Security options, as accepted by
                ``podman create --security-opt``:

                - label=<option>: SELinux label option, e.g. label=disable,
                  label=type:spc_t or label=nested
                - apparmor=<profile>: AppArmor profile, or unconfined
                - seccomp=<path>: Seccomp profile path, or unconfined
                - no-new-privileges[=true|false]
                - mask=<path>[:<path>...] / unmask=<path>[:<path>...]
                - systempaths=unconfined
                - proc-opts=<option>[,<option>...]

                Other values are passed through as raw SELinux label options.
            shm_size (str | int): Size of /dev/shm (e.g. 1G).
            stdin_open (bool): Keep STDIN open even if not attached.
            stdout (bool): Return logs from STDOUT when detach=False. Default: True.
            stderr (bool): Return logs from STDERR when detach=False. Default: False.
            stop_signal (str): The stop signal to use to stop the container (e.g. SIGINT).
            storage_opt (dict[str, str]): Storage driver options per container as a
                key-value mapping.
            stream (bool): If true and detach is false, return a log generator instead of a string.
                Ignored if detach is true. Default: False.
            sysctls (dict[str, str]): Kernel parameters to set in the container.
            tmpfs (dict[str, str]): Temporary filesystems to mount, as a dictionary mapping a
                path inside the container to options for that path.

                For example: {'/mnt/vol2': '', '/mnt/vol1': 'size=3G,uid=1000'}

            tls_verify (bool): Require TLS verification. Default: True.
                Only used if the method needs to pull the requested image.
            tty (bool): Allocate a pseudo-TTY.
            ulimits (list[Ulimit]): Ulimits to set inside the container.
            use_config_proxy (bool): If True, and if the docker client configuration
                file (~/.config/containers/config.json by default) contains a proxy configuration,
                the corresponding environment variables will be set in the container being built.
            user (str | int): Username or UID to run commands as inside the container.
            userns_mode (str): Sets the user namespace mode for the container when user namespace
                remapping option is enabled. Supported values documented
                `here <https://docs.podman.io/en/latest/markdown/options/userns.container.html#userns-mode>`_
            uts_mode (str): Sets the UTS namespace mode for the container.
                `These <https://docs.podman.io/en/latest/markdown/options/uts.container.html>`_
                are the supported values.
            version (str): The version of the API to use. Set to auto to automatically detect
                the server's version. Default: 3.0.0
            volume_driver (str): The name of a volume driver/plugin.
            volumes (dict[str, dict[str, str | list]]): A dictionary to configure
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

            volumes_from (list[str]): List of container names or IDs to get volumes from.
            working_dir (str): Path to the working directory.
            workdir (str): Alias of working_dir - Path to the working directory.

        Returns:
            A Container object.

        Raises:
            APIError: when Podman service reports an error
        """
        if isinstance(image, Image):
            image = image.id
        if isinstance(command, str):
            command = [command]

        payload = {"image": image, "command": command}
        payload.update(kwargs)
        payload = self._render_payload(payload)
        payload = api.prepare_body(payload)

        response = self.api.post(
            "/containers/create",
            headers={"content-type": "application/json"},
            data=payload,
        )
        if response.status_code == requests.codes.not_found:
            self.podman_client.images.pull(
                image,
                all_tags=kwargs.get("all_tags", False),
                auth_config=kwargs.get("auth_config"),
                decode=kwargs.get("decode", False),
                platform=kwargs.get("platform"),
                policy=kwargs.get("policy", "missing"),
                progress_bar=kwargs.get("progress_bar", False),
                stream=kwargs.get("pull_stream", False),
                tls_verify=kwargs.get("tls_verify", True),
            )
            response = self.client.post(
                "/containers/create",
                headers={"content-type": "application/json"},
                data=payload,
            )
        response.raise_for_status()

        container_id = response.json()["Id"]

        return self.get(container_id)

    @staticmethod
    def _convert_env_list_to_dict(env_list):
        """Convert a list of environment variables to a dictionary.

        Args:
            env_list (list[str]): List of environment variables in the format ["KEY=value"]

        Returns:
            dict[str, str]: Dictionary of environment variables

        Raises:
            ValueError: If any environment variable is not in the correct format
        """
        if not isinstance(env_list, list):
            raise TypeError(f"Expected list, got {type(env_list).__name__}")

        env_dict = {}

        for env_var in env_list:
            if not isinstance(env_var, str):
                raise TypeError(
                    f"Environment variable must be a string, "
                    f"got {type(env_var).__name__}: {repr(env_var)}"
                )

            # Handle empty strings
            if not env_var.strip():
                raise ValueError("Environment variable cannot be empty")
            if "=" not in env_var:
                raise ValueError(
                    f"Environment variable '{env_var}' is not in the correct format. "
                    "Expected format: 'KEY=value'"
                )
            key, value = env_var.split("=", 1)  # Split on first '=' only

            # Validate key is not empty
            if not key.strip():
                raise ValueError(f"Environment variable has empty key: '{env_var}'")

            env_dict[key] = value
        return env_dict

    @staticmethod
    def _apply_security_opt(params: dict[str, Any], security_opt: list[str] | None) -> None:
        """Map security_opt entries onto the libpod container spec.

        Mirrors ``podman create --security-opt``: each "key=value" (or the deprecated
        "key:value") entry is routed to its own spec field, and the annotations used by
        ``podman inspect`` to report HostConfig.SecurityOpt are set. Entries without a known
        key, e.g. raw SELinux options such as "disable" or "type:spc_t", are passed through
        to selinux_opts unchanged.

        Args:
            params: Container spec being built, updated in place.
            security_opt: Security options as given to create().

        Raises:
            ValueError: If a known option has an invalid value.
        """
        annotations = {}
        label_set = False
        for opt in security_opt or []:
            key, sep, value = opt.partition("=" if "=" in opt else ":")
            if key == "label" and sep:
                if value == "nested":
                    params["label_nested"] = True
                    continue
                params["selinux_opts"] = (params["selinux_opts"] or []) + [value]
                label_set = True
            elif key == "apparmor" and sep:
                params["apparmor_profile"] = value
                annotations["io.podman.annotations.apparmor"] = value
            elif key == "seccomp" and sep:
                params["seccomp_profile_path"] = value
                annotations["io.podman.annotations.seccomp"] = value
            elif key == "no-new-privileges":
                if not sep or value in ("1", "t", "T", "TRUE", "true", "True"):
                    params["no_new_privileges"] = True
                elif value in ("0", "f", "F", "FALSE", "false", "False"):
                    params["no_new_privileges"] = False
                else:
                    raise ValueError(f"Invalid security_opt {opt!r}: expected a boolean value")
            elif key in ("mask", "unmask") and sep:
                params[key] = (params[key] or []) + value.split(":")
            elif key == "systempaths" and sep:
                if value != "unconfined":
                    raise ValueError(
                        f"Invalid security_opt {opt!r}: only 'systempaths=unconfined' is supported"
                    )
                params["unmask"] = (params["unmask"] or []) + ["ALL"]
            elif key == "proc-opts" and sep:
                params["procfs_opts"] = value.split(",")
            else:
                params["selinux_opts"] = (params["selinux_opts"] or []) + [opt]

        if label_set:
            annotations["io.podman.annotations.label"] = ",label=".join(params["selinux_opts"])
        if annotations:
            params["annotations"] = {**(params["annotations"] or {}), **annotations}

    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    @staticmethod
    def _render_payload(kwargs: MutableMapping[str, Any]) -> dict[str, Any]:
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
            "all_tags",  # used by caller
            "auth_config",  # used by caller
            "decode",  # used by caller
            "policy",  # used by caller
            "progress_bar",  # used by caller
            "pull_stream",  # used by caller
            "tls_verify",  # used by caller
            "volume_driver",
        ):
            with suppress(KeyError):
                del args[key]

        # Handle environment variables
        environment = args.pop("environment", None)
        if environment is not None:
            if isinstance(environment, list):
                try:
                    environment = CreateMixin._convert_env_list_to_dict(environment)
                except ValueError as e:
                    raise ValueError(
                        "Failed to convert environment variables list to dictionary. "
                        f"Error: {str(e)}"
                    ) from e
            elif not isinstance(environment, dict):
                raise TypeError(
                    "Environment variables must be provided as either a dictionary "
                    "or a list of strings in the format ['KEY=value']"
                )

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

        def normalize_nsmode(
            mode: str | MutableMapping[str, str],
        ) -> dict[str, str]:
            if isinstance(mode, dict):
                return mode
            # Split "<mode>:<value>" the same way the podman CLI does, e.g.
            # "container:<name|id>", "ns:<path>", "keep-id:uid=1000" or "auto:size=1024".
            nsmode, sep, value = mode.partition(":")
            if sep and nsmode in ("container", "ns", "keep-id", "auto"):
                return {"nsmode": "path" if nsmode == "ns" else nsmode, "value": value}
            return {"nsmode": mode}

        def to_bytes(size: int | str | None) -> int | None:
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
                    mapping = {"b": 0, "k": 1, "m": 2, "g": 3}
                    mapping_regex = "".join(mapping.keys())
                    search = re.search(rf"^(\d+)([{mapping_regex}])$", size.lower())
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

        # Like the CLI (ParseNetworkFlag): `network` is either a namespace mode keyword
        # or the name of a network to attach to (shorthand for `networks={network: {}}`).
        networks = dict(pop("networks") or {})
        # Networks given by the caller, to detect `network` options that would override them.
        user_networks = set(networks)
        network = pop("network")
        network_mode = pop("network_mode")
        if network and network_mode:
            raise RuntimeError('The options "network" and "network_mode" can not be used together.')
        if network:
            if CreateMixin._is_network_mode(network):
                network_mode = network
            else:
                name, sep, options = network.partition(":")
                if sep:
                    if not name:
                        raise ValueError("network name cannot be empty")
                    if name in user_networks:
                        raise ValueError(f'network "{name}" is set in both network and networks')
                    networks[name] = CreateMixin._parse_network_options(options)
                else:
                    # Comma-separated list of networks, kept by the CLI for backwards compatibility.
                    for item in network.split(","):
                        name = item.strip()
                        if not name:
                            raise ValueError("network name cannot be empty")
                        networks.setdefault(name, {})
        if networks and network_mode:
            if isinstance(network_mode, dict):
                mode = network_mode.get("nsmode")
            else:
                mode = network_mode.partition(":")[0]
            if mode != "bridge":
                raise RuntimeError(
                    f'networks can only be used with bridge network mode, got "{mode}"'
                )

        # Transform keywords into parameters
        params = {
            "annotations": pop("annotations"),  # TODO document, podman only
            "apparmor_profile": pop("apparmor_profile"),  # TODO document, podman only
            "cap_add": pop("cap_add"),
            "cap_drop": pop("cap_drop"),
            "cgroup_parent": pop("cgroup_parent"),
            "cgroups_mode": pop("cgroups_mode"),  # TODO document, podman only
            "command": args.pop("command", args.pop("cmd", None)),
            "conmon_pid_file": pop("conmon_pid_file"),  # TODO document, podman only
            "containerCreateCommand": pop("containerCreateCommand"),  # TODO document, podman only
            "devices": [],
            "dns_option": pop("dns_opt"),
            "dns_search": pop("dns_search"),
            "dns_server": pop("dns"),
            "entrypoint": pop("entrypoint"),
            "env": environment,
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
            "networks": networks or None,
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
            "read_write_tmpfs": pop("read_write_tmpfs"),
            "remove": args.pop("remove", args.pop("auto_remove", None)),
            "resource_limits": {},
            "rootfs": pop("rootfs"),
            "rootfs_propagation": pop("rootfs_propagation"),
            "sdnotifyMode": pop("sdnotifyMode"),  # TODO document, podman only
            "seccomp_policy": pop("seccomp_policy"),  # TODO document, podman only
            "seccomp_profile_path": pop("seccomp_profile_path"),  # TODO document, podman only
            "secrets": [],  # TODO document, podman only
            "selinux_opts": None,  # filled from security_opt by _apply_security_opt()
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
            "work_dir": pop("workdir") or pop("working_dir"),
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
            normalized_item = {key.lower(): value for key, value in item.items()}
            mount_point = {
                "destination": normalized_item.get("target"),
                "options": [],
                "source": normalized_item.get("source"),
                "type": normalized_item.get("type"),
            }

            # some names are different for podman-py vs REST API due to compatibility with docker
            # some (e.g. chown) despite listed in podman-run documentation fails with error
            names_dict = {"read_only": "ro", "chown": "U"}

            options = []
            simple_options = ["propagation", "relabel"]
            bool_options = ["read_only", "U", "chown"]
            regular_options = ["consistency", "mode", "size"]

            for k, v in item.items():
                _k = k.lower()
                option_name = names_dict.get(_k, _k)
                if _k in bool_options and v is True:
                    options.append(option_name)
                elif _k in regular_options:
                    options.append(f"{option_name}={v}")
                elif _k in simple_options:
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
            # avoid redefinition of the loop variable, then ensure it's a string
            str_container = container
            if isinstance(str_container, int):
                str_container = str(str_container)

            if "/" in str_container:
                container_port, protocol = str_container.split("/")
            else:
                container_port, protocol = str_container, "tcp"

            port_map_list = parse_host_port(container_port, protocol, host)
            params["portmappings"].extend(port_map_list)

        if "restart_policy" in args:
            params["restart_policy"] = args["restart_policy"].get("Name")
            params["restart_tries"] = args["restart_policy"].get("MaximumRetryCount")
            args.pop("restart_policy")

        # Assemble fine-grained health kwargs into nested API objects.
        health_kwargs = {
            "health_cmd",
            "health_interval",
            "health_log_destination",
            "health_max_log_count",
            "health_max_logs_size",
            "health_on_failure",
            "health_retries",
            "health_start_period",
            "health_startup_cmd",
            "health_startup_interval",
            "health_startup_retries",
            "health_startup_success",
            "health_startup_timeout",
            "health_timeout",
        }
        present_health_kwargs = set(args) & health_kwargs
        no_healthcheck = args.pop("no_healthcheck", None)

        if no_healthcheck and present_health_kwargs:
            raise ValueError(f"Cannot set {min(present_health_kwargs)} when no_healthcheck is True")

        if params.get("healthconfig") and present_health_kwargs:
            raise ValueError(
                "Cannot combine 'healthcheck' dict with fine-grained health_* kwargs. "
                "Use one or the other."
            )

        if no_healthcheck:
            params["healthconfig"] = {"Test": ["NONE"]}
        elif present_health_kwargs:
            health_cmd = args.pop("health_cmd", None)
            health_interval = args.pop("health_interval", None)
            health_timeout = args.pop("health_timeout", None)
            health_retries = args.pop("health_retries", None)
            health_start_period = args.pop("health_start_period", None)

            healthconfig = {}
            if health_cmd is not None:
                healthconfig["Test"] = ["CMD-SHELL", health_cmd]
            if health_interval is not None:
                healthconfig["Interval"] = prepare_duration_ns(health_interval)
            if health_timeout is not None:
                healthconfig["Timeout"] = prepare_duration_ns(health_timeout)
            if health_retries is not None:
                healthconfig["Retries"] = int(health_retries)
            if health_start_period is not None:
                healthconfig["StartPeriod"] = prepare_duration_ns(health_start_period)
            if healthconfig:
                params["healthconfig"] = healthconfig

            startup_cmd = args.pop("health_startup_cmd", None)
            startup_interval = args.pop("health_startup_interval", None)
            startup_timeout = args.pop("health_startup_timeout", None)
            startup_retries = args.pop("health_startup_retries", None)
            startup_success = args.pop("health_startup_success", None)

            startup_config = {}
            if startup_cmd is not None:
                startup_config["Test"] = ["CMD-SHELL", startup_cmd]
            if startup_interval is not None:
                startup_config["Interval"] = prepare_duration_ns(startup_interval)
            if startup_timeout is not None:
                startup_config["Timeout"] = prepare_duration_ns(startup_timeout)
            if startup_retries is not None:
                startup_config["Retries"] = int(startup_retries)
            if startup_success is not None:
                startup_config["Successes"] = int(startup_success)
            if startup_config:
                params["startupHealthConfig"] = startup_config

            health_log_dest = args.pop("health_log_destination", None)
            if health_log_dest is not None:
                params["healthLogDestination"] = health_log_dest

            health_max_count = args.pop("health_max_log_count", None)
            if health_max_count is not None:
                params["healthMaxLogCount"] = int(health_max_count)

            health_max_size = args.pop("health_max_logs_size", None)
            if health_max_size is not None:
                params["healthMaxLogSize"] = int(health_max_size)

            health_on_failure = args.pop("health_on_failure", None)
            if health_on_failure is not None:
                if params.get("health_check_on_failure_action") is not None:
                    raise ValueError(
                        "Cannot set both 'health_on_failure' and "
                        "'health_check_on_failure_action'. Use one or the other."
                    )
                action = HEALTH_ON_FAILURE_ACTION.get(health_on_failure.lower())
                if action is None:
                    valid = ", ".join(sorted(HEALTH_ON_FAILURE_ACTION))
                    raise ValueError(
                        f"Invalid health_on_failure value: {health_on_failure!r}. "
                        f"Must be one of: {valid}"
                    )
                params["health_check_on_failure_action"] = action

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
            extended_mode = value.get("extended_mode", [])
            if not isinstance(extended_mode, list):
                raise ValueError("'extended_mode' value should be a list")

            options = extended_mode
            mode = value.get("mode")
            if mode is not None:
                if not isinstance(mode, str):
                    raise ValueError("'mode' value should be a str")
                options.append(mode)

            # The Podman API only supports named volumes through the ``volume`` parameter. Directory
            # mounting needs to happen through the ``mounts`` parameter. Luckily the translation
            # isn't too complicated so we can just do it for the user if we suspect that the key
            # isn't a named volume.
            if NAMED_VOLUME_PATTERN.match(key):
                volume = {"Name": key, "Dest": value["bind"], "Options": options}
                params["volumes"].append(volume)
            else:
                mount_point = {
                    "destination": value["bind"],
                    "options": options,
                    "source": key,
                    "type": "bind",
                }
                params["mounts"].append(mount_point)

        for item in args.pop("secrets", []):
            if isinstance(item, Secret):
                params["secrets"].append({"source": item.id})
            elif isinstance(item, str):
                params["secrets"].append({"source": item})
            elif isinstance(item, dict):
                secret = {}
                secret_opts = ["source", "target", "uid", "gid", "mode"]
                for k, v in item.items():
                    if k in secret_opts:
                        secret.update({k: v})
                params["secrets"].append(secret)

        if "secret_env" in args:
            params["secret_env"] = args.pop("secret_env", {})

        if "cgroupns" in args:
            params["cgroupns"] = normalize_nsmode(args.pop("cgroupns"))

        if "ipc_mode" in args:
            params["ipcns"] = normalize_nsmode(args.pop("ipc_mode"))

        if isinstance(network_mode, dict):
            params["netns"] = network_mode
        elif network_mode:
            # Mirrors ParseNetworkFlag: "<mode>:<value>" carries a value or options.
            mode, _, value = network_mode.partition(":")
            if mode == "default":
                params["netns"] = {"nsmode": "private"}
            elif mode == "bridge":
                params["netns"] = {"nsmode": "bridge"}
                if value:
                    if "default" in user_networks:
                        raise ValueError('network "default" is set in both network and networks')
                    # The server resolves the special "default" name to the default network.
                    params["networks"] = {
                        **(params["networks"] or {}),
                        "default": CreateMixin._parse_network_options(value),
                    }
            elif mode in ("pasta", "slirp4netns") and value:
                params["netns"] = {"nsmode": mode}
                params["network_options"] = {
                    **(params["network_options"] or {}),
                    mode: value.split(","),
                }
            else:
                # "container:<id>", "ns:<path>" and plain modes.
                params["netns"] = normalize_nsmode(network_mode)
        elif networks:
            # As `podman run --network <name>` does: joining a network requires bridge mode.
            params["netns"] = {"nsmode": "bridge"}

        if "pid_mode" in args:
            params["pidns"] = normalize_nsmode(args.pop("pid_mode"))

        if "userns_mode" in args:
            params["userns"] = normalize_nsmode(args.pop("userns_mode"))

        if "uts_mode" in args:
            params["utsns"] = normalize_nsmode(args.pop("uts_mode"))

        CreateMixin._apply_security_opt(params, args.pop("security_opt", None))

        if len(args) > 0:
            raise TypeError(
                "Unknown keyword argument(s): " + " ,".join(f"'{k}'" for k in args.keys())
            )

        return params

    @staticmethod
    def _parse_network_options(options: str) -> dict[str, Any]:
        """Map "ip=...,mac=...,alias=..." per-network options to the libpod format.

        Mirrors parseBridgeNetworkOptions in Podman's pkg/specgen/namespaces.go.
        """
        opts: dict[str, Any] = {}
        if not options:
            return opts
        for item in options.split(","):
            key, _, val = item.partition("=")
            if key in ("ip", "ip6"):
                opts.setdefault("static_ips", []).append(val)
            elif key == "alias":
                opts.setdefault("aliases", []).append(val)
            elif key == "mac":
                opts["static_mac"] = val
            elif key == "interface_name":
                opts["interface_name"] = val
            else:
                opts.setdefault("options", {})[key] = val
        return opts

    @staticmethod
    def _is_network_mode(network: str) -> bool:
        """Whether ``network`` is a namespace mode keyword rather than a network name."""
        mode, sep, _ = network.partition(":")
        if sep:
            return mode in _NETWORK_MODES_WITH_OPTIONS or mode in _NETWORK_MODES_WITH_VALUE
        return mode in _NETWORK_MODES or mode in _NETWORK_MODES_WITH_OPTIONS
