"""Podman client module."""
import sys

assert sys.version_info >= (3, 6), "Python 3.6 or greater is required."

try:
    from podman.api_connection import ApiConnection
except ImportError:

    class ApiConnection:  # pylint: disable=too-few-public-methods
        def __init__(self):
            raise NotImplementedError("ApiConnection deprecated, please use PodmanClient().")


from podman.client import PodmanClient, from_env
from podman.version import __version__

# isort: unique-list
__all__ = ['ApiConnection', 'PodmanClient', '__version__', 'from_env']
