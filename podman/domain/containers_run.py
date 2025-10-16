"""Mixin to provide Container run() method."""

import logging
import threading
from contextlib import suppress
from typing import Union
from collections.abc import Generator, Iterator

from podman.domain.containers import Container
from podman.domain.images import Image
from podman.errors import ContainerError, ImageNotFound

logger = logging.getLogger("podman.containers")


class RunMixin:  # pylint: disable=too-few-public-methods
    """Class providing run() method for ContainersManager."""

    def run(
        self,
        image: Union[str, Image],
        command: Union[str, list[str], None] = None,
        *,
        stdout=True,
        stderr=False,
        remove: bool = False,
        **kwargs,
    ) -> Union[Container, Union[Generator[bytes, None, None], Iterator[str]]]:
        """Run a container.

        By default, run() will wait for the container to finish and return its logs.

        If detach=True, run() will start the container and return a Container object rather
            than logs. In this case, if remove=True, run() will monitor and remove the
            container after it finishes running; the logs will be lost in this case.

        Args:
            image: Image to run.
            command: Command to run in the container.
            stdout: Include stdout. Default: True.
            stderr: Include stderr. Default: False.
            remove: Delete container on the client side when the container's processes exit.
                The `auto_remove` flag is also available to manage the removal on the daemon
                side. Default: False.

        Keyword Args:
            - These args are directly used to pull an image when the image is not found.
                auth_config (Mapping[str, str]): Override the credentials that are found in the
                config for this request. auth_config should contain the username and password
                keys to be valid.
                platform (str): Platform in the format os[/arch[/variant]]
                policy (str): Pull policy. "missing" (default), "always", "never", "newer"

            - See the create() method for other keyword arguments.

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
            image_id = image.id
        else:
            image_id = image
        if isinstance(command, str):
            command = [command]

        try:
            container = self.create(image=image_id, command=command, **kwargs)  # type: ignore[attr-defined]
        except ImageNotFound:
            self.podman_client.images.pull(  # type: ignore[attr-defined]
                image_id,
                auth_config=kwargs.get("auth_config"),
                platform=kwargs.get("platform"),
                policy=kwargs.get("policy", "missing"),
            )
            container = self.create(image=image_id, command=command, **kwargs)  # type: ignore[attr-defined]

        container.start()
        container.reload()

        def remove_container(container_object: Container) -> None:
            """
            Wait the container to finish and remove it.
            Args:
                container_object: Container object
            """
            container_object.wait()  # Wait for the container to finish
            container_object.remove()  # Remove the container

        if kwargs.get("detach", False):
            if remove:
                # Start a background thread to remove the container after finishing
                threading.Thread(target=remove_container, args=(container,)).start()
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
            raise ContainerError(container, exit_status, command, image_id, log_iter)

        return log_iter if kwargs.get("stream", False) or log_iter is None else b"".join(log_iter)  # type: ignore[return-value]
