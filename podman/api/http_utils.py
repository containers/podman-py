"""Utility functions for working with URLs."""
import base64
import collections.abc
import json
from typing import Dict, List, Mapping, Optional, Union, Any


def prepare_filters(filters: Union[str, List[str], Mapping[str, str]]) -> Optional[str]:
    """Return filters as an URL quoted JSON Dict[str, List[Any]]."""

    if filters is None or len(filters) == 0:
        return None

    criteria: Dict[str, List[str]] = {}
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
        value = str(value)

        if key in criteria:
            criteria[key].append(value)
        else:
            criteria[key] = [value]


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


def _filter_values(mapping: Mapping[str, Any], recursion=False) -> Dict[str, Any]:
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

        # depending on type we need details...
        if isinstance(value, collections.abc.Mapping):
            proposal = _filter_values(value, recursion=True)
        elif isinstance(value, collections.abc.Iterable) and not isinstance(value, str):
            proposal = [i for i in value if i is not None]
        else:
            proposal = value

        if not recursion and proposal not in (None, str(), [], {}):
            canonical[key] = proposal
        elif recursion and proposal not in (None, [], {}):
            canonical[key] = proposal

    return canonical


def encode_auth_header(auth_config: Dict[str, str]) -> str:
    return base64.b64encode(json.dumps(auth_config).encode('utf-8'))
