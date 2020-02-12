from .model import Model


class Collection(object):
    """
    A base class for representing all objects of a particular type on the
    server.
    """

    #: The type of object this collection represents, set by subclasses
    model = None

    def __init__(self, client=None):
        #: The client pointing at the server that this collection of objects
        #: is on.
        self.client = client

    def list(self):
        """ Get all items in this collection. """
        raise NotImplementedError

    def get(self, key):
        """ Get a single item identified by `key` from this collection. """
        raise NotImplementedError

    def create(self, attrs=None):
        """ Create a new item in this collection. """
        raise NotImplementedError

    def prepare_model(self, attrs):
        """ Create a model from a set of attributes. """
        if isinstance(attrs, Model):
            attrs.client = self.client
            attrs.collection = self
            return attrs
        elif isinstance(attrs, dict):
            return self.model(attrs=attrs, client=self.client, collection=self)
        else:
            raise Exception("Can't create %s from %s" %
                            (self.model.__name__, attrs))
