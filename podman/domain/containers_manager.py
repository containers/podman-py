"""PodmanResource manager subclassed for Containers."""
import urllib
from typing import Any, ClassVar, Dict, List, Mapping, Sequence, Type, Union

from podman import api
from podman.domain.containers import Container
from podman.domain.images import Image
from podman.domain.manager import Manager
from podman.errors import APIError, NotFound


class ContainersManager(Manager):
    """Specialized Manager for Container resources.

    Attributes:
        resource: Container subclass of PodmanResource, factory method will create these.
    """

    resource: ClassVar[Type[Image]] = Container

    def run(
        self,
        image: Union[str, Image],
        command: Union[str, List[str]] = None,
        stdout=True,
        stderr=False,
        remove: bool = False,
        **kwargs,
    ) -> Union[Container, Sequence[str]]:
        """Run container.

        By default, run() will wait for the container to finish and return its logs.

        If detach=True, run() will start the container and return a Container object rather
            than logs.

        Args:
            image: Image to run.
            command: Command to run in the container.
            stdout: Include stdout. Default: True.
            stderr: Include stderr. Default: False.
            remove: Delete container when the container's processes exit. Default: False.

        Keyword Args:
            auto_remove (bool): Enable auto-removal of the container on daemon side when the
                container's process exits.
            blkio_weight_device (Dict[str, Any]): Block IO weight (relative device weight)
                in the form of: [{"Path": "device_path", "Weight": weight}].
            blkio_weight (int): Block IO weight (relative weight), accepts a weight value
                between 10 and 1000.
            cap_add (List[str]): Add kernel capabilities. For example, ["SYS_ADMIN", "MKNOD"].
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

                For example,
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
            healthcheck (Dict[str,str]): Specify a test to perform to check that the
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
            lxc_conf (Dict[str, str]): LXC config.
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
            mounts (List[str]): Specification for mounts to be added to the container. More
                powerful alternative to volumes. Each item in the list is expected to be a
                Mount object.
            name (str): The name for this container.
            nano_cpus (int):  CPU quota in units of 1e-9 CPUs.
            network (str): Name of the network this container will be connected to at creation time.
                You can connect to additional networks using Network.connect.
                Incompatible with network_mode.
            network_disabled (bool): Disable networking.
            network_mode (str): One of:

                - bridge: Create a new network stack for the container on
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
            ports (Dict[str, Union[int, Tuple[str, int], List[int]): Ports to bind inside
                the container.

                The keys of the dictionary are the ports to bind inside the container, either as an
                    integer or a string in the form port/protocol, where the protocol is either
                    tcp, udp, or sctp.

                The values of the dictionary are the corresponding ports to open on the host,
                    which can be either:

                - The port number, as an integer. For example,
                  {'2222/tcp': 3333} will expose port 2222 inside the container as port 3333 on the
                    host.
                - None, to assign a random host port. For example,
                  {'2222/tcp': None}.
                - A tuple of (address, port) if you want to specify the host interface. For example,
                  {'1111/tcp': ('127.0.0.1', 1111)}.
                - A list of integers, if you want to bind multiple host ports to a single container
                    port. For example, {'1111/tcp': [1234, 4567]}.

            privileged (bool): Give extended privileges to this container.
            publish_all_ports (bool): Publish all ports to the host.
            read_only (bool): Mount the container's root filesystem as read only.
            remove (bool): Remove the container when it has finished running. Default: False.
            restart_policy (Dict[str, Union[str, int]]): Restart the container when it exits.
                Configured as a dictionary with keys:

                - Name: One of on-failure, or always.
                - MaximumRetryCount: Number of times to restart the container on failure.

                For example:
                    {"Name": "on-failure", "MaximumRetryCount": 5}

            runtime (str): Runtime to use with this container.
            security_opt (List[str]): A List[str]ing values to customize labels for MLS systems,
                such as SELinux. shm_size (Union[str, int]): Size of /dev/shm (e.g. 1G).
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

                For example:

                    {
                        '/mnt/vol2': '',
                        '/mnt/vol1': 'size=3G,uid=1000'
                    }

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

                - bind The path to mount the volume inside the container
                - mode Either rw to mount the volume read/write, or ro to mount it read-only.

                For example:

                    {'/home/user1/': {'bind': '/mnt/vol2', 'mode': 'rw'},
                     '/var/www': {'bind': '/mnt/vol1', 'mode': 'ro'}}

            volumes_from (List[str]): List of container names or IDs to get volumes from.
            working_dir (str): Path to the working directory.
        """

        if isinstance(image, Image):
            image = image.id

        _ = command
        _ = stdout
        _ = stderr
        _ = remove
        _ = kwargs
        raise NotImplementedError

    def create(
        self, image: Union[Image, str], command: Union[str, List[str]] = None, **kwargs
    ) -> Container:
        """Create a container.

        See Container.run() for arguments. The following are ignored: stdout, stderr, and remove.

        Raises:
            ImageNotFound: If given image does not exist.
            APIError: If service returns an error.
        """
        if isinstance(image, Image):
            image = image.id

        _ = kwargs
        # TODO: Create container create
        _ = command
        # TODO: Get new container
        raise NotImplementedError

    # pylint is flagging 'container_id' here vs. 'key' parameter in super.get()
    def get(self, container_id: str) -> Container:  # pylint: disable=arguments-differ
        """Get container by name or id.

        Args:
            container_id: Container name or id.

        Raises:
            NotFound: Container does not exist.
            APIError: Error return by service.
        """
        container_id = urllib.parse.quote_plus(container_id)
        response = self.client.get(f"/containers/{container_id}/json")
        body = response.json()

        if response.status_code == 200:
            return self.prepare_model(body)

        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def list(self, *args, **kwargs) -> List[Container]:
        """Report on containers.

        Keyword Args:
            all: If False, only show running containers. Default: False.
            since: Show containers created after container name or id given.
            before: Show containers created before container name or id given.
            limit: Show last N created containers.
            filters: Filter container reported.
                Available filters:

                - exited (int): Only containers with specified exit code
                - status (str): One of restarting, running, paused, exited
                - label (Union[str, List[str]]): Format either "key", "key=value" or a list of such.
                - id (str): The id of the container.
                - name (str): The name of the container.
                - ancestor (str): Filter by container ancestor. Format of
                    <image-name>[:tag], <image-id>, or <image@digest>.
                - before (str): Only containers created before a particular container.
                    Give the container name or id.
                - since (str): Only containers created after a particular container.
                    Give container name or id.
            sparse: Ignored
            ignore_removed: If True, ignore failures due to missing containers.

        Raises:
            APIError: If service returns an error.
        """
        params = {
            "all": kwargs.get("all", None),
            "filters": kwargs.get("filters", dict()),
            "limit": kwargs.get("limit", None),
        }
        if "before" in kwargs:
            params["filters"]["before"] = kwargs.get('before')
        if "since" in kwargs:
            params["filters"]["since"] = kwargs.get('since')

        # filters formatted last because some kwargs need to be mapped into filters
        if len(params["filters"]) > 0:
            params["filters"] = api.format_filters(params["filters"])

        response = self.client.get("/containers/json", params=params)
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        containers: List[Container] = []
        for element in body:
            containers.append(self.prepare_model(element))
        return containers

    def prune(self, filters: Mapping[str, str] = None) -> Dict[str, Any]:
        """Delete stopped containers.

        Args:
            filters: Dict of criteria for determining containers to remove. Available keys are:
                - until (str): Delete containers before this time
                - label (List[str]): Labels associated with containers

        Returns:
            List of deleted container id's and the freed disk space in bytes.

        Raises:
            APIError: If service reports an error
        """
        params = dict()
        if filters is not None:
            params = {"filters", api.format_filters(filters)}

        response = self.client.post("/containers/prune", params=params)
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        results = {"ContainersDeleted": [], "SpaceReclaimed": 0}
        for entry in body:
            if entry.get("error", None) is not None:
                raise APIError(entry["error"], response=response, explanation=entry["error"])

            results["ContainersDeleted"].append(entry["id"])
            results["SpaceReclaimed"] += entry["space"]
        return results
