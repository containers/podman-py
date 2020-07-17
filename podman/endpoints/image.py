from podman.endpoints.lib import Libpod124Endpoint


class ImagesEndpoint(Libpod124Endpoint):
    '''
    Supported Verbs:
        - GET
    '''
    path = "/images/json"


class ImagesInspectEndpoint(Libpod124Endpoint):
    '''
    Supported Verbs:
        - GET
    '''
    path = "/images/{uid}/json"


class ImagesExistEndpoint(Libpod124Endpoint):
    '''
    Supported Verbs:
        - GET
    '''
    path = "/images/{uid}/exists"


class ImagesRemoveEndpoint(ImagesInspectEndpoint):
    '''
    Supported Verbs:
        - PUT
    '''
    path = "/images/{uid}/json"


class ImagesForceRemoveEndpoint(ImagesInspectEndpoint):
    '''
    Supported Verbs:
        - PUT
    '''
    path = "/images/{uid}/json"
    params = {
        "force": True,
    }
