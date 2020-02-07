"""Provide system level information for the Podman service."""
from http import HTTPStatus


def version(api, verify_version=False):
    """Obtain a dictionary of versions for the Podman components."""
    response = api.request("GET", "/_ping")
    response.read()
    if response.getcode() == HTTPStatus.OK:
        return response.headers
    # TODO: verify api.base and header[Api-Version] compatible
    return {}


__all__ = ["version"]
