from podman.endpoints.lib import Libpod124Endpoint


class PingEndpoint(Libpod124Endpoint):
    '''
    Supported Verbs:
        - GET
    '''
    path = "/_ping"


class InfoEndpoint(Libpod124Endpoint):
    '''
    Supported Verbs:
        - GET
    '''
    path = '/info'


class SystemDfEndpoint(Libpod124Endpoint):
    '''
    Supported Verbs:
        - GET
    '''
    path = '/system/df'


