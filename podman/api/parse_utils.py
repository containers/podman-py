"""Helper functions for parsing strings."""

import base64
import ipaddress
import json
import struct
from datetime import datetime
from typing import Any, Optional, Union
from collections.abc import Iterator

from podman.api.client import APIResponse
from .output_utils import demux_output


def parse_repository(name: str) -> tuple[str, Optional[str]]:
    """Parse repository image name from tag.

    Returns:
        item 1: repository name
        item 2: Either tag or None
    """
    # split repository and image name from tag
    # tags need to be split from the right since
    # a port number might increase the split list len by 1
    elements = name.rsplit(":", 1)
    if len(elements) == 2 and "/" not in elements[1]:
        return elements[0], elements[1]

    return name, None


def decode_header(value: Optional[str]) -> dict[str, Any]:
    """Decode a base64 JSON header value."""
    if value is None:
        return {}

    value = base64.b64decode(value)
    text = value.decode("utf-8")
    return json.loads(text)


def prepare_timestamp(value: Union[datetime, int, None]) -> Optional[int]:
    """Returns a UTC UNIX timestamp from given input."""
    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, datetime):
        delta = value - datetime.utcfromtimestamp(0)
        return delta.seconds + delta.days * 24 * 3600

    raise ValueError(f"Type '{type(value)}' is not supported by prepare_timestamp()")


def prepare_cidr(value: Union[ipaddress.IPv4Network, ipaddress.IPv6Network]) -> tuple[str, str]:
    """Returns network address and Base64 encoded netmask from CIDR.

    The return values are dictated by the Go JSON decoder.
    """
    return str(value.network_address), base64.b64encode(value.netmask.packed).decode("utf-8")


def frames(response: APIResponse) -> Iterator[bytes]:
    """Returns each frame from multiplexed payload, all results are expected in the payload.

    The stdout and stderr frames are undifferentiated as they are returned.
    """
    length = len(response.content)
    index = 0
    while length - index > 8:
        header = response.content[index : index + 8]
        _, frame_length = struct.unpack_from(">BxxxL", header)
        frame_begin = index + 8
        frame_end = frame_begin + frame_length
        index = frame_end
        yield response.content[frame_begin:frame_end]


def stream_frames(
    response: APIResponse, demux: bool = False
) -> Iterator[Union[bytes, tuple[bytes, bytes]]]:
    """Returns each frame from multiplexed streamed payload.

    If ``demux`` then output will be tuples where the first position is ``STDOUT`` and the second
    is ``STDERR``.
    """
    while True:
        header = response.raw.read(8)
        if not header:
            return

        _, frame_length = struct.unpack_from(">BxxxL", header)
        if not frame_length:
            continue

        data = response.raw.read(frame_length)

        if demux:
            data = demux_output(header + data)

        if not data:
            return
        yield data


def stream_helper(
    response: APIResponse, decode_to_json: bool = False
) -> Union[Iterator[bytes], Iterator[dict[str, Any]]]:
    """Helper to stream results and optionally decode to json"""
    for value in response.iter_lines():
        if decode_to_json:
            yield json.loads(value)
        else:
            yield value
