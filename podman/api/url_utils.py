"""Utility functions for working with URL's."""
import json
from typing import Dict, List, Mapping, Optional, Union


def format_filters(filters: Union[str, List[str], Mapping[str, str]]) -> Optional[str]:
    """Returns filters as an URL quoted JSON Dict[str, List[str]]."""
    if filters is None or len(filters) == 0:
        return None

    criteria: Dict[str, List[str]] = {}
    if isinstance(filters, str):
        key, value = filters.split("=", 1)
        criteria[key] = [value]
    elif isinstance(filters, dict):
        for key, value in filters.items():
            if key in criteria:
                criteria[key].append(value)
            else:
                criteria[key] = [value]
    else:
        # Assume we have an Iterator of str's
        for element in filters:
            key, value = element.split("=", 1)
            if key in criteria:
                criteria[key].append(value)
            else:
                criteria[key] = [value]

    if len(criteria) == 0:
        return None

    return json.dumps(criteria)
