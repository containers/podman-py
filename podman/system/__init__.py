"""Provide system level information for the Podman service."""
from http import HTTPStatus
import json
import logging

import podman.errors as errors

def version(api, verify_version=False):
    """Obtain a dictionary of versions for the Podman components."""
    response = api.request("GET", "/_ping")
    response.read()
    if response.getcode() == HTTPStatus.OK:
        return response.headers
    # TODO: verify api.base and header[Api-Version] compatible
    return {}

def get_info(api):
    """Returns information on the system and libpod configuration"""
    try:
        response = api.request("GET", "/info")
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        _report_not_found(e, e.response)

def _report_not_found(e, response):
    body = json.loads(response.read())
    logging.info(body["cause"])
    raise errors.ImageNotFound(body["message"]) from e

__all__ = ["version"]
