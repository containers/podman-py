""" Python representation of a single OCI image on the server. """
from typing import Generator, Union, List

from ..model import Model
from ...constants import DEFAULT_DATA_CHUNK_SIZE


class Image(Model):
    """ An image on the server. """
    @property
    def labels(self) -> dict:
        """ The labels of an image as dictionary. """
        result = self.attrs['Config'].get('Labels')
        return result or {}

    @property
    def short_id(self) -> str:
        """
        The ID of the image truncated to 10 characters, plus the ``sha256:``
        prefix.
        """
        if self.id.startswith('sha256:'):
            return self.id[:17]
        return self.id[:10]

    @property
    def tags(self) -> List[str]:
        """ The image's tags. """
        tags = self.attrs.get('RepoTags')
        if tags is None:
            tags = []
        return [tag for tag in tags if tag != '<none>:<none>']

    def history(self) -> str:
        """
        Show the history of an image.

        Returns: The history of the image.

        Raises:
            :py:class:`podman.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.history(self.id)

    def save(self, chunk_size: int = DEFAULT_DATA_CHUNK_SIZE, named: Union[bool, str] = False) -> Generator:
        """
        Get a tarball of an image. Similar to the ``podman save`` command.

        Args:
            chunk_size: The generator will return up to that much data
                per iteration, but may return less. If ``None``, data will be
                streamed as it is received. Default: 2 MB
            named: If ``False`` (default), the tarball will not
                retain repository and tag information for this image. If set
                to ``True``, the first tag in the :py:attr:`~tags` list will
                be used to identify the image. Alternatively, any element of
                the :py:attr:`~tags` list can be used as an argument to use
                that specific tag as the saved identifier.

        Returns: A stream of raw archive data.

        Raises:
            :py:class:`podman.errors.APIError`
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
            if isinstance(named, str):
                if named not in self.tags:
                    raise ValueError(
                        "{} is not a valid tag for this image".format(named)
                    )
                    # raise InvalidArgument(
                    #     "{} is not a valid tag for this image".format(named)
                    # )
                img = named

        return self.client.api.get_image(img, chunk_size)

    def tag(self, repository: str, tag: str = None, force: bool = False) -> bool:
        """
        Tag this image into a repository. Similar to the ``podman tag``
        command.

        Args:
            repository: The repository to set for the tag
            tag: The tag name
            force: Force tagging

        Raises:
            :py:class:`podman.errors.APIError`
                If the server returns an error.

        Returns: `True` if tagging was successful, `False` if not
        """
        return self.client.api.tag(self.id, repository, tag=tag, force=force)

    def __repr__(self):
        tags = ', '.join(self.tags)
        return f"<{self.__class__.__name__}: '{tags}'>"
