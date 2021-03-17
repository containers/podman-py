"""Helper functions for parsing strings."""
import base64
import ipaddress
import json
from datetime import datetime
from typing import Any, Dict, MutableMapping, Optional, Tuple, Union


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


def prepare_body(body: MutableMapping[str, Any]) -> str:
    """Strip out any items without a value."""
    if body is None:
        return ""

    targets = {k: v for (k, v) in body.items() if v is None}
    for key in targets:
        del body[key]
    return json.dumps(body)


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

    Notes:
        The return values are dictated by the Go JSON decoder.
    """
    return str(value.network_address), base64.b64encode(value.netmask.packed).decode("utf-8")
