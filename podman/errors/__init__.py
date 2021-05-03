"""errors for Podman API.

    Notes:
        'importlib' exceptions are used to differentiate between APIConnection and PodmanClient
        Errors. Therefore, installing both APIConnection and PodmanClient is not supported.
        PodmanClient related errors take precedence over APIConnection ones.
"""
import warnings
from http.client import HTTPException

# isort: unique-list
__all__ = [
    'APIError',
    'BuildError',
    'ContainerError',
    'DockerException',
    'ImageNotFound',
    'InvalidArgument',
    'NotFound',
    'NotFoundError',
    'PodmanError',
]

try:
    from .exceptions import (
        APIError,
        BuildError,
        ContainerError,
        DockerException,
        InvalidArgument,
        NotFound,
        PodmanError,
    )
except ImportError:
    pass


class NotFoundError(HTTPException):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND.

    Notes:
        TODO Delete when APIConnection EOL.
    """

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response
        warnings.warn("APIConnection() and supporting classes.", PendingDeprecationWarning)


# If found, use new ImageNotFound otherwise old class
try:
    from .exceptions import ImageNotFound
except ImportError:

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


class ManifestNotFound(NotFoundError):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND.
    Specialized for Manifest not found.
    """


class RequestError(HTTPException):
    """Podman service reported issue with the request"""

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response
        warnings.warn("APIConnection() and supporting classes.", PendingDeprecationWarning)


class InternalServerError(HTTPException):
    """Podman service reported an internal error."""

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response
        warnings.warn("APIConnection() and supporting classes.", PendingDeprecationWarning)
