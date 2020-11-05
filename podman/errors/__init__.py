"""errors module is used ti extend HTTPException for Podman API."""
from http.client import HTTPException


class NotFoundError(HTTPException):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND."""

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class ImageNotFound(NotFoundError):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND.
       Specialized for Image not found.
    """


class NetworkNotFound(NotFoundError):
    """Network request returned a http.HTTPStatus.NOT_FOUND."""


class ContainerNotFound(NotFoundError):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND.
       Specialized for Container not found.
    """


class PodNotFound(NotFoundError):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND.
       Specialized for Pod not found.
    """


class RequestError(HTTPException):
    """Podman service reported issue with the request"""

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class InternalServerError(HTTPException):
    """Podman service reported an internal error."""

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response
