"""Podman client module."""
import sys

assert sys.version_info >= (3, 6), "Python 3.6 or greater is required."

from podman.client import PodmanClient, from_env
from podman.version import __version__

# isort: unique-list
__all__ = ['PodmanClient', '__version__', 'from_env']
