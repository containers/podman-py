"""containers provides the operations against containers for a Podman service.
"""

import json
import logging

import podman.errors as errors

__all__ = []


def list_containers(api, all_=None):
    """List all images for a Podman service."""
    path = "/containers/json"
    query = {}
    if all_:
        query["all"] = True
    response = api.get(path, query)
    # observed to return None when no containers
    return json.loads(str(response.read(), "utf-8")) or []

__all__.append('list_containers')


def inspect(api, name):
    """Report on named container for a Podman service.
       Name may also be a container ID.
    """
    try:
        response = api.request(
            "GET", api.join("/containers/{}/json".format(api.quote(name)))
        )
        return json.loads(response.read())
    except errors.NotFoundError as e:
        _report_not_found(e, e.response)

__all__.append('inspect')


def kill(api, name, signal=None):
    """kill named/identified container"""
    path = "/containers/{}/kill".format(api.quote(name))
    if signal is not None:
        path = api.join(path, {"signal": signal})
    else:
        path = api.join(path)

    try:
        response = api.request("POST", path)
        response.read() # returns an empty bytes object
        # return json.loads(response.read())
        return True
    except errors.NotFoundError as e:
        _report_not_found(e, e.response)

__all__.append('kill')


def remove(api, name, force=None, delete_volumes=None):
    """Delete container"""
    path = "/containers/{}".format(api.quote(name))
    query = {}
    if force is not None:
        query['force'] = force
    if delete_volumes is not None:
        query['v'] = delete_volumes
    if query:
        path = api.join(path, query)
    else:
        path = api.join(path)

    try:
        response = api.request("DELETE", path)
        response.read() # returns an empty bytes object
        # return json.loads(response.read())
        return True
    except errors.NotFoundError as e:
        _report_not_found(e, e.response)
    # xxx need to handle error 409 Conflict error in operation ?

__all__.append('remove')


def _report_not_found(e, response):
    body = json.loads(response.read())
    logging.info(body["cause"])
    raise errors.ContainerNotFound(body["message"]) from e
