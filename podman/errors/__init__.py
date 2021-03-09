"""errors for Podman API.

Notes:
    See exceptions.py for APIClient errors.
"""
from http.client import HTTPException

from .exceptions import APIError, ImageNotFound, NotFound

# isort: unique-list
__all__ = ['APIError', 'ImageNotFound', 'NotFound']


class NotFoundError(HTTPException):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND."""

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


# TODO this collision needs resolved.
class ImageNotFound(NotFoundError):  # pylint: disable=function-redefined
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


class ManifestNotFound(NotFoundError):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND.
    Specialized for Manifest not found.
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
