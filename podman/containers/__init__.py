"""containers provides the operations against containers for a Podman service.
"""

import json
from http import HTTPStatus

import podman.errors as errors


def attach(api, name):
    """Attach to a container"""
    raise NotImplementedError('Attach not implemented yet')


def changes(api, name):
    """Get files added, deleted or modified in a container"""
    try:
        response = api.get('/containers/{}/changes'.format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def checkpoint(
    api,
    name,
    export_image=None,
    ignore_root_fs=None,
    keep=None,
    leave_running=None,
    tcp_established=None,
):
    """Copy tar of files into a container"""
    path = '/containers/{}/checkpoint'.format(api.quote(name))
    params = {}
    if export_image is not None:
        params['export'] = export_image
    if ignore_root_fs is not None:
        params['ignoreRootFS'] = ignore_root_fs
    if keep is not None:
        params['keep'] = keep
    if leave_running is not None:
        params['leaveRunning'] = leave_running
    if tcp_established is not None:
        params['tcpEstablished'] = tcp_established
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        return response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def copy(api, name, file_path, pause_container=None):
    """Copy tar of files into a container"""
    path = '/containers/{}/copy'.format(api.quote(name))
    params = {'path': file_path}
    if pause_container is not None:
        params['pause'] = pause_container
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        response.read()
        return True
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def container_exists(api, name):
    """Check if container exists"""
    try:
        api.get("/containers/{}/exists".format(api.quote(name)))
        return True
    except errors.NotFoundError:
        return False


def create(api, container_data):
    """Create a container with the provided attributes

    container_data is a dictionary contining the container attributes for
    creation. See documentation for specifics.
    https://docs.podman.io/en/latest/_static/api.html#operation/libpodCreateContainer
    """
    try:
        response = api.post(
            "/containers/create",
            params=container_data,
            headers={'content-type': 'application/json'},
        )
        response.read()
        return response.status == HTTPStatus.CREATED
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def export(api, name):
    """Container export"""
    try:
        response = api.get("/containers/{}/export".format(api.quote(name)))
        return response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def healthcheck(api, name):
    """Execute container healthcheck"""
    try:
        response = api.get('/containers/{}/healthcheck'.format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def init(api, name):
    """Initialize a container

    Returns true if successful, false if already done
    """
    try:
        response = api.post('/containers/{}/init'.format(api.quote(name)))
        response.read()
        return response.status == HTTPStatus.NO_CONTENT
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def inspect(api, name):
    """Report on named container for a Podman service.
    Name may also be a container ID.
    """
    try:
        response = api.get('/containers/{}/json'.format(api.quote(name)))
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


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


def list_containers(api, all_=None, filters=None, limit=None, size=None, sync=None):
    """List all images for a Podman service."""
    query = {}
    if all_ is not None:
        query["all"] = True
    if filters is not None:
        query["filters"] = filters
    if limit is not None:
        query["limit"] = limit
    if size is not None:
        query["size"] = size
    if sync is not None:
        query["sync"] = sync
    response = api.get("/containers/json", query)
    # observed to return None when no containers
    return json.loads(str(response.read(), "utf-8")) or []


def logs(api, name, follow=None, since=None, stderr=None, tail=None, timestamps=None, until=None):
    """Get stdout and stderr logs"""
    raise NotImplementedError('Logs not implemented yet')


def mount(api, name):
    """Mount container to the filesystem"""
    path = "/containers/{}/mount".format(api.quote(name))
    try:
        response = api.post(path, headers={'content-type': 'application/json'})
        return json.loads(str(response.read(), "utf-8"))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def pause(api, name):
    """Pause a container"""
    path = "/containers/{}/pause".format(api.quote(name))
    try:
        response = api.post(path, headers={'content-type': 'application/json'})
        response.read()
        return response.status == HTTPStatus.NO_CONTENT
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def prune(api, name, filters=None):
    """Remove stopped containers"""
    path = "/containers/{}/prune".format(api.quote(name))
    params = {}
    if filters is not None:
        params['filters'] = filters
    response = api.post(path, params=params, headers={'content-type': 'application/json'})
    return json.loads(str(response.read(), "utf-8"))


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


def resize(api, name, height, width):
    """Resize container tty"""
    path = "/containers/{}/resize".format(api.quote(name))
    params = {'h': height, 'w': width}
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def restart(api, name, timeout=None):
    """Restart container"""
    path = "/containers/{}/restart".format(api.quote(name))
    params = {}
    if timeout is not None:
        params['t'] = timeout
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        response.read()
        return response.status == HTTPStatus.NO_CONTENT
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def restore(
    api,
    name,
    ignore_root_fs=None,
    ignore_static_ip=None,
    ignore_static_mac=None,
    import_arg=None,
    keep=None,
    leave_running=None,
    container_name=None,
    tcp_established=None,
):
    """Restore container"""
    path = "/containers/{}/restore".format(api.quote(name))
    params = {}
    if ignore_root_fs is not None:
        params['ignoreRootFS'] = ignore_root_fs
    if ignore_static_ip is not None:
        params['ignoreStaticIP'] = ignore_static_ip
    if ignore_static_mac is not None:
        params['ignoreStaticMAC'] = ignore_static_mac
    if import_arg is not None:
        params['import'] = import_arg
    if keep is not None:
        params['keep'] = keep
    if leave_running is not None:
        params['leaveRunning'] = leave_running
    if container_name is not None:
        params['name'] = container_name
    if tcp_established is not None:
        params['tcpEstablished'] = tcp_established
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        # TODO(mwhahaha): handle returned tarball better
        return response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def show_mounted(api):
    """Show mounted containers"""
    response = api.get('/containers/showmounted')
    return json.loads(str(response.read(), 'utf-8'))


def start(api, name, detach_keys=None):
    """Start container"""
    path = "/containers/{}/start".format(api.quote(name))
    params = {}
    if detach_keys is not None:
        params['detachKeys'] = detach_keys
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        response.read()
        return response.status == HTTPStatus.NO_CONTENT
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def stats(api, containers=None, stream=True):
    """Get container stats container

    When stream is set to true, the raw HTTPResponse is returned.
    """
    path = "/containers/stats"
    params = {'stream': stream}
    if containers is not None:
        params['containers'] = containers
    try:
        response = api.get(path, params=params)
        if stream:
            return response
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def stop(api, name, timeout=None):
    """Stop container"""
    path = "/containers/{}/stop".format(api.quote(name))
    params = {}
    if timeout is not None:
        params['t'] = timeout
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        response.read()
        return response.status == HTTPStatus.NO_CONTENT
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def top(api, name, ps_args=None, stream=True):
    """List processes in a container

    When stream is set to true, the raw HTTPResponse is returned.
    """
    path = "/containers/{}/top".format(api.quote(name))
    params = {'stream': stream}
    if ps_args is not None:
        params['ps_args'] = ps_args
    try:
        response = api.get(path, params=params)
        if stream:
            return response
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def unmount(api, name):
    """Unmount container"""
    path = "/containers/{}/unmount".format(api.quote(name))
    try:
        response = api.post(path, headers={'content-type': 'application/json'})
        response.read()
        return response.status == HTTPStatus.NO_CONTENT
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def unpause(api, name):
    """Unpause container"""
    path = "/containers/{}/unpause".format(api.quote(name))
    try:
        response = api.post(path, headers={'content-type': 'application/json'})
        response.read()
        return response.status == HTTPStatus.NO_CONTENT
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


def wait(api, name, condition=None):
    """Wait for a container state"""
    path = "/containers/{}/wait".format(api.quote(name))
    params = {}
    if condition is not None:
        params['condition'] = condition
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        return json.loads(str(response.read(), 'utf-8'))
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)


__all__ = [
    "attach",
    "changes",
    "checkpoint",
    "copy",
    "container_exists",
    "export",
    "healthcheck",
    "inspect",
    "kill",
    "list_containers",
    "logs",
    "mount",
    "pause",
    "prune",
    "remove",
    "resize",
    "restore",
    "show_mounted",
    "start",
    "stop",
    "top",
    "unmount",
    "unpause",
    "wait",
]
