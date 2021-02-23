"""Podman API Errors."""
from typing import Iterable, Optional

from requests import Response
from requests.exceptions import HTTPError


class APIError(HTTPError):
    """A wrapper for HTTP errors from the API."""

    def __init__(
        self, message: str, response: Optional[Response] = None, explanation: Optional[str] = None
    ):
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
    def status_code(self) -> Optional[int]:
        """HTTP status code from response."""
        if self.response is not None:
            return self.response.status_code
        return None

    def is_error(self) -> bool:
        """Returns True if an HTTP occurred."""
        return self.is_client_error() or self.is_server_error()

    def is_client_error(self) -> bool:
        """Returns True if error occurred in request."""
        return 400 <= (self.status_code or 0) < 500

    def is_server_error(self) -> bool:
        """Returns True if error occurred in service."""
        return 500 <= (self.status_code or 0) < 600


class NotFound(APIError):
    """Resource not found on Podman service.

    Notes:
        Compatible name, missing Error suffix.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ImageNotFound(APIError):
    """Image not found on Podman service.

    Notes:
        Compatible name, missing Error suffix.
    """


class DockerException(Exception):
    """Base class for exception hierarchy.

    Notes:
        * Provided for compatibility.
    """


class PodmanError(DockerException):
    """Base class for PodmanPy exceptions."""


class BuildError(PodmanError):
    """Error occurred during build operation."""

    def __init__(self, reason: str, build_log: Iterable[str]) -> None:
        """Create BuildError.

        Args:
            reason: describes the error
            build_log: build log output
        """
        super().__init__(reason)
        self.msg = reason
        self.build_log = build_log


class InvalidArgument(PodmanError):
    """Parameter to method/function was not valid."""
