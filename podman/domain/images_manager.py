"""PodmanResource manager subclassed for Images."""

import builtins
import io
import json
import logging
import os
import urllib.parse
from typing import Any, Literal, Optional, Union
from collections.abc import Iterator, Mapping, Generator
from pathlib import Path
import requests

from podman import api
from podman.api.parse_utils import parse_repository
from podman.api.http_utils import encode_auth_header
from podman.domain.images import Image
from podman.domain.images_build import BuildMixin
from podman.domain.json_stream import json_stream
from podman.domain.manager import Manager
from podman.domain.registry_data import RegistryData
from podman.errors import APIError, ImageNotFound, PodmanError

try:
    from rich.progress import (
        Progress,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeRemainingColumn,
    )
except (ImportError, ModuleNotFoundError):
    Progress = None

logger = logging.getLogger("podman.images")


class ImagesManager(BuildMixin, Manager):
    """Specialized Manager for Image resources."""

    @property
    def resource(self):
        """Type[podman.domain.images.Image]: prepare_model() will create Image classes."""
        return Image

    def exists(self, key: str) -> bool:
        """Return true when image exists."""
        key = urllib.parse.quote_plus(key)
        response = self.client.get(f"/images/{key}/exists")
        return response.ok

    def list(self, **kwargs) -> builtins.list[Image]:
        """Report on images.

        Keyword Args:
            name (str) – Only show images belonging to the repository name
            all (bool) – Show intermediate image layers. By default, these are filtered out.
            filters (Mapping[str, Union[str, list[str]]) – Filters to be used on the image list.
                Available filters:

                - dangling (bool)
                - label (Union[str, list[str]]): format either "key" or "key=value"

        Raises:
            APIError: when service returns an error
        """
        filters = kwargs.get("filters", {}).copy()
        if name := kwargs.get("name"):
            filters["reference"] = name

        params = {
            "all": kwargs.get("all"),
            "filters": api.prepare_filters(filters=filters),
        }
        response = self.client.get("/images/json", params=params)
        if response.status_code == requests.codes.not_found:
            return []
        response.raise_for_status()

        return [self.prepare_model(attrs=i) for i in response.json()]

    # pylint is flagging 'name' here vs. 'key' parameter in super.get()
    def get(self, name: str) -> Image:  # pylint: disable=arguments-differ,arguments-renamed
        """Returns an image by name or id.

        Args:
            name: Image id or name for which to search

        Raises:
            ImageNotFound: when image does not exist
            APIError: when service returns an error
        """
        name = urllib.parse.quote_plus(name)
        response = self.client.get(f"/images/{name}/json")
        response.raise_for_status(not_found=ImageNotFound)

        return self.prepare_model(response.json())

    def get_registry_data(
        self,
        name: str,
        auth_config=Mapping[str, str],  # pylint: disable=unused-argument
    ) -> RegistryData:
        """Returns registry data for an image.

        Provided for compatibility

        Args:
            name: Image name
            auth_config: Override configured credentials. Keys username and password are required.

        Raises:
            APIError: when service returns an error
        """
        # FIXME populate attrs using auth_config
        image = self.get(name)
        return RegistryData(
            image_name=name,
            attrs=image.attrs,
            client=self.client,
            collection=self,
        )

    def load(
        self, data: Optional[bytes] = None, file_path: Optional[os.PathLike] = None
    ) -> Generator[bytes, None, None]:
        """Restore an image previously saved.

        Args:
            data: Image to be loaded in tarball format.
            file_path: Path of the Tarball.
                       It works with both str and Path-like objects

        Raises:
            APIError: When service returns an error.
            PodmanError: When the arguments are not set correctly.
        """
        # TODO fix podman swagger cannot use this header!
        # headers = {"Content-type": "application/x-www-form-urlencoded"}

        # Check that exactly one of the data or file_path is provided
        if not data and not file_path:
            raise PodmanError("The 'data' or 'file_path' parameter should be set.")

        if data and file_path:
            raise PodmanError(
                "Only one parameter should be set from 'data' and 'file_path' parameters."
            )

        post_data = data
        if file_path:
            # Convert to Path if file_path is a string
            file_path_object = Path(file_path)
            post_data = file_path_object.read_bytes()  # Read the tarball file as bytes

        # Make the client request before entering the generator
        response = self.client.post(
            "/images/load", data=post_data, headers={"Content-type": "application/x-tar"}
        )
        response.raise_for_status()  # Catch any errors before proceeding

        def _generator(body: dict) -> Generator[bytes, None, None]:
            # Iterate and yield images from response body
            for item in body["Names"]:
                yield self.get(item)

        # Pass the response body to the generator
        return _generator(response.json())

    def prune(
        self,
        all: Optional[bool] = False,  # pylint: disable=redefined-builtin
        external: Optional[bool] = False,
        filters: Optional[Mapping[str, Any]] = None,
    ) -> dict[Literal["ImagesDeleted", "SpaceReclaimed"], Any]:
        """Delete unused images.

        The Untagged keys will always be "".

        Args:
            all: Remove all images not in use by containers, not just dangling ones.
            external: Remove images even when they are used by external containers
            (e.g, by build containers).
            filters: Qualify Images to prune. Available filters:

                - dangling (bool): when true, only delete unused and untagged images.
                - label: (dict): filter by label.
                         Examples:
                         filters={"label": {"key": "value"}}
                         filters={"label!": {"key": "value"}}
                - until (str): Delete images older than this timestamp.

        Raises:
            APIError: when service returns an error
        """

        params = {
            "all": all,
            "external": external,
            "filters": api.prepare_filters(filters),
        }

        response = self.client.post("/images/prune", params=params)
        response.raise_for_status()

        deleted: builtins.list[dict[str, str]] = []
        error: builtins.list[str] = []
        reclaimed: int = 0
        # If the prune doesn't remove images, the API returns "null"
        # and it's interpreted as None (NoneType)
        # so the for loop throws "TypeError: 'NoneType' object is not iterable".
        # The below if condition fixes this issue.
        if response.json() is not None:
            for element in response.json():
                if "Err" in element and element["Err"] is not None:
                    error.append(element["Err"])
                else:
                    reclaimed += element["Size"]
                    deleted.append(
                        {
                            "Deleted": element["Id"],
                            "Untagged": "",
                        }
                    )
        if len(error) > 0:
            raise APIError(response.url, response=response, explanation="; ".join(error))

        return {
            "ImagesDeleted": deleted,
            "SpaceReclaimed": reclaimed,
        }

    def prune_builds(self) -> dict[Literal["CachesDeleted", "SpaceReclaimed"], Any]:
        """Delete builder cache.

        Method included to complete API, the operation always returns empty
            CacheDeleted and zero SpaceReclaimed.
        """
        return {"CachesDeleted": [], "SpaceReclaimed": 0}

    def push(
        self, repository: str, tag: Optional[str] = None, **kwargs
    ) -> Union[str, Iterator[Union[str, dict[str, Any]]]]:
        """Push Image or repository to the registry.

        Args:
            repository: Target repository for push
            tag: Tag to push, if given

        Keyword Args:
            auth_config (Mapping[str, str]: Override configured credentials. Must include
                username and password keys.
            decode (bool): return data from server as dict[str, Any]. Ignored unless stream=True.
            destination (str): alternate destination for image. (Podman only)
            stream (bool): return output as blocking generator. Default: False.
            tlsVerify (bool): Require TLS verification.
            format (str): Manifest type (oci, v2s1, or v2s2) to use when pushing an image.
                Default is manifest type of source, with fallbacks.

        Raises:
            APIError: when service returns an error
        """
        auth_config: Optional[dict[str, str]] = kwargs.get("auth_config")

        headers = {
            # A base64url-encoded auth configuration
            "X-Registry-Auth": encode_auth_header(auth_config) if auth_config else ""
        }

        params = {
            "destination": kwargs.get("destination"),
            "tlsVerify": kwargs.get("tlsVerify"),
            "format": kwargs.get("format"),
        }

        name = f'{repository}:{tag}' if tag else repository
        name = urllib.parse.quote_plus(name)
        response = self.client.post(f"/images/{name}/push", params=params, headers=headers)
        response.raise_for_status(not_found=ImageNotFound)

        tag_count = 0 if tag is None else 1
        body = [
            {
                "status": f"Pushing repository {repository} ({tag_count} tags)",
            },
            {
                "status": "Pushing",
                "progressDetail": {},
                "id": repository,
            },
        ]

        stream = kwargs.get("stream", False)
        decode = kwargs.get("decode", False)
        if stream:
            return self._push_helper(decode, body)

        with io.StringIO() as buffer:
            for entry in body:
                buffer.write(json.dumps(entry) + "\n")
            return buffer.getvalue()

    @staticmethod
    def _push_helper(
        decode: bool, body: builtins.list[dict[str, Any]]
    ) -> Iterator[Union[str, dict[str, Any]]]:
        """Helper needed to allow push() to return either a generator or a str."""
        for entry in body:
            if decode:
                yield entry
            else:
                yield json.dumps(entry)

    # pylint: disable=too-many-locals,too-many-branches
    def pull(
        self,
        repository: str,
        tag: Optional[str] = None,
        all_tags: bool = False,
        **kwargs,
    ) -> Union[Image, builtins.list[Image], Iterator[str]]:
        """Request Podman service to pull image(s) from repository.

        Args:
            repository: Repository to pull from
            tag: Image tag to pull. Default: "latest".
            all_tags: pull all image tags from repository.

        Keyword Args:
            auth_config (Mapping[str, str]) – Override the credentials that are found in the
                config for this request. auth_config should contain the username and password
                keys to be valid.
            compatMode (bool) – Return the same JSON payload as the Docker-compat endpoint.
                Default: True.
            decode (bool) – Decode the JSON data from the server into dicts.
                Only applies with ``stream=True``
            platform (str) – Platform in the format os[/arch[/variant]]
            progress_bar (bool) - Display a progress bar with the image pull progress (uses
                the compat endpoint). Default: False
            tls_verify (bool) - Require TLS verification. Default: True.
            stream (bool) - When True, the pull progress will be published as received.
                Default: False.

        Returns:
            When stream is True, return a generator publishing the service pull progress.
            If all_tags is True, return list of Image's rather than Image pulled.

        Raises:
            APIError: when service returns an error
        """
        if tag is None or len(tag) == 0:
            repository, parsed_tag = parse_repository(repository)
            if parsed_tag is not None:
                tag = parsed_tag
            else:
                tag = "latest"

        auth_config: Optional[dict[str, str]] = kwargs.get("auth_config")

        headers = {
            # A base64url-encoded auth configuration
            "X-Registry-Auth": encode_auth_header(auth_config) if auth_config else ""
        }

        params = {
            "reference": repository,
            "tlsVerify": kwargs.get("tls_verify", True),
            "compatMode": kwargs.get("compatMode", True),
        }

        if all_tags:
            params["allTags"] = True
        else:
            params["reference"] = f"{repository}:{tag}"

        # Check if "platform" in kwargs AND it has value.
        if "platform" in kwargs and kwargs["platform"]:
            tokens = kwargs.get("platform").split("/")
            if 1 < len(tokens) > 3:
                raise ValueError(f'\'{kwargs.get("platform")}\' is not a legal platform.')

            params["OS"] = tokens[0]
            if len(tokens) > 1:
                params["Arch"] = tokens[1]
            if len(tokens) > 2:
                params["Variant"] = tokens[2]

        stream = kwargs.get("stream", False)
        # if the user wants a progress bar, we need to use the compat endpoint
        # so set that to true as well as stream so we can parse that output for the
        # progress bar
        progress_bar = kwargs.get("progress_bar", False)
        if progress_bar:
            if Progress is None:
                raise ModuleNotFoundError('progress_bar requires \'rich.progress\' module')
            params["compatMode"] = True
            stream = True

        response = self.client.post("/images/pull", params=params, stream=stream, headers=headers)
        response.raise_for_status(not_found=ImageNotFound)

        if progress_bar:
            tasks = {}
            print("Pulling", params["reference"])
            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="default", finished_style="green"),
                TaskProgressColumn(),
                TimeRemainingColumn(),
            )
            with progress:
                for line in response.iter_lines():
                    decoded_line = json.loads(line.decode('utf-8'))
                    self.__show_progress_bar(decoded_line, progress, tasks)
            return None

        if stream:
            return self._stream_helper(response, decode=kwargs.get("decode"))

        for item in reversed(list(response.iter_lines())):
            obj = json.loads(item)
            if all_tags and "images" in obj:
                images: builtins.list[Image] = []
                for name in obj["images"]:
                    images.append(self.get(name))
                return images

            if "id" in obj:
                return self.get(obj["id"])
        return self.resource()

    def __show_progress_bar(self, line, progress, tasks):
        completed = False
        if line['status'] == 'Download complete':
            description = f'[green][Download complete  {line["id"]}]'
            completed = True
        elif line['status'] == 'Downloading':
            description = f'[bold][Downloading {line["id"]}]'
        else:
            # skip other statuses
            return

        task_id = line["id"]
        if task_id not in tasks.keys():
            if completed:
                # some layers are really small that they download immediately without showing
                # anything as Downloading in the stream.
                # For that case, show a completed progress bar
                tasks[task_id] = progress.add_task(description, total=100, completed=100)
            else:
                tasks[task_id] = progress.add_task(
                    description, total=line['progressDetail']['total']
                )
        else:
            if completed:
                # due to the stream, the Download complete output can happen before the Downloading
                # bar outputs the 100%. So when we detect that the download is in fact complete,
                # update the progress bar to show 100%
                progress.update(tasks[task_id], description=description, total=100, completed=100)
            else:
                progress.update(tasks[task_id], completed=line['progressDetail']['current'])

    def remove(
        self,
        image: Union[Image, str],
        force: Optional[bool] = None,
        noprune: bool = False,  # pylint: disable=unused-argument
    ) -> builtins.list[dict[Literal["Deleted", "Untagged", "Errors", "ExitCode"], Union[str, int]]]:
        """Delete image from Podman service.

        Args:
            image: Name or Id of Image to remove
            force: Delete Image even if in use
            noprune: Ignored.

        Raises:
            ImageNotFound: when image does not exist
            APIError: when service returns an error
        """
        if isinstance(image, Image):
            image = image.id

        response = self.client.delete(f"/images/{image}", params={"force": force})
        response.raise_for_status(not_found=ImageNotFound)

        body = response.json()
        results: builtins.list[dict[str, Union[int, str]]] = []
        for key in ("Deleted", "Untagged", "Errors"):
            if key in body:
                for element in body[key]:
                    results.append({key: element})
        results.append({"ExitCode": body["ExitCode"]})
        return results

    def search(self, term: str, **kwargs) -> builtins.list[dict[str, Any]]:
        """Search Images on registries.

        Args:
            term: Used to target Image results.

        Keyword Args:
            filters (Mapping[str, list[str]): Refine results of search. Available filters:

                - is-automated (bool): Image build is automated.
                - is-official (bool): Image build is owned by product provider.
                - stars (int): Image has at least this number of stars.

            noTrunc (bool): Do not truncate any result string. Default: True.
            limit (int): Maximum number of results.
            listTags (bool): list the available tags in the repository. Default: False

        Raises:
            APIError: when service returns an error
        """
        params = {
            "filters": api.prepare_filters(kwargs.get("filters")),
            "limit": kwargs.get("limit"),
            "noTrunc": True,
            "term": [term],
        }

        if "listTags" in kwargs:
            params["listTags"] = kwargs.get("listTags")

        response = self.client.get("/images/search", params=params)
        response.raise_for_status(not_found=ImageNotFound)
        return response.json()

    def scp(
        self,
        source: str,
        dest: Optional[str] = None,
        quiet: Optional[bool] = False,
    ) -> str:
        """Securely copy images between hosts.

        Args:
            source: source connection/image
            dest: destination connection/image
            quiet: do not print save/load output, only the image

        Returns:
            A string containing the loaded image

        Raises:
            APIError: when service returns an error
        """
        params = {"quiet": quiet}
        if dest is not None:
            params["destination"] = dest

        response = self.client.post(f"/images/scp/{source}", params=params)
        response.raise_for_status()
        return response.json()

    def _stream_helper(self, response, decode=False):
        """Generator for data coming from a chunked-encoded HTTP response."""

        if response.raw._fp.chunked:
            if decode:
                yield from json_stream(self._stream_helper(response, False))
            else:
                reader = response.raw
                while not reader.closed:
                    # this read call will block until we get a chunk
                    data = reader.read(1)
                    if not data:
                        break
                    if reader._fp.chunk_left:
                        data += reader.read(reader._fp.chunk_left)
                    yield data
        else:
            # Response isn't chunked, meaning we probably
            # encountered an error immediately
            yield self._result(response, json=decode)
