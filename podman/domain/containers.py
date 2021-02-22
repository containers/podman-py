"""Model and Manager for Container resources."""
from signal import SIGKILL
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from podman.api.client import APIClient
from podman.domain.images import Image
from podman.domain.manager import Manager, PodmanResource
from podman.errors import APIError, NotFound


class Container(PodmanResource):
    """Details and configuration for a container managed by the Podman service."""

    @property
    def name(self) -> Optional[str]:
        """Returns container's name."""
        if "name" in self.attrs:
            return self.attrs["Name"].lstrip("/")
        return None

    @property
    def image(self) -> Image:
        """Returns Image object used to create Container."""
        if "ImageID" in self.attrs:
            image_id = self.attrs["ImageId"]
        elif "Image" in self.attrs:
            image_id = self.attrs["Image"]
        else:
            image_id = None
        return self.client.images.get(image_id.split(":")[1])

    @property
    def labels(self) -> Dict[str, str]:
        """Returns labels associated with container."""
        if "Config" in self.attrs and "Labels" in self.attrs["Config"]:
            return self.attrs["Config"]["Labels"]
        return {}

    @property
    def status(self) -> str:
        """Returns operational status of container.

        Example:
            'running', 'stopped', 'exited'
        """
        if isinstance(self.attrs['State'], dict):
            return self.attrs['State']['Status']
        return self.attrs['State']

    @property
    def ports(self) -> Dict[str, int]:
        """Returns ports exposed by container."""
        if "NetworkSettings" in self.attrs and "Ports" in self.attrs["NetworkSettings"]:
            return self.attrs["NetworkSettings"]["Ports"]
        return {}

    def attach(self, **kwargs) -> Union[str, Iterator[str]]:
        """Attach to container's tty.

        Keyword Args:
             stdout (bool): Include stdout. Default: True
             stderr (bool): Include stderr. Default: True
             stream (bool): Return iterator of string(s) vs single string. Default: False
             logs (bool): Include previous container output. Default: False
        """
        return self.client.api.attach(self.id, **kwargs)

    def attach_socket(self, **kwargs):
        """TBD."""
        raise NotImplementedError

    def commit(self, repository: str = None, tag: str = None, **kwargs) -> Image:
        """Save container to given repository using given parameters.

        Args:
            repository: Where to save Image.
            tag: tag to push with Image.

        Keyword Args:
            message (str): Commit message to include with Image.
            author (str): Name of commit author.
            changes (str): Instructions to apply during commit.
            conf (Dict[str, Any]): Configuration for the container.

            See https://docs.podman.io/en/latest/_static/api.html#operation/libpodCommitContainer
        """
        raise NotImplementedError

    def diff(self) -> str:
        """Report changes on container's filesytem."""

        raise NotImplementedError

    def exec_run(
        self,
        cmd: Union[str, List[str]],
        stdout: bool = True,
        stderr: bool = True,
        stdin: bool = False,
        tty: bool = False,
        privileged: bool = False,
        user=None,
        detach: bool = False,
        stream: bool = False,
        socket: bool = False,
        environment: Union[Mapping[str, str], List[str]] = None,
        workdir: str = None,
        demux: bool = False,
    ) -> Tuple[
        Optional[int], Union[Iterator[bytes], Any, Tuple[bytes, bytes]]
    ]:  # pylint: disable=too-many-arguments,unused-argument
        """Run given command inside container and return results.

        Args:
            cmd: Command to be executed
            stdout: Attach to stdout. Default: True
            stderr: Attach to stderr. Default: True
            stdin: Attach to stdin. Default: False
            tty: Allocate a pseudo-TTY. Default: False
            privileged: Run as privileged.
            user: User to execute command as. Default: root
            detach: If true, detach from the exec command.
                Default: False
            stream: Stream response data. Default: False
            socket: Return the connection socket to allow custom
                read/write operations. Default: False
            environment: A dictionary or a List[str]ings in
                the following format ["PASSWORD=xxx"] or
                {"PASSWORD": "xxx"}.
            workdir: Path to working directory for this exec session
            demux: Return stdout and stderr separately
        """
        if user is None:
            user = "root"

        raise NotImplementedError

    def export(self, chunk_size: int = 1024 * 2048) -> Iterator[bytes]:
        """Download container's filesystem contents as a tar archive.

        Args:
            chunk_size: <= number of bytes to return for each iteration of the generator.
        """
        raise NotImplementedError

    def get_archive(self, path: str, chunk_size: int = 1024 * 2048) -> Tuple[bytes, Dict[str, Any]]:
        """Download a file or folder from the container's filesystem.

        Args:
            path: Path to file or folder.
            chunk_size: <= number of bytes to return for each iteration of the generator.

        Returns:
            First element is a raw tar data stream.
            Second element is a dict containing stat information on the specified path.
        """
        raise NotImplementedError

    def kill(self, signal: Union[str, int, None] = None) -> None:
        """Send signal to container. """
        if signal is None:
            signal = SIGKILL
        raise NotImplementedError

    def logs(self, **kwargs) -> Union[str, Iterator[str]]:
        """Get logs from container.

        Keyword Args:
            stdout (bool): Include stdout. Default: True
            stderr (bool): Include stderr. Default: True
            stream (bool): Return generator of strings as the response. Default: False
            timestamps (bool): Show timestamps in output. Default: False
            tail (Union[str, int]): Output specified number of lines at the end of
                logs. Either an integer of number of lines or the string all. Default: all
            since (Union[datetime, int]): Show logs since a given datetime or
                integer epoch (in seconds)
            follow (bool): Follow log output. Default: False
            until (Union[datetime, int]): Show logs that occurred before the given
                datetime or integer epoch (in seconds)
        """
        raise NotImplementedError

    def pause(self) -> None:
        """Pause processes within container."""
        raise NotImplementedError

    def put_archive(self, path: Union[bytes, str], data: bytes) -> bool:
        """Upload contents of tar archive to container writing to path.

        Notes:
            - path must exist.
        """
        if not path or not data:
            raise ValueError("path and data (tar archive) are required parameters.")

        raise NotImplementedError

    def remove(self, **kwargs) -> None:
        """Delete container.
        Keyword Args:
            v (bool): Delete associated volumes as well. Default: False.
            link (bool): ignored.
            force (bool): Kill a running container before deleting. Default: False.
        """
        raise NotImplementedError

    def rename(self, name: str) -> None:
        """Rename container.

        Args:
            name: new name for container.
        """
        if not name:
            raise ValueError("name is a required parameter.")
        raise NotImplementedError

    def resize(self, height: int = None, width: int = None) -> None:
        """Resize the tty session.

        Args:
            height: New height of tty session.
            width: New width of tty session.
        """
        raise NotImplementedError

    def restart(self, **kwargs) -> None:
        """Restart processes in container.

        Keyword Args:
            timeout (int): Seconds to wait for container to stop before killing container.
                Default: 10
        """
        if "timeout" not in kwargs:
            kwargs["timeout"] = 10

        raise NotImplementedError

    def start(self, **kwargs) -> None:
        """Start processes in container."""
        raise NotImplementedError

    def stats(self, **kwargs) -> Union[Sequence[Dict[str, bytes]], bytes]:
        """Return statistics for container.

        Keyword Args:
            decode (bool): If True and stream is True, stream will be decoded into dict's.
                Default: False.
            stream (bool): Stream statistics until cancelled. Default: True.
        """
        raise NotImplementedError

    def stop(self, **kwargs):
        """Stop container.

        Keyword Args:
            timeout (int): Number of seconds to wait on container to stop before killing it.
                Default: 10
        """
        if "timeout" not in kwargs:
            kwargs["timeout"] = 10
        raise NotImplementedError

    def top(self, **kwargs) -> str:
        """Report on running processes in container.

        Keyword Args:
            ps_args (str): Optional arguments passed to ps.
        """
        raise NotImplementedError

    def unpause(self):
        """Unpause processes in container."""
        raise NotImplementedError

    def update(self):
        """Unsupported operation."""
        raise NotImplementedError("container update is not supported by Podman.")

    def wait(self, **kwargs) -> Dict[str, Any]:
        """Block until container enters given state.

        Keyword Args:
            timeout (int): Number of seconds to wait for container to stop.
            condition (str): Container state on which to release, values:
                not-running (default), next-exit or removed.

        Returns:
              API response as a dict, including the container's exit code under the key StatusCode.

        Raises:
              ReadTimeoutError: if the timeout is exceeded.
              APIError: if the service returns as error.
        """
        raise NotImplementedError


class ContainerManager(Manager):
    """Specialized Manager for Container resources."""

    # Abstract methods (create,get,list) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=arguments-differ

    resource = Container

    def __init__(self, client: APIClient) -> None:
        """Initiate ContainManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

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
            auto_remove (bool): enable auto-removal of the container on daemon side when the
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
                the container, as a dictionary or a List[str] in the format ["SOMEVARIABLE=xxx"].
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

        # TODO: Create container create
        _ = command
        # TODO: Get new container
        raise NotImplementedError

    def get(self, container_id: str) -> Container:
        """Get container by name or id.

        Args:
            container_id: Container name or id.

        Raises:
            NotFound: Container does not exist.
            APIError: Error return by service.
        """
        path = f"/containers/{container_id}/json"
        try:
            response = self.client.get(path)
        except OSError as e:
            raise APIError(path) from e

        if response.status_code == 404:
            raise NotFound(
                f"Container '{container_id}' not found.",
                response=response,
                explanation=f"Container '{container_id}'",
            )

        if response.status_code != 200:
            raise APIError(
                response.url, response=response, explanation=f"Container '{container_id}'"
            )

        return self.prepare_model(response.json())

    def list(
        self,
        all: bool = False,  # pylint: disable=redefined-builtin
        before: str = None,
        filters: Mapping[str, Any] = None,
        limit: int = -1,
        since: str = None,
        sparse: bool = False,
        ignore_removed: bool = False,
    ) -> List[Container]:
        """Report on containers.

        Args:
            all: If False, only show running containers. Default: False.
            since: Show containers created after container name or id given.
            before: Show containers created before container name or id given.
            limit: Show last N created containers.
            filters: Filter container reported.
                Available filters:

                - exited (int): Only containers with specified exit code
                - status (str): One of restarting, running, paused, exited
                - label (Union[str, List[str]]): format either "key", "key=value" or a list of such.
                - id (str): The id of the container.
                - name (str): The name of the container.
                - ancestor (str): Filter by container ancestor. Format of
                    <image-name>[:tag], <image-id>, or <image@digest>.
                - before (str): Only containers created before a particular container.
                    Give the container name or id.
                - since (str): Only containers created after a particular container.
                    Give container name or id.
            sparse: ignored
            ignore_removed: If True, ignore failures due to missing containers.

        Raises:
            APIError: If service returns an error.
        """

        _ = all
        _ = before
        _ = filters
        _ = limit
        _ = since
        _ = sparse
        _ = ignore_removed
        raise NotImplementedError

    def prune(self, filters: Mapping[str, str] = None) -> Dict[str, Any]:
        """Delete stopped containers.

        Args:
            filters: TBD

        Returns:
            List of deleted container id's and the freed disk space in bytes.

        Raises:
            APIError: If service reports an error
        """
        raise NotImplementedError
