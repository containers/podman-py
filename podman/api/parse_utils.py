"""Helper functions for parsing strings."""
import base64
import ipaddress
import json
import struct
from datetime import datetime
from typing import Any, Dict, Iterator, Optional, Tuple, Union

from requests import Response


def parse_repository(name: str) -> Tuple[str, Optional[str]]:
    """Parse repository image name from tag or digest

    Returns:
        item 1: repository name
        item 2: Either digest and tag, tag, or None
    """
    # split image name and digest
    elements = name.split("@", 1)
    if len(elements) == 2:
        return elements[0], elements[1]

    # split repository and image name from tag
    elements = name.split(":", 1)
    if len(elements) == 2 and "/" not in elements[1]:
        return elements[0], elements[1]

    return name, None


def decode_header(value: Optional[str]) -> Dict[str, Any]:
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


def prepare_cidr(value: Union[ipaddress.IPv4Network, ipaddress.IPv6Network]) -> (str, str):
    """Returns network address and Base64 encoded netmask from CIDR.

    The return values are dictated by the Go JSON decoder.
    """
    return str(value.network_address), base64.b64encode(value.netmask.packed).decode("utf-8")


def frames(response: Response) -> Iterator[bytes]:
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


def stream_frames(response: Response) -> Iterator[bytes]:
    """Returns each frame from multiplexed streamed payload.

    Notes:
        The stdout and stderr frames are undifferentiated as they are returned.
    """
    while True:
        header = response.raw.read(8)
        if not header:
            return

        _, frame_length = struct.unpack_from(">BxxxL", header)
        if not frame_length:
            continue

        data = response.raw.read(frame_length)
        if not data:
            return
        yield data
