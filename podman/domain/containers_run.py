"""Mixin to provide Container run() method."""

import logging
from contextlib import suppress
from typing import Generator, Iterator, List, Union

from podman.domain.containers import Container
from podman.domain.images import Image
from podman.errors import ContainerError, ImageNotFound

logger = logging.getLogger("podman.containers")


class RunMixin:  # pylint: disable=too-few-public-methods
    """Class providing run() method for ContainersManager."""

    def run(
        self,
        image: Union[str, Image],
        command: Union[str, List[str], None] = None,
        stdout=True,
        stderr=False,
        remove: bool = False,
        **kwargs,
    ) -> Union[Container, Union[Generator[str, None, None], Iterator[str]]]:
        """Run a container.

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
            - See the create() method for keyword arguments.

        Returns:
            - When detach is True, return a Container
            - If stdout is True, include stdout from container in output
            - If stderr is True, include stderr from container in output
            - When stream is True, output from container is returned as a generator
            - Otherwise, an iterator is returned after container has finished

        Raises:
            ContainerError: when Container exists with a non-zero code
            ImageNotFound: when Image not found by Podman service
            APIError: when Podman service reports an error
        """
        if isinstance(image, Image):
            image = image.id
        if isinstance(command, str):
            command = [command]

        try:
            container = self.create(image=image, command=command, **kwargs)
        except ImageNotFound:
            self.client.images.pull(image, platform=kwargs.get("platform"))
            container = self.create(image=image, command=command, **kwargs)

        container.start()
        container.wait(condition=["running", "exited"])
        container.reload()

        if kwargs.get("detach", False):
            return container

        with suppress(KeyError):
            log_type = container.attrs["HostConfig"]["LogConfig"]["Type"]

        log_iter = None
        if log_type in ("json-file", "journald"):
            log_iter = container.logs(stdout=stdout, stderr=stderr, stream=True, follow=True)

        exit_status = container.wait()
        if exit_status != 0:
            log_iter = None
            if not kwargs.get("auto_remove", False):
                log_iter = container.logs(stdout=False, stderr=True)

        if remove:
            container.remove()

        if exit_status != 0:
            raise ContainerError(container, exit_status, command, image, log_iter)

        return log_iter if kwargs.get("stream", False) or log_iter is None else b"".join(log_iter)
