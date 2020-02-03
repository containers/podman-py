# podman-py
This python package is a set of bindings to use the new RESTful API in [libpod](https://github.com/containers/libpod).  It is currently under development
and contributors are welcome!


# Example usage

```

# Provide a URI path for the libpod service.  In libpod, the URI can be a unix
# domain socket(uds) or TCP.  The uds connection has not been implemented in this
# package yet.

uri = "tcp:localhost:8080/"

# Create a new connection based on the URI.  A new connection returns a 'context'

context = new_connection(uri)

# Call a image function such as 'remove'.
data = images.remove(context, "alpine", force=True)

# Dump out the response
print(data)
```
