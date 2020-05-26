"""errors module is used to extend HTTPException for Podman API."""
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


class ContainerNotFound(NotFoundError):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND.
       Specialized for Container not found.
    """


class PodNotFound(NotFoundError):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND.
       Specialized for Pod not found.
    """


class InternalServerError(HTTPException):
    """Podman service reported an internal error."""

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response
