"""Provide system level information for the Podman service."""
import json
import logging
from http import HTTPStatus

from podman import errors


def version(api, verify_version=False):
    """Obtain a dictionary of versions for the Podman components."""
    versions = {}
    response = api.get("/version")
    if response.status == HTTPStatus.OK:
        versions = json.loads(str(response.read(), 'utf-8'))
    # pylint: disable=fixme
    # TODO: verify api.base and header[Api-Version] compatible
    if verify_version:
        pass
    return versions


def get_info(api):
    """Returns information on the system and libpod configuration"""
    try:
        response = api.get("/info")
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response)
    return json.loads(str(response.read(), 'utf-8'))


# this **looks** a lot like the above but is not equivalent - at all !
# the difference lies with calling api.join()
# and the output have nothing to do with one another
# xxx the naming is going to be confusing
def info(api):
    """Returns information on the system and libpod configuration"""
    response = api.get("/info")
    return json.loads(response.read())


def show_disk_usage(api):
    """
    Return information about disk usage for containers,
    images and volumes
    """
    try:
        response = api.get("/system/df")
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response)
    return json.loads(str(response.read(), 'utf-8'))


def _report_not_found(e, response):
    body = json.loads(response.read())
    logging.info(body["cause"])
    raise errors.ImageNotFound(body["message"]) from e


__all__ = [
    "version",
    "get_info",
    "info",
    "show_disk_usage",
]
