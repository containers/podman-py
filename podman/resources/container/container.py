from .utils import ExecResult
from ..model import Model
from ...constants import DEFAULT_DATA_CHUNK_SIZE
from ...errors import (
    PodmanException
)


class Container(Model):
    """
    Local representation of a container object. Detailed configuration may
    be accessed through the :py:attr:`attrs` attribute. Note that local
    attributes are cached; users may call :py:meth:`reload` to
    query the Docker daemon for the current properties, causing
    :py:attr:`attrs` to be refreshed.
    """
    @property
    def name(self):
        """ The name of the container. """
        if self.attrs.get('Name') is not None:
            return self.attrs['Name'].lstrip('/')

    @property
    def image(self):
        """ The image of the container. """
        image_id = self.attrs.get('ImageID', self.attrs['Image'])
        if image_id is None:
            return None
        return self.client.images.get(image_id.split(':')[1])

    @property
    def labels(self):
        """ The labels of a container as dictionary. """
        try:
            result = self.attrs['Config'].get('Labels')
            return result or {}
        except KeyError:
            raise PodmanException(
                'Label data is not available for sparse objects. Call reload()'
                ' to retrieve all information'
            )

    @property
    def status(self):
        """ The status of the container. For example, ``running``, or ``exited``. """
        if isinstance(self.attrs['State'], dict):
            return self.attrs['State']['Status']
        return self.attrs['State']

    @property
    def ports(self):
        """ The ports that the container exposes as a dictionary. """
        return self.attrs.get('NetworkSettings', {}).get('Ports', {})

    def attach(self, **kwargs):
        """
        Attach to this container.

        :py:meth:`logs` is a wrapper around this method, which you can
        use instead if you want to fetch/stream container output without first
        retrieving the entire backlog.

        Args:
            stdout (bool): Include stdout.
            stderr (bool): Include stderr.
            stream (bool): Return container output progressively as an iterator
                of strings, rather than a single string.
            logs (bool): Include the container's previous output.

        Returns:
            By default, the container's output as a single string.

            If ``stream=True``, an iterator of output strings.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.attach(self.id, **kwargs)

    def attach_socket(self, **kwargs):
        """
        Like :py:meth:`attach`, but returns the underlying socket-like object
        for the HTTP request.

        Args:
            params (dict): Dictionary of request parameters (e.g. ``stdout``,
                ``stderr``, ``stream``).
            ws (bool): Use websockets instead of raw HTTP.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.attach_socket(self.id, **kwargs)

    def commit(self, repository=None, tag=None, **kwargs):
        """
        Commit a container to an image. Similar to the ``docker commit``
        command.

        Args:
            repository (str): The repository to push the image to
            tag (str): The tag to push
            message (str): A commit message
            author (str): The name of the author
            changes (str): Dockerfile instructions to apply while committing
            conf (dict): The configuration for the container. See the
                `Engine API documentation
                <https://docs.docker.com/reference/api/docker_remote_api/>`_
                for full details.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """

        resp = self.client.api.commit(self.id, repository=repository, tag=tag,
                                      **kwargs)
        return self.client.images.get(resp['Id'])

    def diff(self):
        """
        Inspect changes on a container's filesystem.

        Returns:
            (str)

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.diff(self.id)

    def exec_run(self, cmd, stdout=True, stderr=True, stdin=False, tty=False,
                 privileged=False, user='', detach=False, stream=False,
                 socket=False, environment=None, workdir=None, demux=False):
        """
        Run a command inside this container. Similar to
        ``docker exec``.

        Args:
            cmd (str or list): Command to be executed
            stdout (bool): Attach to stdout. Default: ``True``
            stderr (bool): Attach to stderr. Default: ``True``
            stdin (bool): Attach to stdin. Default: ``False``
            tty (bool): Allocate a pseudo-TTY. Default: False
            privileged (bool): Run as privileged.
            user (str): User to execute command as. Default: root
            detach (bool): If true, detach from the exec command.
                Default: False
            stream (bool): Stream response data. Default: False
            socket (bool): Return the connection socket to allow custom
                read/write operations. Default: False
            environment (dict or list): A dictionary or a list of strings in
                the following format ``["PASSWORD=xxx"]`` or
                ``{"PASSWORD": "xxx"}``.
            workdir (str): Path to working directory for this exec session
            demux (bool): Return stdout and stderr separately

        Returns:
            (ExecResult): A tuple of (exit_code, output)
                exit_code: (int):
                    Exit code for the executed command or ``None`` if
                    either ``stream`` or ``socket`` is ``True``.
                output: (generator, bytes, or tuple):
                    If ``stream=True``, a generator yielding response chunks.
                    If ``socket=True``, a socket object for the connection.
                    If ``demux=True``, a tuple of two bytes: stdout and stderr.
                    A bytestring containing response data otherwise.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.exec_create(
            self.id, cmd, stdout=stdout, stderr=stderr, stdin=stdin, tty=tty,
            privileged=privileged, user=user, environment=environment,
            workdir=workdir,
        )
        exec_output = self.client.api.exec_start(
            resp['Id'], detach=detach, tty=tty, stream=stream, socket=socket,
            demux=demux
        )
        if socket or stream:
            return ExecResult(None, exec_output)

        return ExecResult(
            self.client.api.exec_inspect(resp['Id'])['ExitCode'],
            exec_output
        )

    def export(self, chunk_size=DEFAULT_DATA_CHUNK_SIZE):
        """
        Export the contents of the container's filesystem as a tar archive.

        Args:
            chunk_size (int): The number of bytes returned by each iteration
                of the generator. If ``None``, data will be streamed as it is
                received. Default: 2 MB

        Returns:
            (str): The filesystem tar archive

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.export(self.id, chunk_size)

    def get_archive(self, path, chunk_size=DEFAULT_DATA_CHUNK_SIZE):
        """
        Retrieve a file or folder from the container in the form of a tar
        archive.

        Args:
            path (str): Path to the file or folder to retrieve
            chunk_size (int): The number of bytes returned by each iteration
                of the generator. If ``None``, data will be streamed as it is
                received. Default: 2 MB

        Returns:
            (tuple): First element is a raw tar data stream. Second element is
            a dict containing ``stat`` information on the specified ``path``.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.

        Example:

            >>> f = open('./sh_bin.tar', 'wb')
            >>> bits, stat = container.get_archive('/bin/sh')
            >>> print(stat)
            {'name': 'sh', 'size': 1075464, 'mode': 493,
             'mtime': '2018-10-01T15:37:48-07:00', 'linkTarget': ''}
            >>> for chunk in bits:
            ...    f.write(chunk)
            >>> f.close()
        """
        return self.client.api.get_archive(self.id, path, chunk_size)

    def kill(self, signal=None):
        """
        Kill or send a signal to the container.

        Args:
            signal (str or int): The signal to send. Defaults to ``SIGKILL``

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """

        return self.client.api.kill(self.id, signal=signal)

    def logs(self, **kwargs):
        """
        Get logs from this container. Similar to the ``docker logs`` command.

        The ``stream`` parameter makes the ``logs`` function return a blocking
        generator you can iterate over to retrieve log output as it happens.

        Args:
            stdout (bool): Get ``STDOUT``. Default ``True``
            stderr (bool): Get ``STDERR``. Default ``True``
            stream (bool): Stream the response. Default ``False``
            timestamps (bool): Show timestamps. Default ``False``
            tail (str or int): Output specified number of lines at the end of
                logs. Either an integer of number of lines or the string
                ``all``. Default ``all``
            since (datetime or int): Show logs since a given datetime or
                integer epoch (in seconds)
            follow (bool): Follow log output. Default ``False``
            until (datetime or int): Show logs that occurred before the given
                datetime or integer epoch (in seconds)

        Returns:
            (generator or str): Logs from the container.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.logs(self.id, **kwargs)

    def pause(self):
        """
        Pauses all processes within this container.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.pause(self.id)

    def put_archive(self, path, data):
        """
        Insert a file or folder in this container using a tar archive as
        source.

        Args:
            path (str): Path inside the container where the file(s) will be
                extracted. Must exist.
            data (bytes): tar data to be extracted

        Returns:
            (bool): True if the call succeeds.

        Raises:
            :py:class:`~docker.errors.APIError` If an error occurs.
        """
        return self.client.api.put_archive(self.id, path, data)

    def remove(self, **kwargs):
        """
        Remove this container. Similar to the ``docker rm`` command.

        Args:
            v (bool): Remove the volumes associated with the container
            link (bool): Remove the specified link and not the underlying
                container
            force (bool): Force the removal of a running container (uses
                ``SIGKILL``)

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.remove_container(self.id, **kwargs)

    def rename(self, name):
        """
        Rename this container. Similar to the ``docker rename`` command.

        Args:
            name (str): New name for the container

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.rename(self.id, name)

    def resize(self, height, width):
        """
        Resize the tty session.

        Args:
            height (int): Height of tty session
            width (int): Width of tty session

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.resize(self.id, height, width)

    def restart(self, **kwargs):
        """
        Restart this container. Similar to the ``docker restart`` command.

        Args:
            timeout (int): Number of seconds to try to stop for before killing
                the container. Once killed it will then be restarted. Default
                is 10 seconds.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.restart(self.id, **kwargs)

    def start(self, **kwargs):
        """
        Start this container. Similar to the ``docker start`` command, but
        doesn't support attach options.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.start(self.id, **kwargs)

    def stats(self, **kwargs):
        """
        Stream statistics for this container. Similar to the
        ``docker stats`` command.

        Args:
            decode (bool): If set to true, stream will be decoded into dicts
                on the fly. Only applicable if ``stream`` is True.
                False by default.
            stream (bool): If set to false, only the current stats will be
                returned instead of a stream. True by default.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.stats(self.id, **kwargs)

    def stop(self, **kwargs):
        """
        Stops a container. Similar to the ``docker stop`` command.

        Args:
            timeout (int): Timeout in seconds to wait for the container to
                stop before sending a ``SIGKILL``. Default: 10

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.stop(self.id, **kwargs)

    def top(self, **kwargs):
        """
        Display the running processes of the container.

        Args:
            ps_args (str): An optional arguments passed to ps (e.g. ``aux``)

        Returns:
            (str): The output of the top

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.top(self.id, **kwargs)

    def unpause(self):
        """
        Unpause all processes within the container.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.unpause(self.id)

    def update(self, **kwargs):
        """
        Update resource configuration of the containers.

        Args:
            blkio_weight (int): Block IO (relative weight), between 10 and 1000
            cpu_period (int): Limit CPU CFS (Completely Fair Scheduler) period
            cpu_quota (int): Limit CPU CFS (Completely Fair Scheduler) quota
            cpu_shares (int): CPU shares (relative weight)
            cpuset_cpus (str): CPUs in which to allow execution
            cpuset_mems (str): MEMs in which to allow execution
            mem_limit (int or str): Memory limit
            mem_reservation (int or str): Memory soft limit
            memswap_limit (int or str): Total memory (memory + swap), -1 to
                disable swap
            kernel_memory (int or str): Kernel memory limit
            restart_policy (dict): Restart policy dictionary

        Returns:
            (dict): Dictionary containing a ``Warnings`` key.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.update_container(self.id, **kwargs)

    def wait(self, **kwargs):
        """
        Block until the container stops, then return its exit code. Similar to
        the ``docker wait`` command.

        Args:
            timeout (int): Request timeout
            condition (str): Wait until a container state reaches the given
                condition, either ``not-running`` (default), ``next-exit``,
                or ``removed``

        Returns:
            (dict): The API's response as a Python dictionary, including
                the container's exit code under the ``StatusCode`` attribute.

        Raises:
            :py:class:`requests.exceptions.ReadTimeout`
                If the timeout is exceeded.
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.wait(self.id, **kwargs)
