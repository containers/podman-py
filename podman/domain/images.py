class Image:
    pass


class ImageManager:
    def __init__(self, client: 'PodmanClient'):
        self.client = client
