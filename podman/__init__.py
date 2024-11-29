"""Podman client module."""

import sys

from podman.client import PodmanClient, from_env
from podman.version import __version__

if sys.version_info < (3, 9):
    raise ImportError("Python 3.6 or greater is required.")

# isort: unique-list
__all__ = ['PodmanClient', '__version__', 'from_env']
