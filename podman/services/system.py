from http import HTTPStatus
from podman.exceptions import EntityNotFound
from podman.endpoints import InfoEndpoint
from podman.services.lib import Service


class GetInfo(Service):

    def get_response(self):
        return InfoEndpoint(self.client).get()
