class Pod:
    pass


class PodManager:
    def __init__(self, client: 'PodmanClient'):
        self.client = client
