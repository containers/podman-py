import json
from http import HTTPStatus
from podman.exceptions import EndpointNotFound
from podman.exceptions import InternalServerError


class Service (object):

    def __init__(self, client):
        self.client = client

    def json(self):
        resp = self.get_response()
        # This here does not make much sense since the 404 might not be an
        # actual network 404
        # if resp.status == HTTPStatus.NOT_FOUND:
        #     raise EndpointNotFound(
        #         resp._method,
        #         'resp.geturl()',
        #         HTTPStatus.NOT_FOUND.description,
        #         resp,
        #         )
        if resp.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            raise InternalServerError(
                resp.method,
                'resp.geturl()',
                resp.content,
                resp,
                )
        return json.loads(resp.read())

    def get_response(self):
        raise NotImplementedError
