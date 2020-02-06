# podman-py
This python package is a set of bindings to use the new RESTful API in [libpod](https://github.com/containers/libpod).  It is currently under development and contributors are welcome!

## Example usage
```python

import podman

# Provide a URI path for the libpod service.  In libpod, the URI can be a unix
# domain socket(UDS) or TCP.  The TCP connection has not been implemented in this
# package yet.

uri = "unix://localhost/run/podman/podman.sock"

with APIConnection(uri) as api:
  # results are written to the screen as python dictionaries
  print(system.version(api))
  print(images.remove(api, "alpine", force=True)
```

## Contributing
See [CONTRIBUTING.md](https://github.com/containers/podman-py/blob/master/README.md)
