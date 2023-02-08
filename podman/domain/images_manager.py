"""PodmanResource manager subclassed for Images."""
import io
import json
import logging
import urllib.parse
from typing import Any, Dict, Generator, Iterator, List, Mapping, Optional, Union

import requests

from podman import api
from podman.api import Literal
from podman.api.http_utils import encode_auth_header
from podman.domain.images import Image
from podman.domain.images_build import BuildMixin
from podman.domain.manager import Manager
from podman.domain.registry_data import RegistryData
from podman.errors import APIError, ImageNotFound

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

    def list(self, **kwargs) -> List[Image]:
        """Report on images.

        Keyword Args:
            name (str) – Only show images belonging to the repository name
            all (bool) – Show intermediate image layers. By default, these are filtered out.
            filters (Mapping[str, Union[str, List[str]]) – Filters to be used on the image list.
                Available filters:

                - dangling (bool)
                - label (Union[str, List[str]]): format either "key" or "key=value"

        Raises:
            APIError: when service returns an error
        """
        params = {
            "all": kwargs.get("all"),
            "name": kwargs.get("name"),
            "filters": api.prepare_filters(kwargs.get("filters")),
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

    def load(self, data: bytes) -> Generator[Image, None, None]:
        """Restore an image previously saved.

        Args:
            data: Image to be loaded in tarball format.

        Raises:
            APIError: when service returns an error
        """
        # TODO fix podman swagger cannot use this header!
        # headers = {"Content-type": "application/x-www-form-urlencoded"}

        response = self.client.post(
            "/images/load", data=data, headers={"Content-type": "application/x-tar"}
        )
        response.raise_for_status()

        body = response.json()
        for item in body["Names"]:
            yield self.get(item)

    def prune(
        self, filters: Optional[Mapping[str, Any]] = None
    ) -> Dict[Literal["ImagesDeleted", "SpaceReclaimed"], Any]:
        """Delete unused images.

        The Untagged keys will always be "".

        Args:
            filters: Qualify Images to prune. Available filters:

                - dangling (bool): when true, only delete unused and untagged images.
                - until (str): Delete images older than this timestamp.

        Raises:
            APIError: when service returns an error
        """
        response = self.client.post(
            "/images/prune", params={"filters": api.prepare_filters(filters)}
        )
        response.raise_for_status()

        deleted: List[Dict[str, str]] = []
        error: List[str] = []
        reclaimed: int = 0
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

    def prune_builds(self) -> Dict[Literal["CachesDeleted", "SpaceReclaimed"], Any]:
        """Delete builder cache.

        Method included to complete API, the operation always returns empty
            CacheDeleted and zero SpaceReclaimed.
        """
        return {"CachesDeleted": [], "SpaceReclaimed": 0}

    def push(
        self, repository: str, tag: Optional[str] = None, **kwargs
    ) -> Union[str, Iterator[Union[str, Dict[str, Any]]]]:
        """Push Image or repository to the registry.

        Args:
            repository: Target repository for push
            tag: Tag to push, if given

        Keyword Args:
            auth_config (Mapping[str, str]: Override configured credentials. Must include
                username and password keys.
            decode (bool): return data from server as Dict[str, Any]. Ignored unless stream=True.
            destination (str): alternate destination for image. (Podman only)
            stream (bool): return output as blocking generator. Default: False.
            tlsVerify (bool): Require TLS verification.

        Raises:
            APIError: when service returns an error
        """
        auth_config: Optional[Dict[str, str]] = kwargs.get("auth_config")

        headers = {
            # A base64url-encoded auth configuration
            "X-Registry-Auth": encode_auth_header(auth_config) if auth_config else ""
        }

        params = {
            "destination": kwargs.get("destination"),
            "tlsVerify": kwargs.get("tlsVerify"),
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
        decode: bool, body: List[Dict[str, Any]]
    ) -> Iterator[Union[str, Dict[str, Any]]]:
        """Helper needed to allow push() to return either a generator or a str."""
        for entry in body:
            if decode:
                yield entry
            else:
                yield json.dumps(entry)

    # pylint: disable=too-many-locals,too-many-branches
    def pull(
        self, repository: str, tag: Optional[str] = None, all_tags: bool = False, **kwargs
    ) -> Union[Image, List[Image], Iterator[str]]:
        """Request Podman service to pull image(s) from repository.

        Args:
            repository: Repository to pull from
            tag: Image tag to pull. Default: "latest".
            all_tags: pull all image tags from repository.

        Keyword Args:
            auth_config (Mapping[str, str]) – Override the credentials that are found in the
                config for this request. auth_config should contain the username and password
                keys to be valid.
            platform (str) – Platform in the format os[/arch[/variant]]
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
            tokens = repository.split(":")
            if len(tokens) == 2:
                repository = tokens[0]
                tag = tokens[1]
            else:
                tag = "latest"

        auth_config: Optional[Dict[str, str]] = kwargs.get("auth_config")

        headers = {
            # A base64url-encoded auth configuration
            "X-Registry-Auth": encode_auth_header(auth_config) if auth_config else ""
        }

        params = {
            "reference": repository,
            "tlsVerify": kwargs.get("tls_verify"),
        }

        if all_tags:
            params["allTags"] = True
        else:
            params["reference"] = f"{repository}:{tag}"

        if "platform" in kwargs:
            tokens = kwargs.get("platform").split("/")
            if 1 < len(tokens) > 3:
                raise ValueError(f'\'{kwargs.get("platform")}\' is not a legal platform.')

            params["OS"] = tokens[0]
            if len(tokens) > 1:
                params["Arch"] = tokens[1]
            if len(tokens) > 2:
                params["Variant"] = tokens[2]

        stream = kwargs.get("stream", False)
        response = self.client.post("/images/pull", params=params, stream=stream, headers=headers)
        response.raise_for_status(not_found=ImageNotFound)

        if stream:
            return response.iter_lines()

        for item in response.iter_lines():
            obj = json.loads(item)
            if all_tags and "images" in obj:
                images: List[Image] = []
                for name in obj["images"]:
                    images.append(self.get(name))
                return images

            if "id" in obj:
                return self.get(obj["id"])
        return self.resource()

    def remove(
        self,
        image: Union[Image, str],
        force: Optional[bool] = None,
        noprune: bool = False,  # pylint: disable=unused-argument
    ) -> List[Dict[Literal["Deleted", "Untagged", "Errors", "ExitCode"], Union[str, int]]]:
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
        results: List[Dict[str, Union[int, str]]] = []
        for key in ("Deleted", "Untagged", "Errors"):
            if key in body:
                for element in body[key]:
                    results.append({key: element})
        results.append({"ExitCode": body["ExitCode"]})
        return results

    def search(self, term: str, **kwargs) -> List[Dict[str, Any]]:
        """Search Images on registries.

        Args:
            term: Used to target Image results.

        Keyword Args:
            filters (Mapping[str, List[str]): Refine results of search. Available filters:

                - is-automated (bool): Image build is automated.
                - is-official (bool): Image build is owned by product provider.
                - stars (int): Image has at least this number of stars.

            noTrunc (bool): Do not truncate any result string. Default: True.
            limit (int): Maximum number of results.

        Raises:
            APIError: when service returns an error
        """
        params = {
            "filters": api.prepare_filters(kwargs.get("filters")),
            "limit": kwargs.get("limit"),
            "noTrunc": True,
            "term": [term],
        }

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
        params = {}
        if dest is not None and quiet:
            params = {"destination": dest, "quiet": quiet}
        elif quiet:
            params = {"quiet": quiet}
        response = self.client.post(f"/images/scp/{source}", params=params)
        response.raise_for_status()
        return response.json()
