# podman-py
[![PyPI Latest Version](https://img.shields.io/pypi/v/podman)](https://pypi.org/project/podman/)

This python package is a library of bindings to use the RESTful API of [Podman](https://github.com/containers/podman).
It is currently under development and contributors are welcome!

## Installation

<div class="termy">

```console
pip install podman
```

</div>

---

**Documentation**: <a href="https://podman-py.readthedocs.io/en/latest/" target="_blank">https://podman-py.readthedocs.io/en/latest/</a>

**Source Code**: <a href="https://github.com/containers/podman-py" target="_blank">https://github.com/containers/podman-py</a>

---

## Dependencies

* For runtime dependencies, see \[dependencies\] in [pyproject.toml](https://github.com/containers/podman-py/blob/main/pyproject.toml)
* For testing and development dependencies, see \[project.optional.dependencies\] in [pyproject.toml](https://github.com/containers/podman-py/blob/main/pyproject.toml)
  * The package is split in \[progress\_bar\], \[docs\], and \[test\]

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
        # After a list call you would probably want to reload the container
        # to get the information about the variables such as status.
        # Note that list() ignores the sparse option and assumes True by default.
        container.reload()
        print(container, container.id, "\n")
        print(container, container.status, "\n")

        # available fields
        print(sorted(container.attrs.keys()))

    print(json.dumps(client.df(), indent=4))
```

## Contributing

See [CONTRIBUTING.md](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md)
