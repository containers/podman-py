"""Utility functions for working with URLs."""

import base64
import collections.abc
import json
import urllib.parse
from typing import Any
from collections.abc import Mapping


def prepare_filters(
    filters: str | list[str] | Mapping[str, Any] | None,
) -> str | None:
    """Return filters as an URL quoted JSON dict[str, list[Any]]."""

    if filters is None or len(filters) == 0:
        return None

    criteria: dict[str, list[str]] = {}
    if isinstance(filters, str):
        _format_string(filters, criteria)
    elif isinstance(filters, collections.abc.Mapping):
        _format_dict(filters, criteria)
    else:
        _format_list(filters, criteria)

    if len(criteria) == 0:
        return None

    return json.dumps(criteria, sort_keys=True)


def _format_list(filters, criteria):
    for item in filters:
        if item is None:
            continue

        key, value = item.split("=", 1)
        if key in criteria:
            criteria[key].append(value)
        else:
            criteria[key] = [value]


def _format_dict(filters, criteria):
    for key, value in filters.items():
        if value is None:
            continue
        values = value if isinstance(value, (list, tuple)) else [value]
        for item in values:
            if item is not None:
                criteria.setdefault(key, []).append(str(item))


def _format_string(filters, criteria):
    key, value = filters.split("=", 1)
    criteria[key] = [value]


def prepare_body(body: Mapping[str, Any]) -> str:
    """Returns JSON payload to be uploaded to server.

    Values of None and empty Iterables are removed, False and zero-values are retained.
    """
    if body is None:
        return ""

    body = _filter_values(body)
    return json.dumps(body, sort_keys=True)


def _filter_values(mapping: Mapping[str, Any], recursion=False) -> dict[str, Any]:
    """Returns a canonical dictionary with values == None or empty Iterables removed.

    Dictionary is walked using recursion.
    """
    canonical = {}

    for key, value in mapping.items():
        # quick filter if possible...
        if (
            value is None
            or (isinstance(value, collections.abc.Sized) and len(value) <= 0)
            and not recursion
        ):
            continue

        # networks can actually be a dictionary with an empty value like this:
        # networks={network.name: {}}
        if key == "networks":
            canonical[key] = value
            continue

        # depending on type we need details...
        proposal: Any
        if isinstance(value, collections.abc.Mapping):
            proposal = _filter_values(value, recursion=True)
        elif isinstance(value, collections.abc.Iterable) and not isinstance(value, str):
            proposal = [i for i in value if i is not None]
        else:
            proposal = value

        if not recursion and proposal not in (None, "", [], {}):
            canonical[key] = proposal
        elif recursion and proposal not in (None, [], {}):
            canonical[key] = proposal

    return canonical


def normalize_registry(registry: str) -> str:
    """Normalize a registry identifier to a canonical form.

    This function normalizes various equivalent registry forms to a consistent
    format for credential storage and lookup. For example:
    - https://quay.io/v2 -> quay.io
    - quay.io -> quay.io
    - https://quay.io -> quay.io
    - https://localhost:5000/v2 -> localhost:5000
    - docker.io -> docker.io

    The normalization:
    - Removes URL scheme (http:// or https://)
    - Removes trailing slashes
    - Removes /v2 suffix if present
    - Preserves hostname and port distinctions
    - Does not change case for hostnames (DNS is case-insensitive but we preserve input)

    Args:
        registry: Registry identifier in any of the common forms

    Returns:
        Canonical registry identifier (hostname[:port] without scheme or /v2)

    Raises:
        ValueError: If registry is empty or cannot be parsed
    """
    if not registry:
        raise ValueError("Registry cannot be empty")

    # Add a temporary scheme if not present to make urlparse work correctly
    if "://" not in registry:
        registry = f"https://{registry}"

    # Parse as URL to handle scheme and path
    parsed = urllib.parse.urlparse(registry)

    # Extract hostname (netloc)
    hostname = parsed.netloc

    # Remove /v2 suffix from path if present
    path = parsed.path.rstrip('/')
    if path.endswith('/v2'):
        path = path[:-3]
        path = path.rstrip('/')

    # For most cases, hostname is sufficient (e.g., quay.io, localhost:5000)
    # If path remains after removing /v2, it's unusual but we preserve it
    if path:
        # Edge case: registry with additional path components
        # Preserve them to avoid misidentification
        result = f"{hostname}{path}"
    else:
        result = hostname

    return result


def _base64url_encode_json(data: Any) -> bytes:
    """Helper to encode JSON data as base64url-encoded bytes.

    Args:
        data: Data to encode (will be JSON serialized)

    Returns:
        Base64url-encoded bytes
    """
    return base64.urlsafe_b64encode(json.dumps(data).encode('utf-8'))


def encode_auth_header(auth_config: dict[str, str]) -> bytes:
    """Encode a single auth configuration for X-Registry-Auth header.

    The X-Registry-Auth header is used for pull/push operations and contains
    a single auth configuration (flat dict with username, password, etc.).

    Args:
        auth_config: Dictionary containing authentication credentials
                      (username, password, serveraddress, etc.)

    Returns:
        Base64url-encoded JSON bytes suitable for X-Registry-Auth header
    """
    return _base64url_encode_json(auth_config)


def encode_registry_config(auth_configs: dict[str, dict[str, str]]) -> bytes:
    """Encode registry authentication configurations for X-Registry-Config header.

    The X-Registry-Config header is used for build operations and contains
    a mapping of registry URLs to their auth configurations (nested dict).
    This format differs from X-Registry-Auth which contains a single auth config.

    Args:
        auth_configs: Dictionary mapping registry URLs to auth config dicts
                      (each containing username, password, etc.)

    Returns:
        Base64url-encoded JSON bytes suitable for X-Registry-Config header
    """
    return _base64url_encode_json(auth_configs)
