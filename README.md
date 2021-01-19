# podman-py

This python package is a set of bindings to use the new RESTful API in [libpod](https://github.com/containers/libpod).  It is currently under development and contributors are welcome!

## Example usage

```python

from podman import ApiConnection, system, images, containers

# Provide a URI path for the libpod service.  In libpod, the URI can be a unix
# domain socket(UDS) or TCP.  The TCP connection has not been implemented in this
# package yet.

uri = "unix://localhost/run/podman/podman.sock"

with ApiConnection(uri) as api:
  # results are written to the screen as python dictionaries
  print(system.version(api))
  # get all images
  l_images = images.list_images(api)
  # print the first one
  print(l_images[0])
  # find all containers
  l_containers = containers.list_containers(api)
  # assuming there is at least one
  first_name = l_containers[0]['Names'][0]
  # inspect that one
  container_details = containers.inspect(api, first_name)
  print(container_details)
  # available fields
  print(sorted(container_details.keys()))
  print(images.remove(api, "alpine", force=True))
```

## Contributing

See [CONTRIBUTING.md](https://github.com/containers/podman-py/blob/master/CONTRIBUTING.md)
