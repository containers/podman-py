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
"""pod provides the pod operations for a Podman service"""
import json

import podman.errors as errors


def create(api, name, pod):
    """create a pod"""
    if not isinstance(pod, str):
        data = json.dumps(pod)
    else:
        data = pod
    path = '/pods/create?name={}'.format(api.quote(name))
    response = api.post(path, params=data, headers={'content-type': 'application/json'})
    return json.loads(str(response.read(), 'utf-8'))


def exists(api, name):
    """inspect a pod"""
    try:
        api.get('/pods/{}/exists'.format(api.quote(name)))
        return True
    except errors.NotFoundError:
        return False


def inspect(api, name):
    """inspect a pod"""
    try:
        response = api.get('/pods/{}/json'.format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.PodNotFound)


def kill(api, name, signal=None):
    """kill a pod"""
    data = {}
    if signal:
        data['signal'] = signal
    try:
        response = api.post('/pods/{}/kill'.format(api.quote(name)), data)
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.PodNotFound)


def list_pods(api, filters=None):
    """list pod using filter"""
    filters_param = {}
    if filters:
        filters_param = {'filter': filters}
    response = api.get('/pods/json', filters_param)
    return json.loads(str(response.read(), 'utf-8'))


def list_processes(api, name, stream=None, ps_args=None):
    """list processes from a pod"""
    params = {}
    # TODO(mwhahaha): test stream
    if stream:
        params['stream'] = stream
    if ps_args:
        params['ps_args'] = ps_args
    response = api.get('/pods/{}/top'.format(api.quote(name)), params)
    return json.loads(str(response.read(), 'utf-8'))


def pause(api, name):
    """pause a pod"""
    try:
        response = api.post('/pods/{}/pause'.format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.PodNotFound)


def prune(api):
    """prune pods"""
    response = api.get('/pods/prune')
    return json.loads(str(response.read(), 'utf-8'))


def remove(api, name, force=None):
    """Remove named/identified image from Podman storage."""
    params = {}
    path = '/pods/{}'.format(api.quote(name))
    if force is not None:
        params = {'force': force}
    try:
        response = api.delete(path, params)
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.PodNotFound)


def restart(api, name):
    """restart a pod"""
    try:
        response = api.post('/pods/{}/restart'.format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.PodNotFound)


def start(api, name):
    """start a pod"""
    try:
        response = api.post('/pods/{}/start'.format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
        # TODO(mwhahaha): handle 304 warning
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.PodNotFound)


def stats(api, all_pods=True, pods=None):
    """get pods stats"""
    params = {'all': all_pods}
    if pods:
        params['namesOrIDs'] = pods
    try:
        response = api.post('/pods/stats', params)
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.PodNotFound)


def stop(api, name):
    """stop a pod"""
    try:
        response = api.post('/pods/{}/stop'.format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
        # TODO(mwhahaha): handle 304 warning
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.PodNotFound)


def unpause(api, name):
    """unpause a pod"""
    try:
        response = api.post('/pods/{}/unpause'.format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.PodNotFound)


__all__ = [
    "create",
    "exists",
    "inspect",
    "kill",
    "list_pods",
    "list_processes",
    "pause",
    "prune",
    "remove",
    "restart",
    "stats",
    "start",
    "stop",
    "unpause",
]
