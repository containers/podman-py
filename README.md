# podman-py
This python package is a set of bindings to use the new RESTful API in [libpod](https://github.com/containers/libpod).  It is currently under development and contributors are welcome!

## Install

### Source

- For User

```bash
git clone https://github.com/containers/podman-py && \
    cd podman-py/ && \
    pip install --user .
```

- System wide

```bash
git clone https://github.com/containers/podman-py && \
    cd podman-py/ && \
    pip install .
```

### PYPI

No support yet

## Configuration

### Sockets

Before running anything this library gives you two option of connecting to the
Podman's socket.

1. *podman.clients.Podman* Class: By default Podman's socket is located at:
`/run/podman/podman.sock`. To connect to it you will need to run your script
with sudo.
2. *podman.clients.PodmanRootless* Class: If you think sudo is not suitable you
can use the rootless socket at: `/run/user/{uid}/podman/podman.sock`. Make sure
the systemd service is up: `systemctl status --user podman.socket`

## Usage

### Services

Let's grab the list of all current images.

```python
from podman.clients import PodmanRootless
from podman.services import GetAllImages

with PodmanRootless() as c:
    # Getting dict with all the images information
    data = GetAllImages(c).json()
    for img in data:
        print("{} {} {} {} MB".format(
            img["Names"][0],
            img["Labels"]["version"],
            img["Id"][:8],
            img["Size"]/(10**6)
            ))
```

Maybe we should check the system version before running some of our routines

```python
from podman.clients import PodmanRootless
from podman.services import GetAllImages
from podman.services import GetInfo

with PodmanRootless() as c:
    # Getting system info
    data = GetInfo(c).json()
    print("buildah {} cgroup {} at {}".format(
        data['host']['buildahVersion'],
        data['host']['cgroupVersion'],
        data['host']['arch'],
        ))
    # Getting dict with all the images information
    data = GetAllImages(c).json()
    for img in data:
        print("{} {} {} {} MB".format(
            img["Names"][0],
            img["Labels"]["version"],
            img["Id"][:8],
            img["Size"]/(10**6)
            ))
```

### Endpoints

If you are interested not only on the data but the status of the request's
response you want to use the endpoint classes. Below is the example of
how to redo the code snippet from the *Services* section:

```python
from podman.clients import PodmanRootless
from podman.endpoints import ImagesEndpoint
from podman.endpoints import InfoEndpoint

with PodmanRootless() as c:
    # Getting system info
    resp = InfoEndpoint(c).get()
    print("resp status code {}".format(resp.status_code))
    data = resp.json()
    print("buildah {} cgroup {} at {}".format(
        data['host']['buildahVersion'],
        data['host']['cgroupVersion'],
        data['host']['arch'],
        ))
    # Getting dict with all the images information
    resp = ImagesEndpoint(c).get()  # HTTP GET
    print("resp status code {}".format(resp.status_code))
    data = resp.json()
    for img in data:
        print("{} {} {} {} MB".format(
            img["Names"][0],
            img["Labels"]["version"],
            img["Id"][:8],
            img["Size"]/(10**6)
            ))
```

## Contributing
See [CONTRIBUTING.md](https://github.com/containers/podman-py/blob/master/CONTRIBUTING.md)
