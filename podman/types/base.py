# TODO: Remove
class DictType(dict):
    def __init__(self, init: dict):
        for k, v in init.items():
            self[k] = v
