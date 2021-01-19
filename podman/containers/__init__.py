"""containers provides the operations against containers for a Podman service.
"""

import json

import podman.errors as errors


def inspect(api, name):
    """Report on named container for a Podman service.
    Name may also be a container ID.
    """
    try:
        response = api.get('/containers/{}/json'.format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def list_containers(api, all_=None):
    """List all images for a Podman service."""
    query = {}
    if all_:
        query["all"] = True
    response = api.get("/containers/json", query)
    # observed to return None when no containers
    return json.loads(str(response.read(), "utf-8")) or []


def kill(api, name, signal=None):
    """kill named/identified container"""
    path = "/containers/{}/kill".format(api.quote(name))
    params = {}
    if signal is not None:
        params = {'signal': signal}

    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        # returns an empty bytes object
        response.read()
        return True
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def remove(api, name, force=None, delete_volumes=None):
    """Delete container"""
    path = "/containers/{}".format(api.quote(name))
    params = {}
    if force is not None:
        params['force'] = force
    if delete_volumes is not None:
        params['v'] = delete_volumes

    try:
        response = api.delete(path, params)
        # returns an empty bytes object
        response.read()
        return True
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    # xxx need to handle error 409 Conflict error in operation


__all__ = [
    "inspect",
    "kill",
    "list_containers",
    "remove",
]
