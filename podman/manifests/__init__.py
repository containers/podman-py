#   Copyright 2020 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#
"""manifests provides the manifest operations for a Podman service"""
import json
from http import HTTPStatus

from podman import errors


def add(api, name, manifest):
    """Add image to a manifest list"""
    path = f'/manifests/{api.quote(name)}/add'
    try:
        response = api.post(path, params=manifest, headers={'content-type': 'application/json'})
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ManifestNotFound)
    return response.status == HTTPStatus.OK


def create(api, name, image=None, all_contents=None):
    """create a manifest"""
    params = {'name': name}
    if image:
        params['image'] = image
    if all_contents:
        params['all'] = all_contents
    path = '/manifests/create'
    try:
        response = api.post(path, params=params)
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ManifestNotFound)
    return response.status == HTTPStatus.OK


def inspect(api, name):
    """inspect a manifest"""
    try:
        response = api.get(f'/manifests/{api.quote(name)}/json')
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ManifestNotFound)
    return json.loads(str(response.read(), 'utf-8'))


def push(api, name, destination, all_images=None):
    """push a manifest"""
    params = {'destination': destination}
    if all_images:
        params['all'] = all_images
    try:
        response = api.post(f'/manifests/{api.quote(name)}/push', params=params)
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ManifestNotFound)
    return response.status == HTTPStatus.OK


def remove(api, name, digest=None):
    """Remove manifest digest."""
    params = {}
    if digest:
        params['digest'] = digest
    path = f'/manifests/{api.quote(name)}'
    try:
        response = api.delete(path, params)
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ManifestNotFound)
    return response.status == HTTPStatus.OK


__all__ = [
    "add",
    "create",
    "inspect",
    "push",
    "remove",
]
