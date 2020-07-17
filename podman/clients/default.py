import os
from podman.clients.lib import Client
from podman.clients.lib import ROOT_SOCKET
from podman.clients.lib import ROOTLESS_SOCKET


class Podman(Client):

    def __init__(self, url=None):
        url = url or ROOT_SOCKET
        super(Podman, self).__init__(url)


class PodmanRootless(Client):

    def __init__(self, url=None, user_uid=None):
        '''
        Notes:
            Before using this client you might want to double check if the user
            socket is up:
                systemctl status --user podman.socket
            If is not up then start it:
                systemctl start --user podman.socket
        '''
        url = url or ROOTLESS_SOCKET.format(user_uid or os.getuid())
        super(PodmanRootless, self).__init__(url)
