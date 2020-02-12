""" Represents the entirety of the images on the server. """
import itertools
import re
import warnings
from typing import List

from .image import Image
from .registry_data import RegistryData
from ..collection import Collection
from ...errors import BuildError, ImageLoadError
from ...utils import parse_repository_tag
from ...utils.json_stream import json_stream


class ImageCollection(Collection):
    model = Image

    def build(self, **kwargs):
        """
        Build an image and return it. Similar to the ``podman build``
        command. Either ``path`` or ``fileobj`` must be set.

        If you have a tar file for the Podman build context (including a
        Podmanfile) already, pass a readable file-like object to ``fileobj``
        and also pass ``custom_context=True``. If the stream is compressed
        also, set ``encoding`` to the correct value (e.g ``gzip``).

        If you want to get the raw output of the build, use the
        :py:meth:`~podman.api.build.BuildApiMixin.build` method in the
        low-level API.

        Args:
            path (str): Path to the directory containing the Podmanfile
            fileobj: A file object to use as the Podmanfile. (Or a file-like
                object)
            tag (str): A tag to add to the final image
            quiet (bool): Whether to return the status
            nocache (bool): Don't use the cache when set to ``True``
            rm (bool): Remove intermediate containers. The ``podman build``
                command now defaults to ``--rm=true``, but we have kept the old
                default of `False` to preserve backward compatibility
            timeout (int): HTTP timeout
            custom_context (bool): Optional if using ``fileobj``
            encoding (str): The encoding for a stream. Set to ``gzip`` for
                compressing
            pull (bool): Downloads any updates to the FROM image in Podmanfiles
            forcerm (bool): Always remove intermediate containers, even after
                unsuccessful builds
            podmanfile (str): path within the build context to the Podmanfile
            buildargs (dict): A dictionary of build arguments
            container_limits (dict): A dictionary of limits applied to each
                container created by the build process. Valid keys:

                - memory (int): set memory limit for build
                - memswap (int): Total memory (memory + swap), -1 to disable
                    swap
                - cpushares (int): CPU shares (relative weight)
                - cpusetcpus (str): CPUs in which to allow execution, e.g.,
                    ``"0-3"``, ``"0,1"``
            shmsize (int): Size of `/dev/shm` in bytes. The size must be
                greater than 0. If omitted the system uses 64MB
            labels (dict): A dictionary of labels to set on the image
            cache_from (list): A list of images used for build cache
                resolution
            target (str): Name of the build-stage to build in a multi-stage
                Podmanfile
            network_mode (str): networking mode for the run commands during
                build
            squash (bool): Squash the resulting images layers into a
                single layer.
            extra_hosts (dict): Extra hosts to add to /etc/hosts in building
                containers, as a mapping of hostname to IP address.
            platform (str): Platform in the format ``os[/arch[/variant]]``.
            isolation (str): Isolation technology used during build.
                Default: `None`.
            use_config_proxy (bool): If ``True``, and if the podman client
                configuration file (``~/.podman/config.json`` by default)
                contains a proxy configuration, the corresponding environment
                variables will be set in the container being built.

        Returns:
            (tuple): The first item is the :py:class:`Image` object for the
                image that was build. The second item is a generator of the
                build logs as JSON-decoded objects.

        Raises:
            :py:class:`podman.errors.BuildError`
                If there is an error during the build.
            :py:class:`podman.errors.APIError`
                If the server returns any other error.
            ``TypeError``
                If neither ``path`` nor ``fileobj`` is specified.
        """
        resp = self.client.api.build(**kwargs)
        if isinstance(resp, str):
            return self.get(resp)
        last_event = None
        image_id = None
        result_stream, internal_stream = itertools.tee(json_stream(resp))
        for chunk in internal_stream:
            if 'error' in chunk:
                raise BuildError(chunk['error'], result_stream)
            if 'stream' in chunk:
                match = re.search(
                    r'(^Successfully built |sha256:)([0-9a-f]+)$',
                    chunk['stream']
                )
                if match:
                    image_id = match.group(2)
            last_event = chunk
        if image_id:
            return self.get(image_id), result_stream
        raise BuildError(last_event or 'Unknown', result_stream)

    def get(self, name):
        """
        Gets an image.

        Args:
            name (str): The name of the image.

        Returns:
            (:py:class:`Image`): The image.

        Raises:
            :py:class:`podman.errors.ImageNotFound`
                If the image does not exist.
            :py:class:`podman.errors.APIError`
                If the server returns an error.
        """
        return self.prepare_model(self.client.api.inspect_image(name))

    def get_registry_data(self, name, auth_config=None):
        """
        Gets the registry data for an image.

        Args:
            name (str): The name of the image.
            auth_config (dict): Override the credentials that are found in the
                config for this request.  ``auth_config`` should contain the
                ``username`` and ``password`` keys to be valid.

        Returns:
            (:py:class:`RegistryData`): The data object.

        Raises:
            :py:class:`podman.errors.APIError`
                If the server returns an error.
        """
        return RegistryData(
            image_name=name,
            attrs=self.client.api.inspect_distribution(name, auth_config),
            client=self.client,
            collection=self,
        )

    def list(self, name: str = None, all: bool = False, filters: bool = None) -> List[Image]:
        """
        List images on the server.

        Args:
            name: Only show images belonging to the repository ``name``
            all: Show intermediate image layers. By default, these are
                filtered out.
            filters: Filters to be processed on the image list.
                Available filters:
                - ``dangling`` (bool)
                - `label`: format either ``"key"``, ``"key=value"`` or a list of such.
                - `reference`: format (<image-name>[:<tag>])
                - `since`: (<image-name>[:<tag>], <image id> or <image@digest>

        Returns: List of :py:class:`Image`

        Raises:
            :py:class:`podman.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.images(name=name, all=all, filters=filters)
        return [self.get(r["Id"]) for r in resp]

    def load(self, data: bytes) -> List[Image]:
        """
        Load an image that was previously saved using
        :py:meth:`~podman.models.images.Image.save` (or ``podman save``).
        Similar to ``podman load``.

        Args:
            data: Image data to be loaded.

        Returns: The Images.

        Raises:
            :py:class:`podman.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.load_image(data)
        images = []
        for chunk in resp:
            if 'stream' in chunk:
                match = re.search(
                    r'(^Loaded image ID: |^Loaded image: )(.+)$',
                    chunk['stream']
                )
                if match:
                    image_id = match.group(2)
                    images.append(image_id)
            if 'error' in chunk:
                raise ImageLoadError(chunk['error'])

        return [self.get(i) for i in images]

    def pull(self, repository, tag=None, **kwargs):
        """
        Pull an image of the given name and return it. Similar to the
        ``podman pull`` command.
        If no tag is specified, all tags from that repository will be
        pulled.

        If you want to get the raw pull output, use the
        :py:meth:`~podman.api.image.ImageApiMixin.pull` method in the
        low-level API.

        Args:
            repository (str): The repository to pull
            tag (str): The tag to pull
            auth_config (dict): Override the credentials that are found in the
                config for this request.  ``auth_config`` should contain the
                ``username`` and ``password`` keys to be valid.
            platform (str): Platform in the format ``os[/arch[/variant]]``

        Returns:
            (:py:class:`Image` or list): The image that has been pulled.
                If no ``tag`` was specified, the method will return a list
                of :py:class:`Image` objects belonging to this repository.

        Raises:
            :py:class:`podman.errors.APIError`
                If the server returns an error.

        Example:

            >>> from podman import PodmanClient
            >>> client = PodmanClient()

            >>> # Pull the image tagged `latest` in the busybox repo
            >>> image = client.images.pull('busybox:latest')

            >>> # Pull all tags in the busybox repo
            >>> images = client.images.pull('busybox')
        """
        if not tag:
            repository, tag = parse_repository_tag(repository)

        if 'stream' in kwargs:
            warnings.warn(
                '`stream` is not a valid parameter for this method'
                ' and will be overridden'
            )
            del kwargs['stream']

        pull_log = self.client.api.pull(
            repository, tag=tag, stream=True, **kwargs
        )
        for _ in pull_log:
            # We don't do anything with the logs, but we need
            # to keep the connection alive and wait for the image
            # to be pulled.
            pass
        if tag:
            return self.get('{0}{2}{1}'.format(
                repository, tag, '@' if tag.startswith('sha256:') else ':'
            ))
        return self.list(repository)

    def push(self, repository, tag=None, **kwargs):
        return self.client.api.push(repository, tag=tag, **kwargs)
    # push.__doc__ = APIClient.push.__doc__

    def remove(self, *args, **kwargs):
        self.client.api.remove_image(*args, **kwargs)
    # remove.__doc__ = APIClient.remove_image.__doc__

    def search(self, *args, **kwargs):
        return self.client.api.search(*args, **kwargs)
    # search.__doc__ = APIClient.search.__doc__

    def prune(self, filters=None):
        return self.client.api.prune_images(filters=filters)
    # prune.__doc__ = APIClient.prune_images.__doc__

    def prune_builds(self, *args, **kwargs):
        return self.client.api.prune_builds(*args, **kwargs)
    # prune_builds.__doc__ = APIClient.prune_builds.__doc__
