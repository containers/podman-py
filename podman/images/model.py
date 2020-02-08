class Image(Model):
    """
    An image on the server.
    """
    def __repr__(self):
        return "<%s: '%s'>" % (self.__class__.__name__, "', '".join(self.tags))

    @property
    def labels(self):
        """
        The labels of an image as dictionary.
        """
        result = self.attrs['Config'].get('Labels')
        return result or {}

    @property
    def short_id(self):
        """
        The ID of the image truncated to 10 characters, plus the ``sha256:``
        prefix.
        """
        if self.id.startswith('sha256:'):
            return self.id[:17]
        return self.id[:10]

    @property
    def tags(self):
        """
        The image's tags.
        """
        tags = self.attrs.get('RepoTags')
        if tags is None:
            tags = []
        return [tag for tag in tags if tag != '<none>:<none>']

    def history(self):
        """
        Show the history of an image.

        Returns:
            (str): The history of the image.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.history(self.id)

    def save(self, chunk_size=DEFAULT_DATA_CHUNK_SIZE, named=False):
        """
        Get a tarball of an image. Similar to the ``docker save`` command.

        Args:
            chunk_size (int): The generator will return up to that much data
                per iteration, but may return less. If ``None``, data will be
                streamed as it is received. Default: 2 MB
            named (str or bool): If ``False`` (default), the tarball will not
                retain repository and tag information for this image. If set
                to ``True``, the first tag in the :py:attr:`~tags` list will
                be used to identify the image. Alternatively, any element of
                the :py:attr:`~tags` list can be used as an argument to use
                that specific tag as the saved identifier.

        Returns:
            (generator): A stream of raw archive data.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.

        Example:

            >>> image = cli.get_image("busybox:latest")
            >>> f = open('/tmp/busybox-latest.tar', 'wb')
            >>> for chunk in image:
            >>>   f.write(chunk)
            >>> f.close()
        """
        img = self.id
        if named:
            img = self.tags[0] if self.tags else img
            if isinstance(named, six.string_types):
                if named not in self.tags:
                    raise InvalidArgument(
                        "{} is not a valid tag for this image".format(named)
                    )
                img = named

        return self.client.api.get_image(img, chunk_size)

    def tag(self, repository, tag=None, **kwargs):
        """
        Tag this image into a repository. Similar to the ``docker tag``
        command.

        Args:
            repository (str): The repository to set for the tag
            tag (str): The tag name
            force (bool): Force

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.

        Returns:
            (bool): ``True`` if successful
        """
        return self.client.api.tag(self.id, repository, tag=tag, **kwargs)

