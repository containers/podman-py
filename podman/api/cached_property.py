"""Provide cached_property for Python < 3.8 programs."""

import functools
import sys

if sys.version_info >= (3, 8):
    from functools import cached_property  # pylint: disable=unused-import
else:

    def cached_property(fn):  # type: ignore[no-redef]
        return property(functools.lru_cache()(fn))
