# podman-py
[![Build Status](https://api.cirrus-ci.com/github/containers/podman-py.svg)](https://cirrus-ci.com/github/containers/podman-py/main)

This python package is a library of bindings to use the RESTful API of [Podman](https://github.com/containers/podman).
It is currently under development and contributors are welcome!


## Dependencies

* For runtime dependencies, see [requirements.txt](https://github.com/containers/podman-py/blob/main/requirements.txt).
* For testing and development dependencies, see [test-requirements.txt](https://github.com/containers/podman-py/blob/main/test-requirements.txt).

## Example usage

```python
"""Demonstrate PodmanClient."""
import json
from podman import PodmanClient

# Provide a URI path for the libpod service.  In libpod, the URI can be a unix
# domain socket(UDS) or TCP.  The TCP connection has not been implemented in this
# package yet.

uri = "unix:///run/user/1000/podman/podman.sock"

with PodmanClient(base_url=uri) as client:
    version = client.version()
    print("Release: ", version["Version"])
    print("Compatible API: ", version["ApiVersion"])
    print("Podman API: ", version["Components"][0]["Details"]["APIVersion"], "\n")

    # get all images
    for image in client.images.list():
        print(image, image.id, "\n")

    # find all containers
    for container in client.containers.list():
        first_name = container['Names'][0]
        container = client.containers.get(first_name)
        print(container, container.id, "\n")

        # available fields
        print(sorted(container.attrs.keys()))

    print(json.dumps(client.df(), indent=4))
```

## Contributing

See [CONTRIBUTING.md](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md)
