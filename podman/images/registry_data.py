class RegistryData(Model):
    """
    Image metadata stored on the registry, including available platforms.
    """
    def __init__(self, image_name, *args, **kwargs):
        super(RegistryData, self).__init__(*args, **kwargs)
        self.image_name = image_name

    @property
    def id(self):
        """
        The ID of the object.
        """
        return self.attrs['Descriptor']['digest']

    @property
    def short_id(self):
        """
        The ID of the image truncated to 10 characters, plus the ``sha256:``
        prefix.
        """
        return self.id[:17]

    def pull(self, platform=None):
        """
        Pull the image digest.

        Args:
            platform (str): The platform to pull the image for.
            Default: ``None``

        Returns:
            (:py:class:`Image`): A reference to the pulled image.
        """
        repository, _ = parse_repository_tag(self.image_name)
        return self.collection.pull(repository, tag=self.id, platform=platform)

    def has_platform(self, platform):
        """
        Check whether the given platform identifier is available for this
        digest.

        Args:
            platform (str or dict): A string using the ``os[/arch[/variant]]``
                format, or a platform dictionary.

        Returns:
            (bool): ``True`` if the platform is recognized as available,
            ``False`` otherwise.

        Raises:
            :py:class:`docker.errors.InvalidArgument`
                If the platform argument is not a valid descriptor.
        """
        if platform and not isinstance(platform, dict):
            parts = platform.split('/')
            if len(parts) > 3 or len(parts) < 1:
                raise InvalidArgument(
                    '"{0}" is not a valid platform descriptor'.format(platform)
                )
            platform = {'os': parts[0]}
            if len(parts) > 2:
                platform['variant'] = parts[2]
            if len(parts) > 1:
                platform['architecture'] = parts[1]
        return normalize_platform(
            platform, self.client.version()
        ) in self.attrs['Platforms']

    def reload(self):
        self.attrs = self.client.api.inspect_distribution(self.image_name)

    reload.__doc__ = Model.reload.__doc__

