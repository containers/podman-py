"""Utility functions for working with URL's."""
import json
from typing import Dict, List, Mapping, Optional, Union


def format_filters(filters: Union[str, List[str], Mapping[str, str]]) -> Optional[str]:
    """Returns filters as an URL quoted JSON Dict[str, List[str]]."""

    if filters is None or len(filters) == 0:
        return None

    criteria: Dict[str, List[str]] = {}
    if isinstance(filters, str):
        _format_string(filters, criteria)
    elif isinstance(filters, dict):
        _format_dict(filters, criteria)
    else:
        _format_list(filters, criteria)

    if len(criteria) == 0:
        return None

    return json.dumps(criteria)


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

        if key in criteria:
            criteria[key].append(value)
        else:
            criteria[key] = [value]


def _format_string(filters, criteria):
    key, value = filters.split("=", 1)
    criteria[key] = [value]
