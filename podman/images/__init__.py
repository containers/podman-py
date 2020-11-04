"""images provides the operations against images for a Podman service."""
import json

import podman.errors as errors


def list_images(api):
    """List all images for a Podman service."""
    response = api.get("/images/json")
    return json.loads(str(response.read(), 'utf-8'))


def inspect(api, name):
    """Report on named image for a Podman service.
       Name may also be a image ID.
    """
    try:
        response = api.get("/images/{}/json".format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response)


def image_exists(api, name):
    """Checks if an image exists in the local store"""
    try:
        api.get("/images/{}/exists".format(api.quote(name)))
        return True
    except errors.NotFoundError:
        return False


def remove(api, name, force=None):
    """Remove named/identified image from Podman storage."""
    params = {}
    path = '/images/{}'.format(api.quote(name))
    if force is not None:
        params = {'force': force}
    try:
        response = api.delete(path, params)
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_image_not_found(e, e.response)


__ALL__ = [
    "list_images",
    "inspect",
    "image_exists",
    "remove",
]
