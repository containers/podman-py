"""Provide cached_property for Python <=3.8 programs."""
import functools

try:
    from functools import cached_property  # pylint: disable=unused-import
except ImportError:

    def cached_property(fn):
        return property(functools.lru_cache()(fn))
