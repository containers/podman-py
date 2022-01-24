"""images provides the operations against images for a Podman service."""
import json
from http import HTTPStatus

from podman import errors


def list_images(api):
    """List all images for a Podman service."""
    response = api.get("/images/json")
    return json.loads(str(response.read(), "utf-8"))


def inspect(api, name):
    """Report on named image for a Podman service.
    Name may also be an image ID.
    """
    try:
        response = api.get(f"/images/{api.quote(name)}/json")
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response)
    return json.loads(str(response.read(), "utf-8"))


def image_exists(api, name):
    """Checks if an image exists in the local store"""
    try:
        api.get(f"/images/{api.quote(name)}/exists")
    except errors.NotFoundError:
        return False
    return True


def remove(api, name, force=None):
    """Remove named/identified image from Podman storage."""
    params = {}
    path = f"/images/{api.quote(name)}"
    if force is not None:
        params = {"force": force}
    try:
        response = api.delete(path, params)
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response)
    return json.loads(str(response.read(), "utf-8"))


def tag_image(api, name, repo, tag):
    """create an image tag using repo and tag

    :param repo: string for the image repo
    :param tag: string for the image tag
    :return boolean
    """
    data = {"repo": repo, "tag": tag}
    try:
        response = api.post(f"/images/{api.quote(name)}/tag", data)
    except errors.NotFoundError as e:
        api.raise_image_not_found(e, e.response)
    return response.status == HTTPStatus.CREATED


def history(api, name):
    """get image history"""
    try:
        response = api.get(f"/images/{api.quote(name)}/history")
    except errors.NotFoundError as e:
        api.raise_image_not_found(e, e.response)
    return json.loads(str(response.read(), "utf-8"))


__all__ = [
    "list_images",
    "inspect",
    "image_exists",
    "remove",
    "tag_image",
]
