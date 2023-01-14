"""Model and Manager for Container resources."""
import io
import json
import logging
import shlex
from contextlib import suppress
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple, Union

import requests
from requests import Response

from podman import api
from podman.domain.images import Image
from podman.domain.images_manager import ImagesManager
from podman.domain.manager import PodmanResource
from podman.errors import APIError

logger = logging.getLogger("podman.containers")


class Container(PodmanResource):
    """Details and configuration for a container managed by the Podman service."""

    @property
    def name(self):
        """str: Returns container's name."""
        with suppress(KeyError):
            if 'Name' in self.attrs:
                return self.attrs["Name"].lstrip("/")
            return self.attrs["Names"][0].lstrip("/")
        return None

    @property
    def image(self):
        """podman.domain.images.Image: Returns Image object used to create Container."""
        if "Image" in self.attrs:
            image_id = self.attrs["Image"]

            return ImagesManager(client=self.client).get(image_id)
        return Image()

    @property
    def labels(self):
        """dict[str, str]: Returns labels associated with container."""
        with suppress(KeyError):
            if "Labels" in self.attrs:
                return self.attrs["Labels"]
            return self.attrs["Config"]["Labels"]
        return {}

    @property
    def status(self):
        """Literal["running", "stopped", "exited", "unknown"]: Returns status of container."""
        with suppress(KeyError):
            return self.attrs["State"]["Status"]
        return "unknown"

    @property
    def ports(self):
        """dict[str, int]: Return ports exposed by container."""
        with suppress(KeyError):
            return self.attrs["NetworkSettings"]["Ports"]
        return {}

    def attach(self, **kwargs) -> Union[str, Iterator[str]]:
        """Attach to container's tty.

        Keyword Args:
             stdout (bool): Include stdout. Default: True
             stderr (bool): Include stderr. Default: True
             stream (bool): Return iterator of string(s) vs single string. Default: False
             logs (bool): Include previous container output. Default: False

        Raises:
            NotImplementedError: method not implemented.
        """
        raise NotImplementedError()

    def attach_socket(self, **kwargs):
        """Not Implemented.

        Raises:
            NotImplementedError: method not implemented.
        """
        raise NotImplementedError()

    def commit(self, repository: str = None, tag: str = None, **kwargs) -> Image:
        """Save container to given repository.

        Args:
            repository: Where to save Image
            tag: Tag to push with Image

        Keyword Args:
            author (str): Name of commit author
            changes (List[str]): Instructions to apply during commit
            comment (str): Commit message to include with Image, overrides keyword message
            conf (dict[str, Any]): Ignored.
            format (str): Format of the image manifest and metadata
            message (str): Commit message to include with Image
            pause (bool): Pause the container before committing it
        """
        params = {
            "author": kwargs.get("author"),
            "changes": kwargs.get("changes"),
            "comment": kwargs.get("comment", kwargs.get("message")),
            "container": self.id,
            "format": kwargs.get("format"),
            "pause": kwargs.get("pause"),
            "repo": repository,
            "tag": tag,
        }
        response = self.client.post("/commit", params=params)
        response.raise_for_status()

        body = response.json()
        return ImagesManager(client=self.client).get(body["Id"])

    def diff(self) -> List[Dict[str, int]]:
        """Report changes of a container's filesystem.

        Raises:
            APIError: when service reports an error
        """
        response = self.client.get(f"/containers/{self.id}/changes")
        response.raise_for_status()
        return response.json()

    # pylint: disable=too-many-arguments,unused-argument
    def exec_run(
        self,
        cmd: Union[str, List[str]],
        stdout: bool = True,
        stderr: bool = True,
        stdin: bool = False,
        tty: bool = True,
        privileged: bool = False,
        user=None,
        detach: bool = False,
        stream: bool = False,
        socket: bool = False,
        environment: Union[Mapping[str, str], List[str]] = None,
        workdir: str = None,
        demux: bool = False,
    ) -> Tuple[Optional[int], Union[Iterator[bytes], Any, Tuple[bytes, bytes]]]:
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
            First item is the command response code
            Second item is the requests response content

        Raises:
            NotImplementedError: method not implemented.
            APIError: when service reports error
        """
        # pylint: disable-msg=too-many-locals
        user = user or "root"
        if isinstance(environment, dict):
            environment = [f"{k}={v}" for k, v in environment.items()]
        data = {
            "AttachStderr": stderr,
            "AttachStdin": stdin,
            "AttachStdout": stdout,
            "Cmd": cmd if isinstance(cmd, list) else shlex.split(cmd),
            # "DetachKeys": detach,  # This is something else
            "Env": environment,
            "Privileged": privileged,
            "Tty": tty,
            "User": user,
            "WorkingDir": workdir,
        }
        # create the exec instance
        response = self.client.post(f"/containers/{self.name}/exec", data=json.dumps(data))
        response.raise_for_status()
        exec_id = response.json()['Id']
        # start the exec instance, this will store command output
        start_resp = self.client.post(
            f"/exec/{exec_id}/start", data=json.dumps({"Detach": detach, "Tty": tty})
        )
        start_resp.raise_for_status()
        # get and return exec information
        response = self.client.get(f"/exec/{exec_id}/json")
        response.raise_for_status()
        return response.json().get('ExitCode'), start_resp.content

    def export(self, chunk_size: int = api.DEFAULT_CHUNK_SIZE) -> Iterator[bytes]:
        """Download container's filesystem contents as a tar archive.

        Args:
            chunk_size: <= number of bytes to return for each iteration of the generator.

        Yields:
            tarball in size/chunk_size chunks

        Raises:
            NotFound: when container has been removed from service
            APIError: when service reports an error
        """
        response = self.client.get(f"/containers/{self.id}/export", stream=True)
        response.raise_for_status()

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
            Second item is a dict containing os.stat() information on the specified path.
        """
        response = self.client.get(f"/containers/{self.id}/archive", params={"path": [path]})
        response.raise_for_status()

        stat = response.headers.get("x-docker-container-path-stat", None)
        stat = api.decode_header(stat)
        return response.iter_content(chunk_size=chunk_size), stat

    def inspect(self) -> Dict:
        """Inspect a container.

        Raises:
            APIError: when service reports an error
        """
        response = self.client.get(f"/containers/{self.id}/json")
        response.raise_for_status()
        return response.json()

    def kill(self, signal: Union[str, int, None] = None) -> None:
        """Send signal to container.

        Raises:
            APIError: when service reports an error
        """
        response = self.client.post(f"/containers/{self.id}/kill", params={"signal": signal})
        response.raise_for_status()

    def logs(self, **kwargs) -> Union[bytes, Iterator[bytes]]:
        """Get logs from the container.

        Keyword Args:
            stdout (bool): Include stdout. Default: True
            stderr (bool): Include stderr. Default: True
            stream (bool): Return generator of strings as the response. Default: False
            timestamps (bool): Show timestamps in output. Default: False
            tail (Union[str, int]): Output specified number of lines at the end of
                logs.  Integer representing the number of lines to display, or the string all.
                Default: all
            since (Union[datetime, int]): Show logs since a given datetime or
                integer epoch (in seconds)
            follow (bool): Follow log output. Default: False
            until (Union[datetime, int]): Show logs that occurred before the given
                datetime or integer epoch (in seconds)
        """
        stream = bool(kwargs.get("stream", False))
        params = {
            "follow": kwargs.get("follow", kwargs.get("stream", None)),
            "since": api.prepare_timestamp(kwargs.get("since")),
            "stderr": kwargs.get("stderr", None),
            "stdout": kwargs.get("stdout", True),
            "tail": kwargs.get("tail"),
            "timestamps": kwargs.get("timestamps"),
            "until": api.prepare_timestamp(kwargs.get("until")),
        }

        response = self.client.get(f"/containers/{self.id}/logs", stream=stream, params=params)
        response.raise_for_status()

        if stream:
            return api.stream_frames(response)
        return api.frames(response)

    def pause(self) -> None:
        """Pause processes within the container."""
        response = self.client.post(f"/containers/{self.id}/pause")
        response.raise_for_status()

    def put_archive(self, path: str, data: bytes = None) -> bool:
        """Upload tar archive containing a file or folder to be written into container.

        Args:
            path: File to write data into
            data: Contents to write to file, when None path will be read on client to
                  build tarfile.

        Returns:
            True when successful

        Raises:
            APIError: when server reports error
        """
        if path is None:
            raise ValueError("'path' is a required argument.")

        if data is None:
            data = api.create_tar("/", path)

        response = self.client.put(
            f"/containers/{self.id}/archive", params={"path": path}, data=data
        )
        return response.ok

    def remove(self, **kwargs) -> None:
        """Delete container.

        Keyword Args:
            v (bool): Delete associated volumes as well.
            link (bool): Ignored.
            force (bool): Kill a running container before deleting.
        """
        self.manager.remove(self.id, **kwargs)

    def rename(self, name: str) -> None:
        """Rename container.

        Container updated in-situ to avoid reload().

        Args:
            name: New name for container.
        """
        if not name:
            raise ValueError("'name' is a required argument.")

        response = self.client.post(f"/containers/{self.id}/rename", params={"name": name})
        response.raise_for_status()

        self.attrs["Name"] = name  # shortcut to avoid needing reload()

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
        response.raise_for_status()

    def restart(self, **kwargs) -> None:
        """Restart processes in container.

        Keyword Args:
            timeout (int): Seconds to wait for container to stop before killing container.
        """
        params = {"timeout": kwargs.get("timeout")}
        post_kwargs = {}
        if kwargs.get("timeout"):
            post_kwargs["timeout"] = float(params["timeout"]) * 1.5

        response = self.client.post(f"/containers/{self.id}/restart", params=params, **post_kwargs)
        response.raise_for_status()

    def start(self, **kwargs) -> None:
        """Start processes in container.

        Keyword Args:
            detach_keys: Override the key sequence for detaching a container (Podman only)
        """
        response = self.client.post(
            f"/containers/{self.id}/start", params={"detachKeys": kwargs.get("detach_keys")}
        )
        response.raise_for_status()

    def stats(self, **kwargs) -> Union[Sequence[Dict[str, bytes]], bytes]:
        """Return statistics for container.

        Keyword Args:
            decode (bool): If True and stream is True, stream will be decoded into dict's.
                Default: False.
            stream (bool): Stream statistics until cancelled. Default: True.

        Raises:
            APIError: when service reports an error
        """
        # FIXME Errors in stream are not handled, need content and json to read Errors.
        stream = kwargs.get("stream", True)
        decode = kwargs.get("decode", False)

        params = {
            "containers": self.id,
            "stream": stream,
        }

        response = self.client.get("/containers/stats", params=params)
        response.raise_for_status()

        if stream:
            return self._stats_helper(decode, response.iter_lines())

        with io.StringIO() as buffer:
            for entry in response.text:
                buffer.write(json.dumps(entry) + "\n")
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

    def stop(self, **kwargs) -> None:
        """Stop container.

        Keyword Args:
            all (bool): When True, stop all containers. Default: False (Podman only)
            ignore (bool): When True, ignore error if container already stopped (Podman only)
            timeout (int): Number of seconds to wait on container to stop before killing it.
        """
        params = {"all": kwargs.get("all"), "timeout": kwargs.get("timeout")}

        post_kwargs = {}
        if kwargs.get("timeout"):
            post_kwargs["timeout"] = float(params["timeout"]) * 1.5

        response = self.client.post(f"/containers/{self.id}/stop", params=params, **post_kwargs)
        response.raise_for_status()

        if response.status_code == requests.codes.no_content:
            return

        if response.status_code == requests.codes.not_modified:
            if kwargs.get("ignore", False):
                return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def top(self, **kwargs) -> Union[Iterator[Dict[str, Any]], Dict[str, Any]]:
        """Report on running processes in the container.

        Keyword Args:
            ps_args (str): When given, arguments will be passed to ps
            stream (bool): When True, repeatedly return results. Default: False

        Raises:
            NotFound: when the container no longer exists
            APIError: when the service reports an error
        """
        params = {
            "ps_args": kwargs.get("ps_args"),
            "stream": kwargs.get("stream", False),
        }
        response = self.client.get(f"/containers/{self.id}/top", params=params)
        response.raise_for_status()

        if params["stream"]:
            self._top_helper(response)

        return response.json()

    @staticmethod
    def _top_helper(response: Response) -> Iterator[Dict[str, Any]]:
        for line in response.iter_lines():
            yield line

    def unpause(self) -> None:
        """Unpause processes in container."""
        response = self.client.post(f"/containers/{self.id}/unpause")
        response.raise_for_status()

    def update(self, **kwargs):
        """Update resource configuration of the containers.

        Raises:
            NotImplementedError: Podman service unsupported operation.
        """
        raise NotImplementedError("Container.update() is not supported by Podman service.")

    def wait(self, **kwargs) -> int:
        """Block until the container enters given state.

        Keyword Args:
            condition (Union[str, List[str]]): Container state on which to release.
                One or more of: "configured", "created", "running", "stopped",
                "paused", "exited", "removing", "stopping".
            interval (int): Time interval to wait before polling for completion.

        Returns:
            "Error" key has a dictionary value with the key "Message".

        Raises:
              NotFound: when Container not found
              ReadTimeoutError: when timeout is exceeded
              APIError: when service returns an error
        """
        condition = kwargs.get("condition")
        if isinstance(condition, str):
            condition = [condition]

        interval = kwargs.get("interval")

        params = {}
        if condition != []:
            params["condition"] = condition
        if interval != "":
            params["interval"] = interval

        # This API endpoint responds with a JSON encoded integer.
        # See:
        # https://docs.podman.io/en/latest/_static/api.html#tag/containers/operation/ContainerWaitLibpod
        response = self.client.post(f"/containers/{self.id}/wait", params=params)
        response.raise_for_status()
        return response.json()
