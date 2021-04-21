"""Tools for connecting to a Podman service."""
import re

from podman.api.client import APIClient
from podman.api.http_utils import prepare_body, prepare_filters
from podman.api.parse_utils import (
    decode_header,
    frames,
    parse_repository,
    prepare_cidr,
    prepare_timestamp,
    stream_frames,
)
from podman.api.tar_utils import create_tar, prepare_containerfile, prepare_containerignore

from . import version

DEFAULT_TIMEOUT: float = 60.0
DEFAULT_CHUNK_SIZE = 2 * 1024 * 1024


def _api_version(release: str, significant: int = 3) -> str:
    """Return API version removing any additional identifiers from the release version.

    Notes:
        This is a simple lexicographical parsing, no semantics are applied, e.g. semver checking.
    """
    items = re.split(r"\.|-|\+", release)
    parts = items[0:significant]
    return ".".join(parts)


VERSION: str = _api_version(version.__version__)
COMPATIBLE_VERSION: str = _api_version(version.__compatible_version__, 2)

# isort: unique-list
__all__ = [
    'APIClient',
    'VERSION',
    'COMPATIBLE_VERSION',
    'DEFAULT_CHUNK_SIZE',
    'DEFAULT_TIMEOUT',
    'create_tar',
    'decode_header',
    'frames',
    'parse_repository',
    'prepare_body',
    'prepare_cidr',
    'prepare_containerfile',
    'prepare_containerignore',
    'prepare_filters',
    'prepare_timestamp',
    'stream_frames',
]
