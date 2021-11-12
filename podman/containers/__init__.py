"""containers provides the operations against containers for a Podman service.
"""

import json
from http import HTTPStatus

from podman import errors


def attach(api, name):
    """Attach to a container"""
    raise NotImplementedError('Attach not implemented yet')


def changes(api, name):
    """Get files added, deleted or modified in a container"""
    try:
        response = api.get(f'/containers/{api.quote(name)}/changes')
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return json.loads(str(response.read(), 'utf-8'))


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
    path = f'/containers/{api.quote(name)}/checkpoint'
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
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return response.read()


def copy(api, name, file_path, pause_container=None):
    """Copy tar of files into a container"""
    path = f'/containers/{api.quote(name)}/copy'
    params = {'path': file_path}
    if pause_container is not None:
        params['pause'] = pause_container
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return True


def container_exists(api, name):
    """Check if container exists"""
    try:
        api.get(f"/containers/{api.quote(name)}/exists")
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
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return response.status == HTTPStatus.CREATED


def export(api, name):
    """Container export"""
    try:
        response = api.get(f"/containers/{api.quote(name)}/export")
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return response.read()


def healthcheck(api, name):
    """Execute container healthcheck"""
    try:
        response = api.get(f'/containers/{api.quote(name)}/healthcheck')
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return json.loads(str(response.read(), 'utf-8'))


def init(api, name):
    """Initialize a container

    Returns true if successful, false if already done
    """
    try:
        response = api.post(f'/containers/{api.quote(name)}/init')
        response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return response.status == HTTPStatus.NO_CONTENT


def inspect(api, name):
    """Report on named container for a Podman service.
    Name may also be a container ID.
    """
    try:
        response = api.get(f'/containers/{api.quote(name)}/json')
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return json.loads(str(response.read(), 'utf-8'))


def kill(api, name, signal=None):
    """kill named/identified container"""
    path = f"/containers/{api.quote(name)}/kill"
    params = {}
    if signal is not None:
        params = {'signal': signal}

    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        # returns an empty bytes object
        response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return True


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
    path = f"/containers/{api.quote(name)}/mount"
    try:
        response = api.post(path, headers={'content-type': 'application/json'})
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return json.loads(str(response.read(), "utf-8"))


def pause(api, name):
    """Pause a container"""
    path = f"/containers/{api.quote(name)}/pause"
    try:
        response = api.post(path, headers={'content-type': 'application/json'})
        response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return response.status == HTTPStatus.NO_CONTENT


def prune(api, name, filters=None):
    """Remove stopped containers"""
    path = f"/containers/{api.quote(name)}/prune"
    params = {}
    if filters is not None:
        params['filters'] = filters
    response = api.post(path, params=params, headers={'content-type': 'application/json'})
    return json.loads(str(response.read(), "utf-8"))


def remove(api, name, force=None, delete_volumes=None):
    """Delete container"""
    path = f"/containers/{api.quote(name)}"
    params = {}
    if force is not None:
        params['force'] = force
    if delete_volumes is not None:
        params['v'] = delete_volumes

    try:
        response = api.delete(path, params)
        # returns an empty bytes object
        response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return True


def resize(api, name, height, width):
    """Resize container tty"""
    path = f"/containers/{api.quote(name)}/resize"
    params = {'h': height, 'w': width}
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return json.loads(str(response.read(), 'utf-8'))


def restart(api, name, timeout=None):
    """Restart container"""
    path = f"/containers/{api.quote(name)}/restart"
    params = {}
    if timeout is not None:
        params['t'] = timeout
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return response.status == HTTPStatus.NO_CONTENT


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
    path = f"/containers/{api.quote(name)}/restore"
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
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    # TODO(mwhahaha): handle returned tarball better
    return response.read()


def show_mounted(api):
    """Show mounted containers"""
    response = api.get('/containers/showmounted')
    return json.loads(str(response.read(), 'utf-8'))


def start(api, name, detach_keys=None):
    """Start container"""
    path = f"/containers/{api.quote(name)}/start"
    params = {}
    if detach_keys is not None:
        params['detachKeys'] = detach_keys
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return response.status == HTTPStatus.NO_CONTENT


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
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return json.loads(str(response.read(), 'utf-8'))


def stop(api, name, timeout=None):
    """Stop container"""
    path = f"/containers/{api.quote(name)}/stop"
    params = {}
    if timeout is not None:
        params['t'] = timeout
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
        response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return response.status == HTTPStatus.NO_CONTENT


def top(api, name, ps_args=None, stream=True):
    """List processes in a container

    When stream is set to true, the raw HTTPResponse is returned.
    """
    path = f"/containers/{api.quote(name)}/top"
    params = {'stream': stream}
    if ps_args is not None:
        params['ps_args'] = ps_args
    try:
        response = api.get(path, params=params)
        if stream:
            return response
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return json.loads(str(response.read(), 'utf-8'))


def unmount(api, name):
    """Unmount container"""
    path = f"/containers/{api.quote(name)}/unmount"
    try:
        response = api.post(path, headers={'content-type': 'application/json'})
        response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return response.status == HTTPStatus.NO_CONTENT


def unpause(api, name):
    """Unpause container"""
    path = f"/containers/{api.quote(name)}/unpause"
    try:
        response = api.post(path, headers={'content-type': 'application/json'})
        response.read()
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return response.status == HTTPStatus.NO_CONTENT


def wait(api, name, condition=None):
    """Wait for a container state"""
    path = f"/containers/{api.quote(name)}/wait"
    params = {}
    if condition is not None:
        params['condition'] = condition
    try:
        response = api.post(path, params=params, headers={'content-type': 'application/json'})
    except errors.NotFoundError as e:
        api.raise_not_found(e, e.response, errors.ContainerNotFound)
    return json.loads(str(response.read(), 'utf-8'))


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
