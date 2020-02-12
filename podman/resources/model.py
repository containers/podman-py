class Model(object):
    """ A base class for representing a single object on the server. """
    id_attribute = 'Id'

    def __init__(self, attrs=None, client=None, collection=None):
        #: A client pointing at the server that this object is on.
        self.client = client

        #: The collection that this model is part of.
        self.collection = collection

        #: The raw representation of this object from the API
        self.attrs = attrs
        if self.attrs is None:
            self.attrs = {}

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.short_id}>'

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self):
        return hash("%s:%s" % (self.__class__.__name__, self.id))

    @property
    def id(self):
        """ The ID of the object. """
        return self.attrs.get(self.id_attribute)

    @property
    def short_id(self):
        """ The ID of the object, truncated to 10 characters. """
        return self.id[:10]

    def reload(self):
        """
        Load this object from the server again and update ``attrs`` with the
        new data.
        """
        new_model = self.collection.get(self.id)
        self.attrs = new_model.attrs

