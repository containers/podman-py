class Volume:
    pass


class VolumeManager:
    def __init__(self, client: 'PodmanClient'):
        self.client = client
