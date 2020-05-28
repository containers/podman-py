"""Provide system level information for the Podman service."""
from http import HTTPStatus
import json


def make_call(api, endpoint, method='GET', params=None):
    """A helper function to keep things DRY"""
    path = api.join(endpoint)
    response = api.request(method, path)
    return response.read()


def ping(api, verify_version=False):
    """Obtain a dictionary of versions for the Podman components."""
    # this is hitting the compatability endpoint
    response = api.request("GET", "/_ping")
    response.read()
    if response.getcode() == HTTPStatus.OK:
        return response.headers
    # TODO: verify api.base and header[Api-Version] compatible
    return {}


def get_info(api):
    """Returns information on the system and libpod configuration"""
    return json.loads(make_call(api, "/info"))


def show_disk_usage(api):
    """Return information about disk usage for containers, images, and volumes"""
    # this endpoint is non-functional podman 1.9.2
    return json.loads(make_call(api, "/system/df"))


def get_events(api):
    """Returns events filtered on query parameters"""
    # this endpoint is non-functional and will just hang podman 1.9.2
    return json.loads(make_call(api, "/events"))


def prune_unused_data(api):
    """Prune unused data"""
    # this endpoint is non-functional podman 1.9.2
    return json.loads(make_call(api, "/system/prune", "POST"))


def version(api):
    """Get system version information"""
    # uri does not conform to the /{version}/lipod/{endpoint} format
    return json.loads(make_call(api, "/version"))


__all__ = [
    "ping",
    "get_info",
    "show_disk_usage",
    "get_events",
    "prune_unused_data",
    "version",
]
