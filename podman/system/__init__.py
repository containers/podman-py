"""Provide system level information for the Podman service."""
from http import HTTPStatus
import json

def ping(api, verify_version=False):
    """Obtain a dictionary of versions for the Podman components."""
    response = api.request("GET", "/_ping")
    response.read()
    if response.getcode() == HTTPStatus.OK:
        return response.headers
    # TODO: verify api.base and header[Api-Version] compatible
    return {}


def get_info(api):
    """Returns information on the system and libpod configuration"""
    path = api.join("/info")
    response = api.request("GET", path)
    return json.loads(response.read())

def show_disk_usage(api):
    """Return information about disk usage for containers, images, and volumes"""
    # this endpoint is non-functional (returns 0 values) podman 1.9.2
    # uri does not conform to the /{version}/lipod/{endpoint} format
    response = api.request("GET", "/system/df")
    return json.loads(response.read())

def get_events(api):
    """Returns events filtered on query parameters"""
    # this endpoint is non-functional and will just hang podman 1.9.2
    path = api.join("/events")
    response = api.request("GET", path)
    return json.loads(response.read())

def prune_unused_data(api):
    """Prune unused data"""
    # this endpoint is non-functional podman 1.9.2
    path = api.join("/system/prune")
    response = api.request("POST", path)
    return  json.loads(response.read())

def version(api):
    """Get system version information"""
    # uri does not conform to the /{version}/lipod/{endpoint} format
    response = api.request("GET", "/version")
    return json.loads(response.read())

__all__ = [
    "ping",
    "get_info",
    "show_disk_usage",
    "get_events",
    "prune_unused_data",
    "version",
]
