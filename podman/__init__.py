"""Podman client module."""
try:
    from podman.api_connection import ApiConnection
except ImportError:

    class ApiConnection:  # pylint: disable=too-few-public-methods
        def __init__(self):
            raise NotImplementedError("ApiConnection deprecated, please use PodmanClient().")


from podman.api.version import __version__
from podman.client import PodmanClient, from_env

# isort: unique-list
__all__ = ['ApiConnection', 'PodmanClient', '__version__', 'from_env']
