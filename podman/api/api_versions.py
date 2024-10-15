"""Constants API versions"""

import re
from .. import version


def _api_version(release: str, significant: int = 3) -> str:
    """Return API version removing any additional identifiers from the release version.

    This is a simple lexicographical parsing, no semantics are applied, e.g. semver checking.
    """
    items = re.split(r"\.|-|\+", release)
    parts = items[0:significant]
    return ".".join(parts)


VERSION: str = _api_version(version.__version__)
COMPATIBLE_VERSION: str = _api_version(version.__compatible_version__, 2)
