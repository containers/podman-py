import json
import urllib.parse
from podman.logger import logger


class Endpoint(object):
    path = None
    params = None
    headers = None
    api_ver = None
    domain = None

    def __init__(self, client, **kwargs):
        self.client = client
        self.path_vars = kwargs

    def get_domain(self):
        if not self.api_ver:
            raise TypeError('Endpoint.api_ver cannot be None')
        if not self.domain:
            raise TypeError('Endpoint.domain cannot be None')
        return "/{}{}".format(self.api_ver, self.domain)

    def get_path(self):
        path = self.path.format(**self.path_vars)
        return '{}{}'.format(
            self.get_domain(),
            path,
        )

    def get_headers(self):
        return self.headers or {}

    def get_params(self):
        return self.params or {}

    def request(self, method, params=None, body=None, headers=None, ec=False):
        # ----------------------------------------------------[Normalizing Args]
        headers = headers or {}
        params = params or {}

        # ---------------------------------------------------[Merging Constants]
        headers.update(self.get_headers())
        params.update(self.get_params())

        # -----------------------------------------------------[Normalizing URL]
        url = "{}?{}".format(
            self.get_path(),
            urllib.parse.urlencode(params),
            )

        logger.debug("Request - {} {}".format(method, url))
        logger.debug("Request - Headers - {}".format(headers))
        logger.debug("Request - Body - {}".format(body))

        resp = self.client.request(method, url, body, headers, ec)

        logger.debug("Response - Status - {}".format(resp.status))

        return resp

    def get(self, params=None, headers=None, ec=False):
        return self.request("GET", params, None, headers, ec)

    def post(self, data=None, params=None, headers=None, ec=False):
        return self.request("POST", params, data, headers, ec)

    def delete(self, params=None, headers=None, ec=False):
        return self.request("DELETE", params, None, headers, ec)

    def put(self, data=None, params=None, headers=None, ec=False):
        return self.request("PUT", params, data, headers, ec)

# TODO should we move it to a proper module called default or api?
class Libpod124Endpoint(Endpoint):
    api_ver = "v1.24"
    domain = "/libpod"
