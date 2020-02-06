import socket
import urllib.parse
from contextlib import AbstractContextManager
from http import HTTPStatus
from http.client import HTTPConnection

import errors
import images
import system


class ApiConnection(HTTPConnection, AbstractContextManager):
    def __init__(self, url, base="/v1.24/libpod", *args, **kwargs):
        if url is None:
            raise Exception("Must give unix domain url")

        super().__init__("localhost", *args, **kwargs)
        #         http.client.HTTPConnection.__init__(self, 'localhost')

        supported_schemes = ("unix", "ssh")
        uri = urllib.parse.urlparse(url)
        if uri.scheme not in ("unix", "ssh"):
            raise Exception(
                "The scheme '{}' is not supported, only {}".format(
                    uri.scheme, supported_schemes
                )
            )
        self.uri = uri
        self.base = base

    def connect(self):
        if self.uri.scheme == "unix":
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.uri.path)
            self.sock = sock
        else:
            raise NotImplementedError(
                "Scheme {} not yet implemented".format(self.uri.scheme)
            )

    def request(self, method, url, *args, **kwargs):
        super().request(method, url, *args, **kwargs)
        response = super().getresponse()

        if HTTPStatus.OK <= response.status < HTTPStatus.MULTIPLE_CHOICES:
            return response
        elif HTTPStatus.NOT_FOUND == response.status:
            raise errors.NotFoundError(
                "Request {}:{} failed: {}".format(
                    method, url, HTTPStatus.NOT_FOUND.phrase
                ),
                response,
            )
        elif HTTPStatus.INTERNAL_SERVER_ERROR >= response.status:
            raise errors.InternalServerError(
                "Request {}:{} failed: {}".format(
                    method, url, HTTPStatus.INTERNAL_SERVER_ERROR.phrase
                ),
                response,
            )
        else:
            return response

    def join(self, path, query=None):
        p = self.base + path
        if query is not None:
            q = urllib.parse.urlencode(query)
            p = p + "?" + q
        return p

    def quote(self, value):
        return urllib.parse.quote(value)

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


if __name__ == "__main__":
    with ApiConnection("unix:///run/podman/podman.sock") as api:
        print(system.version(api))
        print(images.list(api))

        try:
            images.inspect(api, "bozo the clown")
        except errors.ImageNotFound as e:
            print(e)
