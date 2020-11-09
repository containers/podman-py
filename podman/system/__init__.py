"""Provide system level information for the Podman service."""
import json
import logging
from http import HTTPStatus

import podman.errors as errors


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
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response)


def show_disk_usage(api):
    """
    Return information about disk usage for containers,
    images and volumes
    """
    try:
        response = api.get("/system/df")
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response)


def _report_not_found(e, response):
    body = json.loads(response.read())
    logging.info(body["cause"])
    raise errors.ImageNotFound(body["message"]) from e


__all__ = [
    "version",
    "get_info",
    "show_disk_usage",
]
