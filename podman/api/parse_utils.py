"""Helper functions for parsing strings."""
from typing import Optional, Tuple


def parse_repository(name: str) -> Tuple[str, Optional[str]]:
    """Parse repository image name from tag or digest

    Returns:
        element 1: repository name
        element 2: Either digest and tag, tag, or None
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
