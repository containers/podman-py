class Event:
    pass


class EventManager:
    def __init__(self, client: 'PodmanClient'):
        self.client = client

    def apply(self, *args, **kwargs) -> object:
        pass
