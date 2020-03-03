from .container import Container
from .utils import _create_container_args
from ..collection import Collection
from ..images import Image
from ...api.base import BaseAPIClient
from ...errors import (
    ContainerError, ImageNotFound,
    NotFound
)
from ...utils import version_gte


class ContainerCollection(Collection):
    model = Container

    def run(self, image, command=None, stdout=True, stderr=False,
            remove=False, **kwargs):
        """
        Run a container. By default, it will wait for the container to finish
        and return its logs, similar to ``docker run``.

        If the ``detach`` argument is ``True``, it will start the container
        and immediately return a :py:class:`Container` object, similar to
        ``docker run -d``.

        Example:
            Run a container and get its output:

            >>> import docker
            >>> client = docker.from_env()
            >>> client.containers.run('alpine', 'echo hello world')
            b'hello world\\n'

            Run a container and detach:

            >>> container = client.containers.run('bfirsh/reticulate-splines',
                                                  detach=True)
            >>> container.logs()
            'Reticulating spline 1...\\nReticulating spline 2...\\n'

        Args:
            image (str): The image to run.
            command (str or list): The command to run in the container.
            auto_remove (bool): enable auto-removal of the container on daemon
                side when the container's process exits.
            blkio_weight_device: Block IO weight (relative device weight) in
                the form of: ``[{"Path": "device_path", "Weight": weight}]``.
            blkio_weight: Block IO weight (relative weight), accepts a weight
                value between 10 and 1000.
            cap_add (list of str): Add kernel capabilities. For example,
                ``["SYS_ADMIN", "MKNOD"]``.
            cap_drop (list of str): Drop kernel capabilities.
            cgroup_parent (str): Override the default parent cgroup.
            cpu_count (int): Number of usable CPUs (Windows only).
            cpu_percent (int): Usable percentage of the available CPUs
                (Windows only).
            cpu_period (int): The length of a CPU period in microseconds.
            cpu_quota (int): Microseconds of CPU time that the container can
                get in a CPU period.
            cpu_rt_period (int): Limit CPU real-time period in microseconds.
            cpu_rt_runtime (int): Limit CPU real-time runtime in microseconds.
            cpu_shares (int): CPU shares (relative weight).
            cpuset_cpus (str): CPUs in which to allow execution (``0-3``,
                ``0,1``).
            cpuset_mems (str): Memory nodes (MEMs) in which to allow execution
                (``0-3``, ``0,1``). Only effective on NUMA systems.
            detach (bool): Run container in the background and return a
                :py:class:`Container` object.
            device_cgroup_rules (:py:class:`list`): A list of cgroup rules to
                apply to the container.
            device_read_bps: Limit read rate (bytes per second) from a device
                in the form of: `[{"Path": "device_path", "Rate": rate}]`
            device_read_iops: Limit read rate (IO per second) from a device.
            device_write_bps: Limit write rate (bytes per second) from a
                device.
            device_write_iops: Limit write rate (IO per second) from a device.
            devices (:py:class:`list`): Expose host devices to the container,
                as a list of strings in the form
                ``<path_on_host>:<path_in_container>:<cgroup_permissions>``.

                For example, ``/dev/sda:/dev/xvda:rwm`` allows the container
                to have read-write access to the host's ``/dev/sda`` via a
                node named ``/dev/xvda`` inside the container.
            dns (:py:class:`list`): Set custom DNS servers.
            dns_opt (:py:class:`list`): Additional options to be added to the
                container's ``resolv.conf`` file.
            dns_search (:py:class:`list`): DNS search domains.
            domainname (str or list): Set custom DNS search domains.
            entrypoint (str or list): The entrypoint for the container.
            environment (dict or list): Environment variables to set inside
                the container, as a dictionary or a list of strings in the
                format ``["SOMEVARIABLE=xxx"]``.
            extra_hosts (dict): Additional hostnames to resolve inside the
                container, as a mapping of hostname to IP address.
            group_add (:py:class:`list`): List of additional group names and/or
                IDs that the container process will run as.
            healthcheck (dict): Specify a test to perform to check that the
                container is healthy.
            hostname (str): Optional hostname for the container.
            init (bool): Run an init inside the container that forwards
                signals and reaps processes
            init_path (str): Path to the docker-init binary
            ipc_mode (str): Set the IPC mode for the container.
            isolation (str): Isolation technology to use. Default: `None`.
            kernel_memory (int or str): Kernel memory limit
            labels (dict or list): A dictionary of name-value labels (e.g.
                ``{"label1": "value1", "label2": "value2"}``) or a list of
                names of labels to set with empty values (e.g.
                ``["label1", "label2"]``)
            links (dict): Mapping of links using the
                ``{'container': 'alias'}`` format. The alias is optional.
                Containers declared in this dict will be linked to the new
                container using the provided alias. Default: ``None``.
            log_config (LogConfig): Logging configuration.
            lxc_conf (dict): LXC config.
            mac_address (str): MAC address to assign to the container.
            mem_limit (int or str): Memory limit. Accepts float values
                (which represent the memory limit of the created container in
                bytes) or a string with a units identification char
                (``100000b``, ``1000k``, ``128m``, ``1g``). If a string is
                specified without a units character, bytes are assumed as an
                intended unit.
            mem_reservation (int or str): Memory soft limit.
            mem_swappiness (int): Tune a container's memory swappiness
                behavior. Accepts number between 0 and 100.
            memswap_limit (str or int): Maximum amount of memory + swap a
                container is allowed to consume.
            mounts (:py:class:`list`): Specification for mounts to be added to
                the container. More powerful alternative to ``volumes``. Each
                item in the list is expected to be a
                :py:class:`docker.types.Mount` object.
            name (str): The name for this container.
            nano_cpus (int):  CPU quota in units of 1e-9 CPUs.
            network (str): Name of the network this container will be connected
                to at creation time. You can connect to additional networks
                using :py:meth:`Network.connect`. Incompatible with
                ``network_mode``.
            network_disabled (bool): Disable networking.
            network_mode (str): One of:

                - ``bridge`` Create a new network stack for the container on
                  on the bridge network.
                - ``none`` No networking for this container.
                - ``container:<name|id>`` Reuse another container's network
                  stack.
                - ``host`` Use the host network stack.

                Incompatible with ``network``.
            oom_kill_disable (bool): Whether to disable OOM killer.
            oom_score_adj (int): An integer value containing the score given
                to the container in order to tune OOM killer preferences.
            pid_mode (str): If set to ``host``, use the host PID namespace
                inside the container.
            pids_limit (int): Tune a container's pids limit. Set ``-1`` for
                unlimited.
            platform (str): Platform in the format ``os[/arch[/variant]]``.
                Only used if the method needs to pull the requested image.
            ports (dict): Ports to bind inside the container.

                The keys of the dictionary are the ports to bind inside the
                container, either as an integer or a string in the form
                ``port/protocol``, where the protocol is either ``tcp``,
                ``udp``, or ``sctp``.

                The values of the dictionary are the corresponding ports to
                open on the host, which can be either:

                - The port number, as an integer. For example,
                  ``{'2222/tcp': 3333}`` will expose port 2222 inside the
                  container as port 3333 on the host.
                - ``None``, to assign a random host port. For example,
                  ``{'2222/tcp': None}``.
                - A tuple of ``(address, port)`` if you want to specify the
                  host interface. For example,
                  ``{'1111/tcp': ('127.0.0.1', 1111)}``.
                - A list of integers, if you want to bind multiple host ports
                  to a single container port. For example,
                  ``{'1111/tcp': [1234, 4567]}``.

            privileged (bool): Give extended privileges to this container.
            publish_all_ports (bool): Publish all ports to the host.
            read_only (bool): Mount the container's root filesystem as read
                only.
            remove (bool): Remove the container when it has finished running.
                Default: ``False``.
            restart_policy (dict): Restart the container when it exits.
                Configured as a dictionary with keys:

                - ``Name`` One of ``on-failure``, or ``always``.
                - ``MaximumRetryCount`` Number of times to restart the
                  container on failure.

                For example:
                ``{"Name": "on-failure", "MaximumRetryCount": 5}``

            runtime (str): Runtime to use with this container.
            security_opt (:py:class:`list`): A list of string values to
                customize labels for MLS systems, such as SELinux.
            shm_size (str or int): Size of /dev/shm (e.g. ``1G``).
            stdin_open (bool): Keep ``STDIN`` open even if not attached.
            stdout (bool): Return logs from ``STDOUT`` when ``detach=False``.
                Default: ``True``.
            stderr (bool): Return logs from ``STDERR`` when ``detach=False``.
                Default: ``False``.
            stop_signal (str): The stop signal to use to stop the container
                (e.g. ``SIGINT``).
            storage_opt (dict): Storage driver options per container as a
                key-value mapping.
            stream (bool): If true and ``detach`` is false, return a log
                generator instead of a string. Ignored if ``detach`` is true.
                Default: ``False``.
            sysctls (dict): Kernel parameters to set in the container.
            tmpfs (dict): Temporary filesystems to mount, as a dictionary
                mapping a path inside the container to options for that path.

                For example:

                .. code-block:: python

                    {
                        '/mnt/vol2': '',
                        '/mnt/vol1': 'size=3G,uid=1000'
                    }

            tty (bool): Allocate a pseudo-TTY.
            ulimits (:py:class:`list`): Ulimits to set inside the container,
                as a list of :py:class:`docker.types.Ulimit` instances.
            use_config_proxy (bool): If ``True``, and if the docker client
                configuration file (``~/.docker/config.json`` by default)
                contains a proxy configuration, the corresponding environment
                variables will be set in the container being built.
            user (str or int): Username or UID to run commands as inside the
                container.
            userns_mode (str): Sets the user namespace mode for the container
                when user namespace remapping option is enabled. Supported
                values are: ``host``
            uts_mode (str): Sets the UTS namespace mode for the container.
                Supported values are: ``host``
            version (str): The version of the API to use. Set to ``auto`` to
                automatically detect the server's version. Default: ``1.35``
            volume_driver (str): The name of a volume driver/plugin.
            volumes (dict or list): A dictionary to configure volumes mounted
                inside the container. The key is either the host path or a
                volume name, and the value is a dictionary with the keys:

                - ``bind`` The path to mount the volume inside the container
                - ``mode`` Either ``rw`` to mount the volume read/write, or
                  ``ro`` to mount it read-only.

                For example:

                .. code-block:: python

                    {'/home/user1/': {'bind': '/mnt/vol2', 'mode': 'rw'},
                     '/var/www': {'bind': '/mnt/vol1', 'mode': 'ro'}}

            volumes_from (:py:class:`list`): List of container names or IDs to
                get volumes from.
            working_dir (str): Path to the working directory.

        Returns:
            The container logs, either ``STDOUT``, ``STDERR``, or both,
            depending on the value of the ``stdout`` and ``stderr`` arguments.

            ``STDOUT`` and ``STDERR`` may be read only if either ``json-file``
            or ``journald`` logging driver used. Thus, if you are using none of
            these drivers, a ``None`` object is returned instead. See the
            `Engine API documentation
            <https://docs.docker.com/engine/api/v1.30/#operation/ContainerLogs/>`_
            for full details.

            If ``detach`` is ``True``, a :py:class:`Container` object is
            returned instead.

        Raises:
            :py:class:`docker.errors.ContainerError`
                If the container exits with a non-zero exit code and
                ``detach`` is ``False``.
            :py:class:`docker.errors.ImageNotFound`
                If the specified image does not exist.
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        if isinstance(image, Image):
            image = image.id
        stream = kwargs.pop('stream', False)
        detach = kwargs.pop('detach', False)
        platform = kwargs.pop('platform', None)

        if detach and remove:
            if version_gte(self.client.api._version, '1.25'):
                kwargs["auto_remove"] = True
            else:
                raise RuntimeError("The options 'detach' and 'remove' cannot "
                                   "be used together in api versions < 1.25.")

        if kwargs.get('network') and kwargs.get('network_mode'):
            raise RuntimeError(
                'The options "network" and "network_mode" can not be used '
                'together.'
            )

        try:
            container = self.create(image=image, command=command,
                                    detach=detach, **kwargs)
        except ImageNotFound:
            self.client.images.pull(image, platform=platform)
            container = self.create(image=image, command=command,
                                    detach=detach, **kwargs)

        container.start()

        if detach:
            return container

        logging_driver = container.attrs['HostConfig']['LogConfig']['Type']

        out = None
        if logging_driver == 'json-file' or logging_driver == 'journald':
            out = container.logs(
                stdout=stdout, stderr=stderr, stream=True, follow=True
            )

        exit_status = container.wait()['StatusCode']
        if exit_status != 0:
            out = None
            if not kwargs.get('auto_remove'):
                out = container.logs(stdout=False, stderr=True)

        if remove:
            container.remove()
        if exit_status != 0:
            raise ContainerError(
                container, exit_status, command, image, out
            )

        return out if stream or out is None else b''.join(
            [line for line in out]
        )

    def create(self, image, command=None, **kwargs):
        """
        Create a container without starting it. Similar to ``docker create``.

        Takes the same arguments as :py:meth:`run`, except for ``stdout``,
        ``stderr``, and ``remove``.

        Returns:
            A :py:class:`Container` object.

        Raises:
            :py:class:`docker.errors.ImageNotFound`
                If the specified image does not exist.
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        if isinstance(image, Image):
            image = image.id
        kwargs['image'] = image
        kwargs['command'] = command
        kwargs['version'] = self.client.api._version
        create_kwargs = _create_container_args(kwargs)
        resp = self.client.api.create_container(**create_kwargs)
        return self.get(resp['Id'])

    def get(self, container_id):
        """
        Get a container by name or ID.

        Args:
            container_id (str): Container name or ID.

        Returns:
            A :py:class:`Container` object.

        Raises:
            :py:class:`docker.errors.NotFound`
                If the container does not exist.
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.inspect_container(container_id)
        return self.prepare_model(resp)

    def list(self, all=False, before=None, filters=None, limit=-1, since=None,
             sparse=False, ignore_removed=False):
        """
        List containers. Similar to the ``docker ps`` command.

        Args:
            all (bool): Show all containers. Only running containers are shown
                by default
            since (str): Show only containers created since Id or Name, include
                non-running ones
            before (str): Show only container created before Id or Name,
                include non-running ones
            limit (int): Show `limit` last created containers, include
                non-running ones
            filters (dict): Filters to be processed on the image list.
                Available filters:

                - `exited` (int): Only containers with specified exit code
                - `status` (str): One of ``restarting``, ``running``,
                    ``paused``, ``exited``
                - `label` (str|list): format either ``"key"``, ``"key=value"``
                    or a list of such.
                - `id` (str): The id of the container.
                - `name` (str): The name of the container.
                - `ancestor` (str): Filter by container ancestor. Format of
                    ``<image-name>[:tag]``, ``<image-id>``, or
                    ``<image@digest>``.
                - `before` (str): Only containers created before a particular
                    container. Give the container name or id.
                - `since` (str): Only containers created after a particular
                    container. Give container name or id.

                A comprehensive list can be found in the documentation for
                `docker ps
                <https://docs.docker.com/engine/reference/commandline/ps>`_.

            sparse (bool): Do not inspect containers. Returns partial
                information, but guaranteed not to block. Use
                :py:meth:`Container.reload` on resulting objects to retrieve
                all attributes. Default: ``False``
            ignore_removed (bool): Ignore failures due to missing containers
                when attempting to inspect containers from the original list.
                Set to ``True`` if race conditions are likely. Has no effect
                if ``sparse=True``. Default: ``False``

        Returns:
            (list of :py:class:`Container`)

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.containers(all=all, before=before,
                                          filters=filters, limit=limit,
                                          since=since)
        if sparse:
            return [self.prepare_model(r) for r in resp]
        else:
            containers = []
            for r in resp:
                try:
                    containers.append(self.get(r['Id']))
                # a container may have been removed while iterating
                except NotFound:
                    if not ignore_removed:
                        raise
            return containers

    def prune(self, filters=None):
        return self.client.api.prune_containers(filters=filters)
    prune.__doc__ = BaseAPIClient.prune_containers.__doc__

