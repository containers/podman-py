"""Model and Manager for Container resources."""
import io
import json
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple, Union

from podman import api
from podman.domain.images import Image
from podman.domain.images_manager import ImagesManager
from podman.domain.manager import PodmanResource
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
        if "Image" in self.attrs:
            image_id = self.attrs["Image"].split(":")[1]
            return ImagesManager(client=self.client).get(image_id)
        return Image()

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
        if "State" in self.attrs and "Status" in self.attrs["State"]:
            return self.attrs["State"]["Status"]
        return "unknown"

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
        raise NotImplementedError()

    def attach_socket(self, **kwargs):
        """TBD."""
        raise NotImplementedError()

    def commit(self, repository: str = None, tag: str = None, **kwargs) -> Image:
        """Save container to given repository using given parameters.

        Args:
            repository: Where to save Image
            tag: Tag to push with Image

        Keyword Args:
            author (str): Name of commit author
            changes (List[str]): Instructions to apply during commit
            comment (List[str]): Instructions to apply while committing in Dockerfile format
            conf (Dict[str, Any]): Ignored
            format (str): Format of the image manifest and metadata
            message (str): Commit message to include with Image
            pause (bool): Pause the container before committing it

            See https://docs.podman.io/en/latest/_static/api.html#operation/libpodCommitContainer
        """
        params = {
            "author": kwargs.get("author", None),
            "changes": kwargs.get("changes", None),
            "comment": kwargs.get("comment", None),
            "container": self.id,
            "format": kwargs.get("format", None),
            "pause": kwargs.get("pause", None),
            "repo": repository,
            "tag": tag,
        }
        response = self.client.post("/commit", params=params)
        body = response.json()

        if response.status_code != 201:
            if response.status_code == 404:
                raise NotFound(body["cause"], response=response, explanation=body["message"])
            raise APIError(body["cause"], response=response, explanation=body["message"])

        return ImagesManager(client=self.client).get(body["ID"])

    def diff(self) -> List[Dict[str, int]]:
        """Report changes on container's filesystem.

        Raises:
            APIError when service reports error
        """
        response = self.client.get(f"/containers/{self.id}/changes")
        body = response.json()

        if response.status_code == 200:
            return body
        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

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
            environment: A dictionary or a List[str] in
                the following format ["PASSWORD=xxx"] or
                {"PASSWORD": "xxx"}.
            workdir: Path to working directory for this exec session
            demux: Return stdout and stderr separately

        Returns:
            TBD

        Raises:
            APIError when service reports error
        """
        if user is None:
            user = "root"

        raise NotImplementedError()

    def export(self, chunk_size: int = api.DEFAULT_CHUNK_SIZE) -> Iterator[bytes]:
        """Download container's filesystem contents as a tar archive.

        Args:
            chunk_size: <= number of bytes to return for each iteration of the generator.

        Yields:
            tarball in size/chunk_size chunks

        Raises:
            NotFound when container has been removed from service
            APIError when service reports an error
        """
        response = self.client.get(f"/containers/{self.id}/export", stream=True)

        if response.status_code != 200:
            body = response.json()
            if response.status_code == 404:
                raise NotFound(body["cause"], response=response, explanation=body["message"])
            raise APIError(body["cause"], response=response, explanation=body["message"])

        for out in response.iter_content(chunk_size=chunk_size):
            yield out

    def get_archive(
        self, path: str, chunk_size: int = api.DEFAULT_CHUNK_SIZE
    ) -> Tuple[Iterable, Dict[str, Any]]:
        """Download a file or folder from the container's filesystem.

        Args:
            path: Path to file or folder.
            chunk_size: <= number of bytes to return for each iteration of the generator.

        Returns:
            First item is a raw tar data stream.
            Second item is a dict containing stat information on the specified path.
        """
        response = self.client.get(f"/containers/{self.id}/archive", params={"path": [path]})
        if response.status_code != 200:
            body = response.json()
            if response.status_code == 404:
                raise NotFound(body["cause"], response=response, explanation=body["message"])
            raise APIError(body["cause"], response=response, explanation=body["message"])

        stat = response.headers.get('x-docker-container-path-stat', None)
        stat = api.decode_header(stat)
        return response.iter_content(chunk_size=chunk_size), stat

    def kill(self, signal: Union[str, int, None] = None) -> None:
        """Send signal to container. """
        params = {"signal": signal}

        response = self.client.post(f"/containers/{self.id}/kill", params=params)
        if response.status_code == 204:
            return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])

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
        raise NotImplementedError()

    def pause(self) -> None:
        """Pause processes within container."""
        response = self.client.post(f"/containers/{self.id}/pause")
        if response.status_code == 204:
            return

        body = response.json()
        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def put_archive(self, path: Union[bytes, str, None] = None, data: bytes = None) -> bool:
        """Upload tar archive containing a file or folder to be written into container.

        Args:
            path: File to write data into
            data: Contents to write to file

        Returns:
            True when successful

        Raises:
            APIError when server reports error

        Notes:
            - path must exist.
        """
        if not path or not data:
            raise ValueError("path and data (tar archive) are required parameters.")

        response = self.client.put(
            f"/containers/{self.id}/archive", params={"path": path}, data=data
        )
        return response.status_code == 200

    def remove(self, **kwargs) -> None:
        """Delete container.

        Keyword Args:
            v (bool): Delete associated volumes as well.
            link (bool): Ignored.
            force (bool): Kill a running container before deleting.
        """
        params = {
            "v": kwargs.get("v"),
            "force": kwargs.get("force"),
        }

        response = self.client.delete(f"/containers/{self.id}", params=params)
        if response.status_code == 204:
            return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def rename(self, name: Optional[str] = None) -> None:
        """Rename container.

        Args:
            name: New name for container.
        """
        if not name:
            raise ValueError("name is a required parameter.")

        response = self.client.post(f"/containers/{self.id}/rename", params={"name": name})
        if response.status_code == 204:
            self.attrs["Name"] = name
            return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def resize(self, height: int = None, width: int = None) -> None:
        """Resize the tty session.

        Args:
            height: New height of tty session.
            width: New width of tty session.
        """
        params = {
            "h": height,
            "w": width,
        }
        response = self.client.post(f"/containers/{self.id}/resize", params=params)
        if response.status_code == 200:
            return

        body = response.json()
        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def restart(self, **kwargs) -> None:
        """Restart processes in container.

        Keyword Args:
            timeout (int): Seconds to wait for container to stop before killing container.
        """
        connection_timeout = api.DEFAULT_TIMEOUT

        params = {}
        if "timeout" in kwargs:
            params = {"timeout": kwargs["timeout"]}
            connection_timeout += float(kwargs["timeout"])

        response = self.client.post(
            f"/containers/{self.id}/restart", params=params, timeout=connection_timeout
        )
        if response.status_code == 204:
            return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def start(self, **kwargs) -> None:
        """Start processes in container.

        Keyword Args:
            detach_keys: Override the key sequence for detaching a container (Podman only)
        """
        params = {}
        if "detach_keys" in kwargs:
            params = {"detachKeys": kwargs["detach_keys"]}

        response = self.client.post(f"/containers/{self.id}/start", params=params)
        if response.status_code == 204:
            return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def stats(self, **kwargs) -> Union[Sequence[Dict[str, bytes]], bytes]:
        """Return statistics for container.

        Keyword Args:
            decode (bool): If True and stream is True, stream will be decoded into dict's.
                Default: False.
            stream (bool): Stream statistics until cancelled. Default: True.

        Raises:
            APIError when service reports an error
        """
        # FIXME Errors in stream are not handled, need content and json to read Errors.
        stream = kwargs.get("stream", True)
        decode = kwargs.get("decode", False)

        params = {
            "containers": self.id,
            "stream": stream,
        }

        response = self.client.get("/containers/stats", params=params)

        if response.status_code != 200:
            body = response.json()
            if response.status_code == 404:
                raise NotFound(body["cause"], response=response, explanation=body["message"])
            raise APIError(body["cause"], response=response, explanation=body["message"])

        if stream:
            return self._stats_helper(decode, response.iter_lines())

        with io.StringIO() as buffer:
            for entry in response.text:
                buffer.writer(json.dumps(entry) + "\n")
            return buffer.getvalue()

    @staticmethod
    def _stats_helper(
        decode: bool, body: List[Dict[str, Any]]
    ) -> Iterator[Union[str, Dict[str, Any]]]:
        """Helper needed to allow stats() to return either a generator or a str."""
        for entry in body:
            if decode:
                yield json.loads(entry)
            else:
                yield entry

    def stop(self, **kwargs):
        """Stop container.

        Keyword Args:
            all (bool): When True, stop all containers. Default: False (Podman only)
            ignore (bool): When True, ignore error if container already stopped (Podman only)
            timeout (int): Number of seconds to wait on container to stop before killing it.
        """
        connection_timeout = api.DEFAULT_TIMEOUT

        params = {}
        if "all" in kwargs:
            params["all"] = kwargs["all"]
        if "timeout" in kwargs:
            params["timeout"] = kwargs["timeout"]
            connection_timeout += float(kwargs["timeout"])

        response = self.client.post(
            f"/containers/{self.id}/stop", params=params, timeout=connection_timeout
        )
        if response.status_code == 204:
            return

        if response.status_code == 304:
            if kwargs.get("ignore", False):
                return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def top(self, **kwargs) -> Dict[str, Any]:
        """Report on running processes in container.

        Keyword Args:
            ps_args (str): Optional arguments passed to ps
        """
        params = {
            "ps_args": kwargs.get("ps_args"),
            "stream": False,
        }
        response = self.client.get(f"/containers/{self.id}/top", params=params)
        body = response.json()

        if response.status_code != 200:
            if response.status_code == 404:
                raise NotFound(body["cause"], response=response, explanation=body["message"])
            raise APIError(body["cause"], response=response, explanation=body["message"])

        return body

    def unpause(self) -> None:
        """Unpause processes in container."""
        response = self.client.post(f"/containers/{self.id}/unpause")
        if response.status_code == 204:
            return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def update(self, **kwargs):
        """Update resource configuration of the containers.

        Note:
            Podman unsupported operation
        """
        raise NotImplementedError("container update is not supported by Podman.")

    def wait(self, **kwargs) -> Dict[str, Any]:
        """Block until container enters given state.

        Keyword Args:
            condition (str): Container state on which to release, values:
                not-running (default), next-exit or removed.
            timeout (int): Number of seconds to wait for container to stop.

        Returns:
              API response as a dict, including the container's exit code under the key StatusCode.

        Raises:
              ReadTimeoutError: If the timeout is exceeded.
              APIError: If the service returns as error.
        """
        params = {"condition": kwargs.get("condition", None)}
        response = self.client.post(f"/containers/{self.id}/wait", params=params)

        if response.status_code == 204:
            return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])
