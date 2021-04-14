# podman-py

This python package is a set of bindings to use the new RESTful API in [libpod](https://github.com/containers/libpod).  It is currently under development and contributors are welcome!

## Dependencies

The following packages (or their distro-equivilents) are required:

* `python3-coverage`
* `python3-pylint`
* `python3-requests`
* `python3-requests-mock`
* `python3-fixtures`

## Example usage

```python

from podman import PodmanClient

# Provide a URI path for the libpod service.  In libpod, the URI can be a unix
# domain socket(UDS) or TCP.  The TCP connection has not been implemented in this
# package yet.

uri = "unix://localhost/run/podman/podman.sock"

with PodmanClient(uri) as client:
    print("version: ", client.version())
    # get all images
    images = client.images.list()
    # print the first one
    print(images[0])
    # find all containers
    containers = client.containers.list()
    # assuming there is at least one
    first_name = containers[0]['Names'][0]
    # inspect that one
    container = client.containers.get(first_name)
    print(container)
    # available fields
    print(sorted(container.attrs.keys()))
    client.images.remove(images.id)
```

## Contributing

See [CONTRIBUTING.md](https://github.com/containers/podman-py/blob/master/CONTRIBUTING.md)
