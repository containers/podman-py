"""images provides the operations against images for a Podman service."""
import json
import logging

import podman.errors as errors


def list_images(api):
    """List all images for a Podman service."""
    response = api.request("GET", api.join("/images/json"))
    return json.loads(response.read())


def inspect(api, name):
    """Report on named image for a Podman service.
       Name may also be a image ID.
    """
    try:
        response = api.request(
            "GET", api.join("/images/{}/json".format(api.quote(name)))
        )
        return json.loads(response.read())
    except errors.NotFoundError as e:
        _report_not_found(e, e.response)


def remove(api, name, force=None):
    """Remove named/identified image from Podman storage."""
    path = ""
    if force is not None:
        path = api.join("/images/", api.quote(name), {"force": force})
    else:
        path = api.join("/images/", api.quote(name))

    try:
        response = api.request("DELETE", path)
        return json.loads(response.read())
    except errors.NotFoundError as e:
        _report_not_found(e, e.response)


def _report_not_found(e, response):
    body = json.loads(response.read())
    logging.info(body["cause"])
    raise errors.ImageNotFound(body["message"]) from e


__ALL__ = [
    "list_images",
    "inspect",
    "remove",
]
