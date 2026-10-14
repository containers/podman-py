"""Helper functions for parsing strings."""

import base64
import ipaddress
import json
import re
import struct
from datetime import datetime, timezone
from typing import Any, Optional, Union
from collections.abc import Iterator

from podman.api.client import APIResponse
from .output_utils import demux_output

DURATION_UNITS_NS = {
    "ns": 1,
    "us": 1_000,
    "µs": 1_000,
    "ms": 1_000_000,
    "s": 1_000_000_000,
    "m": 60_000_000_000,
    "h": 3_600_000_000_000,
}

HEALTH_ON_FAILURE_ACTION = {
    "none": 0,
    # value 1 is "invalid" in the Go enum (HealthCheckOnFailureActionInvalid)
    # and should not be used directly
    "kill": 2,
    "restart": 3,
    "stop": 4,
}


def prepare_duration_ns(value: Union[int, str, None]) -> Union[int, None]:
    """Returns nanoseconds from given input.

    Accepts:
        - None: returns None
        - int: returned as-is (assumed nanoseconds)
        - str: parsed as Go duration (e.g. "30s", "1m", "500ms", "1h30m", "0")

    Raises:
        TypeError: if value is not int, str, or None
        ValueError: if the string cannot be parsed as a Go duration
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        raise TypeError(f"Duration must be int or str, got {type(value).__name__}")

    total_ns = 0
    remaining = value.strip()
    if not remaining:
        raise ValueError("Empty duration string")

    if remaining == "0":
        return 0

    pattern = re.compile(r"(\d+)(ns|µs|us|ms|s|m|h)")
    pos = 0
    while pos < len(remaining):
        match = pattern.match(remaining, pos)
        if not match:
            raise ValueError(
                f"Invalid duration format: {value!r}. "
                f"Use Go-style durations like '30s', '1m', '500ms', '1h30m'."
            )
        num_str, unit = match.groups()
        total_ns += int(num_str) * DURATION_UNITS_NS[unit]
        pos = match.end()

    return total_ns


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
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        delta = value - datetime.fromtimestamp(0, timezone.utc)
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
