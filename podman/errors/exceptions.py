"""Podman API Errors."""

from typing import Iterable, List, Optional, Union, TYPE_CHECKING

from requests import Response
from requests.exceptions import HTTPError

# Break circular import
if TYPE_CHECKING:
    from podman.domain.containers import Container
    from podman.api.client import APIResponse


class APIError(HTTPError):
    """Wraps HTTP errors for processing by the API and clients."""

    def __init__(
        self,
        message: str,
        response: Union[Response, "APIResponse", None] = None,
        explanation: Optional[str] = None,
    ):
        """Initialize APIError.

        Args:
            message: Message from service. Default: response.text, may be enhanced or wrapped by
                bindings
            response: HTTP Response from service.
            explanation: An enhanced or wrapped version of message with additional context.
        """
        super().__init__(message, response=response)
        self.explanation = explanation

    def __str__(self):
        msg = super().__str__()

        if self.response is not None:
            msg = self.response.reason

        if self.is_client_error():
            msg = f"{self.status_code} Client Error: {msg}"

        elif self.is_server_error():
            msg = f"{self.status_code} Server Error: {msg}"

        if self.explanation:
            msg = f"{msg} ({self.explanation})"

        return msg

    @property
    def status_code(self):
        """Optional[int]: HTTP status code from response."""
        if self.response is not None:
            return self.response.status_code
        return None

    def is_error(self) -> bool:
        """Returns True when HTTP operation resulted in an error."""
        return self.is_client_error() or self.is_server_error()

    def is_client_error(self) -> bool:
        """Returns True when request is incorrect."""
        return 400 <= (self.status_code or 0) < 500

    def is_server_error(self) -> bool:
        """Returns True when error occurred in service."""
        return 500 <= (self.status_code or 0) < 600


class NotFound(APIError):
    """Resource not found on Podman service.

    Named for compatibility.
    """


class ImageNotFound(APIError):
    """Image not found on Podman service."""


class DockerException(Exception):
    """Base class for exception hierarchy.

    Provided for compatibility.
    """


class PodmanError(DockerException):
    """Base class for PodmanPy exceptions."""


class BuildError(PodmanError):
    """Error occurred during build operation."""

    def __init__(self, reason: str, build_log: Iterable[str]) -> None:
        """Initialize BuildError.

        Args:
            reason: describes the error
            build_log: build log output
        """
        super().__init__(reason)
        self.msg = reason
        self.build_log = build_log


class ContainerError(PodmanError):
    """Represents a container that has exited with a non-zero exit code."""

    def __init__(
        self,
        container: "Container",
        exit_status: int,
        command: Union[str, List[str]],
        image: str,
        stderr: Optional[Iterable[str]] = None,
    ):  # pylint: disable=too-many-positional-arguments
        """Initialize ContainerError.

        Args:
            container: Container that reported error.
            exit_status: Non-zero status code from Container exit.
            command: Command passed to container when created.
            image: Name of image that was used to create container.
            stderr: Errors reported by Container.
        """
        err = f": {stderr}" if stderr is not None else ""
        msg = (
            f"Command '{command}' in image '{image}' returned non-zero exit "
            f"status {exit_status}{err}"
        )

        super().__init__(msg)

        self.container = container
        self.exit_status: int = exit_status
        self.command = command
        self.image = image
        self.stderr = stderr


class InvalidArgument(PodmanError):
    """Parameter to method/function was not valid."""
