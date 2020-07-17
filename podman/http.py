import os
import stat
import json
import socket
import urllib.parse
from http.client import HTTPConnection
from podman.exceptions import SchemaNotSupported
from podman.exceptions import SocketFileNotFound


class HttpResponse(object):  # TODO different name to avoid namespace issues
    def __init__(self, resp):
        '''
        Description:
            Created to replicate the behavior of requests library response.
        Params:
            resp (http.client.HTTPResponse):
                Normally sourced from HTTPConnection.getresponse function
        Attributes:
            http_response:
                holds the http.client.HTTPResponse passed through the args
                (resp). Only here for compatibility.
            status:
                holds http.client.HTTPResponse.status
            status_code:
                holds http.client.HTTPResponse.status
            content:
                return from http.client.HTTPResponse.read() (bytes)
            text:
                str version of the content field
            method:
                holds http.client.HTTPResponse._method
            headers:
                return from http.client.HTTPResponse.getheaders() but in dict
        '''
        self.http_response = resp
        self.status = resp.status
        self.status_code = resp.status
        self.content = resp.read()
        self.text = self.content
        self.method = resp._method
        self.headers = dict((k, v) for k, v in resp.getheaders())

    def json(self):
        return json.loads(self.content)

    def read(self):
        return self.content


class HTTPConnectionSocket(HTTPConnection):

    TIMEOUT = 10
    SUPPORTED_SCHEMAS = [
        "unix",
    ]

    def __init__(self, uri):
        if not uri:
            raise TypeError("uri cannot be None")
        try:
            self.uri = urllib.parse.url(uri)
        except AttributeError:
            self.uri = urllib.parse.urlparse(uri)
        super().__init__(self.uri.netloc)

    def connect(self):
        """Connect to the URL given when initializing class"""
        if self.uri.scheme in self.SUPPORTED_SCHEMAS:
            # Checking path here will avoid opening a socket for nothing
            if stat.S_ISSOCK(os.stat(self.uri.path).st_mode):
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(self.TIMEOUT)
                sock.connect(self.uri.path)
                self.sock = sock
            else:
                raise SocketFileNotFound(self.uri.path)
        else:
            raise SchemaNotSupported(self.uri.scheme, self.SUPPORTED_SCHEMAS)

    def getresponse(self):
        resp = super(HTTPConnectionSocket, self).getresponse()
        return HttpResponse(resp)