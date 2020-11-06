"""images provides the operations against images for a Podman service."""
import json
import logging

import podman.errors as errors


def commit(api, **kwargs):
    """Create a new image from a container"""
    # this endpoint is non-functional podman 1.9.2
    response = api.make_call(api, "/commit", "POST", kwargs)
    tag = kwargs['tag']
    # an empty 201 response is sent back, some JSON feedback feels more appropriate
    if response.status == 201:
        return {'Container_created': tag}
    return json.loads(response.read())


def run_healthcheck(api, name):
    """Execute the defined healthcheck and return information about the results"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/healthcheck".format(name)
    response = api.make_call(api, path)
    return json.loads(response.read())


def delete_container(api, name, params=None):
    """Delete a container"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}".format(name)
    return json.loads(api.make_call(api, path, 'DELETE', params))


def attach_to_container(api, name, **kwargs):
    """Hijacks the connection to forward the containers stand streams to the client"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/attach".format(name)
    return json.loads(api.make_call(api, path, "POST", kwargs))


def report_fs_changes(api, name):
    """Returns which files in a containers filesystem have been changed"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/changes".format(name)
    return json.loads(api.make_call(api, path))


def checkpoint(api, name, **kwargs):
    """Creates a checkpoint file"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/checkpoint".format(name)
    response = api.make_call(api, path, "POST", kwargs)
    # if user requests export a tarball will be returned, catch that
    json_resp = json.loads(response)
    try:
        json_resp = json.loads(response)
        return json_resp
    except json.decoder.JSONDecodeError:
        return response


def check_container_exists(api, name):
    """Quick way to determine if container exists by name or ID"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/exists".format(name)
    response = api.make_call(api, path)
    # HTTP 204 empty response returned on success, give them some nice json
    if response.status == 204:
        return {name : "exists"}
    return json.loads(response)


def export_container(api, name):
    """Export the contents of a container as a tarball"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/export".format(name)
    response = api.make_call(api, path)
    # On success returns a tarball, on failure returns json
    if response.status == 200:
        return response
    return json.loads(response)


def initialize_container(api, name):
    """Performs all tasks requried to initialize container but does not start it"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/init".format(name)
    response = api.make_call(api, path)
    # HTTP 204 on success, 304 on already initialized
    if response.status == 204:
        return {name : "initializing"}
    if response.status == 304:
        return {name : "Already initialized"}
    return json.loads(response)


def inspect_container(api, name, params=None):
    """Returns low-level information about a container"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/json".format(name)
    return json.loads(api.make_call(api, path, params))


def kill_container(api, name, params=None):
    """Send a signal to a container, defaults to kill"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/kill".format(name)
    response = api.make_call(api, path, params)
    if response.status == 204:
        return {name: 'Signal Sent'}
    return json.loads(response)


def get_container_logs(api, name, params=None):
    """Get stdout and stderr logs from a container"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/logs".format(name)
    return json.loads(api.make_call(api, path, params))


def mount_container(api, name):
    """Mount a container to the filesystem"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/mount".format(name)
    return json.loads(api.make_call(api, path, "POST"))


def pause_container(api, name):
    """Use the cgroups freezer to suspend all process in a container"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/pause".format(name)
    response = api.make_call(api, path, "POST")
    # returns HTTP 204 on success
    if response.status == 204:
        return {name : 'Frozen'}
    return json.loads(response)


def resize_tty(api, name, **kwargs):
    """Resize the terminal attached to a container (for use with attach)"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/resize".format(name)
    return json.loads(api.make_call(api, path, "POST", kwargs))


def restart_container(api, name, params=None):
    """Restarts a container"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/restart".format(name)
    response = api.make_call(api, path, "POST", params)
    # returns HTTP 204 on success
    if response.status == 204:
        return {name : 'Restarted'}
    return json.loads(response)


def restore_container(api, name, **kwargs):
    """Restores a container"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/restore".format(name)
    response = api.make_call(api, path, "POST", kwargs)
    # returns tarball if exported
    try:
        return json.loads(response)
    except json.decoder.JSONDecodeError:
        return response


def start_container(api, name, params=None):
    """Starts a container"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/start".format(name)
    response = api.make_call(api, path, "POST", params)
    if response.status == 204:
        return {name : "Started"}
    if response.status == 304:
        return {name : "Already started"}
    return json.loads(response)


def get_container_stats(api, name, params=None):
    """Returns a live stream of a containers resource usage stats"""
    # TODO: figure out stream handling


def stop_container(api, name, params=None):
    """Stops a container"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/stop".format(name)
    response = api.make_call(api, path, "POST", params)
    if response.status == 204:
        return {name : "Stopped"}
    if response.status == 304:
        return {name : "Already stopped"}
    return json.loads(response)


def list_processes(api, name, params=None):
    """List processes running inside a container"""
    # this endpoint is non-functional podman 1.9.2
    # TODO: figure out stream handling


def unmount_container(api, name):
    """Unmount a container from the filesystem"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/unmount".format(name)
    response = api.make_call(api, path, "POST")
    if response.status == 204:
        return {name : "Unmounted"}
    return json.loads(response)


def unpause_container(api, name):
    """Stops a container"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/unpause".format(name)
    response = api.make_call(api, path, "POST")
    if response.status == 204:
        return {name : "Unpaused"}
    return json.loads(response)


def wait_on_container(api):
    """Wait on a container to meet a given condition"""
    # this endpoint is non-functional podman 1.9.2
    path = "/containers/{}/wait"
    return api.make_call(api, path, "POST")


def create_container(api, body):
    """Create a container"""
    # this endpoint is non-functional podman 1.9.2
    path = "containers/create"
    return json.loads(api.make_call(api, path, "POST", body=body))


def list_containers(api, params=None):
    """Return a list of containers"""
    # this endpoint is non-functianal in podman 1.9.2
    # currently just returns HTTP 200
    path = "/containers/json"
    return json.loads(api.make_call(api, path, params=params))


def delete_stopped_containers(api, **kwargs):
    """Remove containers not in use"""
    # this endpoint is non-functional in podman 1.9.2
    path = "/containers/prune"
    return json.loads(api.make_call(api, path, "POST", kwargs))


def show_mounted_containers(api):
    """Shows currently mounted container mountpoints"""
    # this endpoint is non-functional in podman 1.9.2
    path = "/containers/showmounted"
    return json.loads(api.make_call(api, path))


def generate_kube_yaml_file(api, name, params=None):
    """Create and run pods based on a Kubernetes YAML file (pod or service kind"""
    # this endpoint is non-functioanl in podman 1.9.2
    path = "/generate/{}/kube".format(name)
    return json.loads(api.make_call(api, path, params=params))


def create_based_on_kube_yaml_file(api, body, **kwargs):
    """Create and run pods based on a Kubernetes YAML file (pod or service kind"""
    # this endpoint is non-functiaon in podman 1.9.2
    path = "/play/kube"
    return json.loads(api.make_call(api, path, "POST", body, kwargs))


__all__ = [
    "commit",
    "run_healthcheck",
    "delete_container",
    "attach_to_container",
    "report_fs_changes",
    "checkpoint",
    "check_container_exists",
    "export_container",
    "initialize_container",
    "inspect_container",
    "kill_container",
    "get_container_logs",
    "mount_container",
    "pause_container",
    "resize_tty",
    "restart_container",
    "restore_container",
    "start_container",
    "get_container_stats",
    "stop_container",
    "list_processes",
    "unmount_container",
    "unpause_container",
    "wait_on_container",
    "create_container",
    "list_containers",
    "delete_stopped_containers",
    "show_mounted_containers",
    "generate_kube_yaml_file",
    "create_based_on_kube_yaml_file",
]
