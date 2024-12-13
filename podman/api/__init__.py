"""Tools for connecting to a Podman service."""

from podman.api.cached_property import cached_property
from podman.api.client import APIClient
from podman.api.api_versions import VERSION, COMPATIBLE_VERSION
from podman.api.http_utils import prepare_body, prepare_filters
from podman.api.parse_utils import (
    decode_header,
    frames,
    parse_repository,
    prepare_cidr,
    prepare_timestamp,
    stream_frames,
    stream_helper,
)
from podman.api.tar_utils import create_tar, prepare_containerfile, prepare_containerignore

DEFAULT_CHUNK_SIZE = 2 * 1024 * 1024


# isort: unique-list
__all__ = [
    'APIClient',
    'COMPATIBLE_VERSION',
    'DEFAULT_CHUNK_SIZE',
    'VERSION',
    'cached_property',
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
    'stream_helper',
]
