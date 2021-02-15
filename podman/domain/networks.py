class Network:
    pass


class NetworkManager:
    def __init__(self, client: 'PodmanClient'):
        self.client = client
