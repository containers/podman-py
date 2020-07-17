from http import HTTPStatus
from podman.exceptions import EntityNotFound
from podman.endpoints import ImagesEndpoint
from podman.endpoints import ImagesInspectEndpoint
from podman.endpoints import ImagesExistEndpoint
from podman.endpoints import ImagesRemoveEndpoint
from podman.services.lib import Service


class GetAllImages(Service):

    def get_response(self):
        return ImagesEndpoint(self.client).get()


class GetImage(Service):

    def __init__(self, client, uid):
        self.uid = uid
        super(GetImage, self).__init__(client)

    def get_response(self):
        resp = ImagesInspectEndpoint(self.client, uid=self.uid).get()
        if resp.status_code == 404 and resp.content:
            raise EntityNotFound(resp)


class RemoveImage(GetImage):
    def get_response(self):
        return ImagesRemoveEndpoint(self.client, self.uid).delete()


class ImageExists(GetImage):
    def get_response(self):
        return ImagesExistEndpoint(self.client, self.uid).get()