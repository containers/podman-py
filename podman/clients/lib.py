import os
from http import HTTPStatus
from contextlib import AbstractContextManager
from podman.http import HTTPConnectionSocket


ROOT_SOCKET = 'unix://localhost/run/podman/podman.sock'
ROOTLESS_SOCKET = "unix://localhost/run/user/{}/podman/podman.sock"


# class Client(object):
class Client(AbstractContextManager):

    def __init__(self, socker_uri, *args, **kwargs):
        self.http = HTTPConnectionSocket(socker_uri)
        # super(Client, self).__init__()

    def request(self, method, url, body, headers, ec=False):
        self.http.request(
            method, url, body, headers, encode_chunked=ec)
        return self.http.getresponse()

    def __exit__(self, exc_type, exc_value, traceback):
        self.http.close()
