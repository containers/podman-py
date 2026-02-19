"""Model and Manager for Container resources."""

import json
import logging
import shlex
from collections.abc import Iterable, Iterator, Mapping
from contextlib import suppress
from typing import Any, Optional, Union

import requests

from podman import api
from podman.api.output_utils import demux_output
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
        labels = None
        with suppress(KeyError):
            # Container created from ``list()`` operation
            if "Labels" in self.attrs:
                labels = self.attrs["Labels"]
            # Container created from ``get()`` operation
            else:
                labels = self.attrs["Config"].get("Labels", {})
        return labels or {}

    @property
    def status(self):
        """Literal["created", "initialized", "running", "stopped", "exited", "unknown"]:
        Returns status of container."""
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
            changes (list[str]): Instructions to apply during commit
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

    def diff(self) -> list[dict[str, int]]:
        """Report changes of a container's filesystem.

        Raises:
            APIError: when service reports an error
        """
        response = self.client.get(f"/containers/{self.id}/changes")
        response.raise_for_status()
        return response.json()

    # pylint: disable=too-many-arguments
    def exec_run(
        self,
        cmd: Union[str, list[str]],
        *,
        stdout: bool = True,
        stderr: bool = True,
        stdin: bool = False,
        tty: bool = False,
        privileged: bool = False,
        user=None,
        detach: bool = False,
        stream: bool = False,
        socket: bool = False,  # pylint: disable=unused-argument
        environment: Union[Mapping[str, str], list[str]] = None,
        workdir: str = None,
        demux: bool = False,
    ) -> tuple[
        Optional[int],
        Union[Iterator[Union[bytes, tuple[bytes, bytes]]], Any, tuple[bytes, bytes]],
    ]:
        """Run given command inside container and return results.

        Args:
            cmd: Command to be executed
            stdout: Attach to stdout. Default: True
            stderr: Attach to stderr. Default: True
            stdin: Attach to stdin. Default: False
            tty: Allocate a pseudo-TTY. Default: False
            privileged: Run as privileged.
            user: User to execute command as.
            detach: If true, detach from the exec command.
                Default: False
            stream: Stream response data. Ignored if ``detach`` is ``True``. Default: False
            socket: Return the connection socket to allow custom
                read/write operations. Default: False
            environment: A dictionary or a list[str] in
                the following format ["PASSWORD=xxx"] or
                {"PASSWORD": "xxx"}.
            workdir: Path to working directory for this exec session
            demux: Return stdout and stderr separately

        Returns:
            A tuple of (``response_code``, ``output``).
            ``response_code``:
                The exit code of the provided command. ``None`` if ``stream``.
            ``output``:
                If ``stream``, then a generator yielding response chunks.
                If ``demux``, then a tuple of (``stdout``, ``stderr``).
                Else the response content.

        Raises:
            NotImplementedError: method not implemented.
            APIError: when service reports error
        """
        # pylint: disable-msg=too-many-locals
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
            "WorkingDir": workdir,
        }
        if user:
            data["User"] = user

        stream = stream and not detach

        # create the exec instance
        response = self.client.post(f"/containers/{self.name}/exec", data=json.dumps(data))
        response.raise_for_status()
        exec_id = response.json()['Id']
        # start the exec instance, this will store command output
        start_resp = self.client.post(
            f"/exec/{exec_id}/start", data=json.dumps({"Detach": detach, "Tty": tty}), stream=stream
        )
        start_resp.raise_for_status()

        if stream:
            return None, api.stream_frames(start_resp, demux=demux)

        # get and return exec information
        response = self.client.get(f"/exec/{exec_id}/json")
        response.raise_for_status()
        if demux:
            stdout_data, stderr_data = demux_output(start_resp.content)
            return response.json().get('ExitCode'), (stdout_data, stderr_data)
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

        yield from response.iter_content(chunk_size=chunk_size)

    def get_archive(
        self, path: str, chunk_size: int = api.DEFAULT_CHUNK_SIZE
    ) -> tuple[Iterable, dict[str, Any]]:
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

    def init(self) -> None:
        """Initialize the container."""
        response = self.client.post(f"/containers/{self.id}/init")
        response.raise_for_status()

    def inspect(self) -> dict:
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
            "stderr": kwargs.get("stderr", True),
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

    def stats(
        self, **kwargs
    ) -> Union[bytes, dict[str, Any], Iterator[bytes], Iterator[dict[str, Any]]]:
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

        response = self.client.get("/containers/stats", params=params, stream=stream)
        response.raise_for_status()

        if stream:
            return api.stream_helper(response, decode_to_json=decode)

        return json.loads(response.content) if decode else response.content

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
            else:
                raise APIError(
                    response.text, response=response, explanation="Container already stopped."
                )

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def top(self, **kwargs) -> Union[Iterator[dict[str, Any]], dict[str, Any]]:
        """Report on running processes in the container.

        Keyword Args:
            ps_args (str): When given, arguments will be passed to ps
            stream (bool): When True, repeatedly return results. Default: False

        Raises:
            NotFound: when the container no longer exists
            APIError: when the service reports an error
        """
        stream = kwargs.get("stream", False)

        params = {
            "stream": stream,
            "ps_args": kwargs.get("ps_args"),
        }
        response = self.client.get(f"/containers/{self.id}/top", params=params, stream=stream)
        response.raise_for_status()

        if stream:
            return api.stream_helper(response, decode_to_json=True)

        return response.json()

    def unpause(self) -> None:
        """Unpause processes in container."""
        response = self.client.post(f"/containers/{self.id}/unpause")
        response.raise_for_status()

    def update(self, **kwargs) -> None:
        """Update resource configuration of the containers.
        Keyword Args:
            Please refer to Podman API documentation for details:
            https://docs.podman.io/en/latest/_static/api.html#tag/containers/operation/ContainerUpdateLibpod

            restart_policy (str): New restart policy for the container.
            restart_retries (int): New amount of retries for the container's restart policy.
                Only allowed if restartPolicy is set to on-failure

            blkio_weight_device tuple(str, int):Block IO weight (relative device weight)
                in the form: (device_path, weight)
            blockio (dict): LinuxBlockIO for Linux cgroup 'blkio' resource management
                Example:
                blockio = {
                        "leafWeight": 0
                        "throttleReadBpsDevice": [{
                            "major": 0,
                            "minor": 0,
                            "rate": 0
                        }],
                        "throttleReadIopsDevice": [{
                            "major": 0,
                            "minor": 0,
                            "rate": 0
                        }],
                        "throttleWriteBpsDevice": [{
                            "major": 0,
                            "minor": 0,
                            "rate": 0
                        }],
                        "throttleWriteIopsDevice": [{
                            "major": 0,
                            "minor": 0,
                            "rate": 0
                        }],
                        "weight": 0,
                        "weightDevice": [{
                            "leafWeight": 0,
                            "major": 0,
                            "minor": 0,
                            "weight": 0
                        }],
                    }
            cpu (dict): LinuxCPU for Linux cgroup 'cpu' resource management
                Example:
                cpu = {
                        "burst": 0,
                        "cpus": "string",
                        "idle": 0,
                        "mems": "string",
                        "period": 0
                        "quota": 0,
                        "realtimePeriod": 0,
                        "realtimeRuntime": 0,
                        "shares": 0
                    }
            device_read_bps (list(dict)): Limit read rate (bytes per second) from a device,
                in the form: [{"Path": "string", "Rate": 0}]
            device_read_iops (list(dict)): Limit read rate (IO operations per second) from a device,
                in the form: [{"Path": "string", "Rate": 0}]
            device_write_bps (list(dict)): Limit write rate (bytes per second) to a device,
                in the form: [{"Path": "string", "Rate": 0}]
            device_write_iops (list(dict)): Limit write rate (IO operations per second) to a device,
                in the form: [{"Path": "string", "Rate": 0}]
            devices (list(dict)): Devices configures the device allowlist.
                Example:
                devices = [{
                    access: "string"
                    allow: 0,
                    major: 0,
                    minor: 0,
                    type: "string"
                }]
            health_cmd (str): set a healthcheck command for the container ('None' disables the
                existing healthcheck)
            health_interval (str): set an interval for the healthcheck (a value of disable results
                in no automatic timer setup)(Changing this setting resets timer.) (default "30s")
            health_log_destination (str):  set the destination of the HealthCheck log. Directory
                path, local or events_logger (local use container state file)(Warning: Changing
                this setting may cause the loss of previous logs.) (default "local")
            health_max_log_count (int): set maximum number of attempts in the HealthCheck log file.
                ('0' value means an infinite number of attempts in the log file) (default 5)
            health_max_logs_size (int): set maximum length in characters of stored HealthCheck log.
                ('0' value means an infinite log length) (default 500)
            health_on_failure (str): action to take once the container turns unhealthy
                (default "none")
            health_retries (int): the number of retries allowed before a healthcheck is considered
                to be unhealthy (default 3)
            health_start_period (str): the initialization time needed for a container to bootstrap
                (default "0s")
            health_startup_cmd (str): Set a startup healthcheck command for the container
            health_startup_interval (str): Set an interval for the startup healthcheck. Changing
                this setting resets the timer, depending on the state of the container.
                (default "30s")
            health_startup_retries (int): Set the maximum number of retries before the startup
                healthcheck will restart the container
            health_startup_success (int): Set the number of consecutive successes before the
                startup healthcheck is marked as successful and the normal healthcheck begins
                (0 indicates any success will start the regular healthcheck)
            health_startup_timeout (str): Set the maximum amount of time that the startup
                healthcheck may take before it is considered failed (default "30s")
            health_timeout (str): the maximum time allowed to complete the healthcheck before an
                interval is considered failed (default "30s")
            no_healthcheck (bool): Disable healthchecks on container
            hugepage_limits (list(dict)): Hugetlb limits (in bytes).
                Default to reservation limits if supported.
                Example:
                    huugepage_limits = [{"limit": 0, "pageSize": "string"}]
            memory (dict): LinuxMemory for Linux cgroup 'memory' resource management
                Example:
                memory = {
                    "checkBeforeUpdate": True,
                    "disableOOMKiller": True,
                    "kernel": 0,
                    "kernelTCP": 0,
                    "limit": 0,
                    "reservation": 0,
                    "swap": 0,
                    "swappiness": 0,
                    "useHierarchy": True,
                }
            network (dict): LinuxNetwork identification and priority configuration
                Example:
                network = {
                    "classID": 0,
                    "priorities": {
                        "name": "string",
                        "priority": 0
                    }
                )
            pids (dict): LinuxPids for Linux cgroup 'pids' resource management (Linux 4.3)
                Example:
                    pids = {
                        "limit": 0
                    }
            rdma (dict): Rdma resource restriction configuration. Limits are a set of key value
                pairs that define RDMA resource limits, where the key is device name and value
                is resource limits.
                Example:
                rdma = {
                    "property1": {
                        "hcaHandles": 0
                        "hcaObjects": 0
                    },
                    "property2": {
                        "hcaHandles": 0
                        "hcaObjects": 0
                    },
                    ...
                }
            unified (dict): Unified resources.
                Example:
                unified = {
                    "property1": "value1",
                    "property2": "value2",
                    ...
                }

        """

        data = {}
        params = {}

        health_commands_data = [
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
        ]
        # the healthcheck section of parameters accepted can be either no_healthcheck or a series
        # of healthcheck parameters
        if kwargs.get("no_healthcheck"):
            for command in health_commands_data:
                if command in kwargs:
                    raise ValueError(f"Cannot set {command} when no_healthcheck is True")
            data["no_healthcheck"] = kwargs.get("no_healthcheck")
        else:
            for hc in health_commands_data:
                if hc in kwargs:
                    data[hc] = kwargs.get(hc)

        data_mapping = {
            "BlkIOWeightDevice": "blkio_weight_device",
            "blockio": "blockIO",
            "cpu": "cpu",
            "device_read_bps": "DeviceReadBPs",
            "device_read_iops": "DeviceReadIOps",
            "device_write_bps": "DeviceWriteBPs",
            "device_write_iops": "DeviceWriteIOps",
            "devices": "devices",
            "hugepage_limits": "hugepageLimits",
            "memory": "memory",
            "network": "network",
            "pids": "pids",
            "rdma": "rdma",
            "unified": "unified",
        }
        for kwarg_key, data_key in data_mapping.items():
            value = kwargs.get(kwarg_key)
            if value is not None:
                data[data_key] = value

        if kwargs.get("restart_policy"):
            params["restartPolicy"] = kwargs.get("restart_policy")
        if kwargs.get("restart_retries"):
            params["restartRetries"] = kwargs.get("restart_retries")

        response = self.client.post(
            f"/containers/{self.id}/update", params=params, data=json.dumps(data)
        )
        response.raise_for_status()

    def wait(self, **kwargs) -> int:
        """Block until the container enters given state.

        Keyword Args:
            condition (Union[str, list[str]]): Container state on which to release.
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
