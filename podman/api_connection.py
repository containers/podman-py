""" Provides a Connection to a Podman service. """
import json
import logging
import socket
import urllib.parse
from contextlib import AbstractContextManager
from http import HTTPStatus
from http.client import HTTPConnection

import podman.containers as containers
import podman.errors as errors
import podman.images as images
import podman.system as system


class ApiConnection(HTTPConnection, AbstractContextManager):
    """
    ApiConnection provides a specialized HTTPConnection
    to a Podman service.
    """

    def __init__(self, url, base="/v2.0.0/libpod", *args, **kwargs):  # pylint: disable-msg=W1113
        if url is None or not url:
            raise ValueError("url is required for service connection.")

        super().__init__("localhost", *args, **kwargs)
        supported_schemes = ("unix", "ssh")
        uri = urllib.parse.urlparse(url)
        if uri.scheme not in supported_schemes:
            raise ValueError(
                "The scheme '{}' is not supported, only {}".format(uri.scheme, supported_schemes)
            )
        self.uri = uri
        self.base = base

    def connect(self):
        """Connect to the URL given when initializing class"""
        if self.uri.scheme == "unix":
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.uri.path)
            self.sock = sock
        else:
            raise NotImplementedError("Scheme {} not yet implemented".format(self.uri.scheme))

    def delete(self, path, params=None):
        """Basic DELETE wrapper for requests

        Send a delete request with params added to the url as a query string

        :param path: url part to the call, appended to self.base
        :param params: optional dictionary of query params added to the request
        :return: http response object
        """
        return self.request("DELETE", self.join(path, params))

    def get(self, path, params=None):
        """Basic GET wrapper for requests

        Send a get request with params added to the url as a query string

        :param path: url part to the call, appended to self.base
        :param params: optional dictionary of query params added to the request
        :return: http response object
        """
        return self.request("GET", self.join(path, params))

    def post(self, path, params=None, headers=None, encode=False):
        """Basic POST wrapper for requests

        Send a POST request with params converted into a urlencoded form to be
        sent with the post.

        :param path: url part to the call, appended to self.base
        :param params: optional dictionary of query params added to the post
                       request as url encoded form data
        :param headers: optional dictionary of request headers
        :param encode: flag to indicate if you want the params to be encoded
                       prior to posting. When set to False, params are posted
                       directly as the body of the request.
        :return: http response object
        """
        data = params
        if not headers:
            headers = {}

        if encode:
            if "content-type" not in set(key.lower() for key in headers) and params:
                headers["content-type"] = "application/x-www-form-urlencoded"

            data = urllib.parse.urlencode(params)
        return self.request('POST', self.join(path), body=data, headers=headers)

    def request(self, method, url, body=None, headers=None, *, encode_chunked=False):
        """Make request to Podman service."""
        if headers is None:
            headers = {}

        super().request(method, url, body, headers, encode_chunked=encode_chunked)
        response = super().getresponse()

        # Errors are mapped to exceptions
        if HTTPStatus.OK <= response.status < HTTPStatus.MULTIPLE_CHOICES:
            pass
        elif HTTPStatus.NOT_FOUND == response.status:
            raise errors.NotFoundError(
                "Request {}:{} failed: {}".format(
                    method,
                    url,
                    HTTPStatus.NOT_FOUND.description or HTTPStatus.NOT_FOUND.phrase,
                ),
                response,
            )
        elif (
            response.status >= HTTPStatus.BAD_REQUEST
            and response.status < HTTPStatus.INTERNAL_SERVER_ERROR
        ):
            raise errors.RequestError(
                "Request {}:{} failed: {}".format(
                    method,
                    url,
                    response.reason or "Response Status Code {}".format(response.status),
                ),
                response,
            )
        elif response.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            raise errors.InternalServerError(
                "Request {}:{} failed: {}".format(
                    method,
                    url,
                    HTTPStatus.INTERNAL_SERVER_ERROR.description
                    or HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
                ),
                response,
            )
        return response

    def join(self, path, query=None):
        """Create a service URL.  Join base + path + query parameters"""
        path = self.base + path
        if query is not None:
            query = urllib.parse.urlencode(query)
            path = path + "?" + query
        return path

    @staticmethod
    def quote(value):
        """Quote value for use in a URL"""
        return urllib.parse.quote(value)

    @staticmethod
    def raise_not_found(exc, response, exception_type=errors.ImageNotFound):
        """helper function to raise a not found exception of exception_type"""
        body = json.loads(response.read())
        logging.info(body["cause"])
        raise exception_type(body["message"]) from exc

    def __exit__(self, exc_type, exc_value, traceback):
        super().close()


if __name__ == "__main__":  # pragma: no cover
    with ApiConnection("unix:///run/podman/podman.sock") as api:
        print(system.version(api))
        print(images.list_images(api))
        print(containers.list_containers(api))

        try:
            images.inspect(api, "bozo the clown")
        except errors.ImageNotFound as e:
            print(e)
