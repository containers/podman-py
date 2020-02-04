from contextlib import contextmanager
from urllib.parse import urlparse, urlencode
import http.client
import libpod_errors
import os

default_libpod_path = "/v1.24/libpod"

class Context:
    def __init__(self, **kwargs):
        self.contents = kwargs

    @contextmanager
    def get_connection(self):
        conn = self.contents["conn"]
        yield conn


class Connection:
    address = ""
    path = default_libpod_path

    # client
    def __init__(self, address, client):
        self.address = address
        self.client = client

    def do_request(self, method, path, path_params=None, query_params=None):
        #  TODO path params also need to escaped and made safe
        if path_params is None:
            path_params = []
        endpoint = os.path.join(default_libpod_path, path.format(*path_params))
        # u = urlparse(endpoint)
        if query_params is not None:
            endpoint = "{}?{}".format(endpoint, urlencode(query_params, doseq=True))
        # new_url = u._replace(query=query_safe_string)
        print(endpoint)
        self.client.request(method, endpoint)
        return self.client.getresponse()


def new_connection(uri):
    # urlparse doesn't parse URIs so doing dirty way for now
    if uri.startswith("tcp:"):
        conn = new_tcp_connection(uri)
        return Context(conn=conn)
    elif uri.startswith("unix:"):
        new_unix_connection(uri)
    else:
        print("unable to parse uri: only tcp and unix are supported")
        exit(1)


def new_tcp_connection(uri):
    # remove tcp: from the uri and add http so urlparse can do its job
    address = uri.replace("tcp:", "http://")
    u = urlparse(address)
    conn = http.client.HTTPConnection("{}".format(u.hostname), port=u.port)
    return Connection(address, conn)


def new_unix_connection(uri):
    _ = uri
    raise libpod_errors.ErrNotImplemented("", "this function is not implemented yet")
