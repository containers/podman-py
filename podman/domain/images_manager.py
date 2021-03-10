"""PodmanResource manager subclassed for Images."""
import io
import json
import tarfile
import tempfile
import urllib.parse
from typing import IO, Any, ClassVar, Dict, Iterable, Iterator, List, Mapping, Optional, Type, Union

from podman import api
from podman.domain.image_build import BuildMixin
from podman.domain.images import Image
from podman.domain.manager import Manager
from podman.domain.registry_data import RegistryData
from podman.errors.exceptions import APIError, ImageNotFound


class ImagesManager(Manager, BuildMixin):
    """Specialized Manager for Image resources.

    Attributes:
        resource: Image subclass of PodmanResource, factory method will create these.
    """

    resource: ClassVar[Type[Image]] = Image

    def list(self, *args, **kwargs) -> List[Image]:
        """Report on images.

        Keyword Args:
            name (str) – Only show images belonging to the repository name
            all (bool) – Show intermediate image layers. By default, these are filtered out.
            filters (Mapping[str, Union[str, List[str]]) – Filters to be used on the image list.
                Available filters:
                - dangling (bool)
                - label (Union[str, List[str]]): format either "key", "key=value"

        Raises:
            APIError: when service returns an error.
        """
        params = {}
        if "all" in kwargs:
            params["all"] = kwargs.pop("all")
        if "name" in kwargs:
            params["name"] = kwargs.pop("name")
        if "filters" in kwargs:
            params["filters"] = api.format_filters(kwargs.pop("filters"))

        response = self.client.get("/images/json", params=params)
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        images: List[Image] = []
        for element in body:
            images.append(self.prepare_model(element))
        return images

    # pylint is flagging 'name' here vs. 'key' parameter in super.get()
    def get(self, name: str) -> Image:  # pylint: disable=arguments-differ
        """Returns an image by name or id.

        Args:
            name: Image id or name for which to search

        Raises:
            ImageNotFound: when image does not exist.
            APIError: when service returns an error.
        """
        name = urllib.parse.quote_plus(name)
        response = self.client.get(f"/images/{name}/json")
        body = response.json()

        if response.status_code == 200:
            return self.prepare_model(body)

        if response.status_code == 404:
            raise ImageNotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def get_registry_data(self, name: str, auth_config=Mapping[str, str]) -> RegistryData:
        """Returns registry data for an image.

        Args:
            name: Image name
            auth_config: Override configured credentials. Keys username and password are required.

        Raises:
            APIError: when service returns an error.
        """
        # FIXME populate attrs using auth_config
        _ = auth_config
        image = self.get(name)
        return RegistryData(
            image_name=name,
            attrs=image.attrs,
            client=self.client,
            collection=self,
        )

    def load(self, data: bytes) -> Iterable[Image]:
        """Restore an image previously saved.

        Args:
            data: Image to be loaded in tarball format.

        Yields:

        Raises:
            APIError: when service returns an error.
        """
        response = self.client.post(
            "/images/load", data=data, headers={"Content-type": "application/x-www-form-urlencoded"}
        )
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        # Dict[Literal["Names"], List[str]]]
        for i in body["Names"]:
            yield self.get(i)

    def prune(self, filters: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """Delete unused images.

        Args:
            filters: Qualify Images to prune. Available filters:
                - dangling (bool): when true, only delete unused and untagged images.
                - until (str): Delete images older than this timestamp.

        Raises:
            APIError: when service returns an error.

        Note:
            The Untagged key will always be "".
        """
        params = {}
        if filters is not None:
            params["filters"] = api.format_filters(filters)

        response = self.client.post("/images/prune", params=params)
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

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
                        "Deleted":  element["Id"],
                        "Untagged": "",
                    }
                )
        if len(error) > 0:
            raise APIError(response.url, response=response, explanation="; ".join(error))

        # body -> Dict[Literal["ImagesDeleted", "SpaceReclaimed"],
        #   List[Dict[Literal["Deleted", "Untagged"], str]
        return {
            "ImagesDeleted":  deleted,
            "SpaceReclaimed": reclaimed,
        }

    def prune_builds(self) -> Dict[str, Any]:
        """Delete builder cache.

        Returns:
            (Dict[str, Any]): Information about the operation's result.
                The ``SpaceReclaimed`` key indicates the amount of bytes of disk space reclaimed.

        Note:
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
            APIError: when service returns an error.
        """
        # TODO set X-Registry-Auth
        headers = {
            # A base64url-encoded auth configuration
            "X-Registry-Auth": ""
        }

        params = {}
        if "destination" in kwargs:
            params["destination"] = kwargs.pop("destination")
        if "tlsVerify" in kwargs:
            params["tlsVery"] = kwargs.pop("tlsVerify")

        name = urllib.parse.quote_plus(repository)
        response = self.client.post(f"/images/{name}/push", params=params, headers=headers)

        if response.status_code != 200:
            body = response.json()
            raise APIError(body["cause"], response=response, explanation=body["message"])

        tag_count = 0 if tag is None else 1
        body = [
            {
                "status": f"Pushing repository {repository} ({tag_count} tags)",
            },
            {
                "status":         "Pushing",
                "progressDetail": {},
                "id":             repository,
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
    ) -> Union[Image, List[Image]]:
        """Request Podman service to pull image(s) from repository.

        Args:
            repository: repository to pull from
            tag: image tag to pull, if None all tags in repository are pulled.
            all_tags: pull all image tags from repository.

        Keyword Args:
            auth_config (Mapping[str, str]) – Override the credentials that are found in the
                config for this request. auth_config should contain the username and password
                keys to be valid.
            platform (str) – Platform in the format os[/arch[/variant]]
            all_tags (bool) – Pull all image tags
            tls_verify (bool) - Require TLS verification. Default: True.

        Returns:
            If all_tags is True, return list of Image's rather than Image pulled.

        Raises:
            APIError: when service returns an error.
        """
        if tag is None or len(tag) == 0:
            tag = "latest"

        params = {"reference": repository}
        if all_tags:
            params["allTags"] = True
        else:
            params["reference"] = f"{repository}:{tag}"

        if "platform" in kwargs:
            platform = kwargs.pop("platform")
            ospm, arch, variant = platform.split("/")

            if ospm is not None:
                params["OS"] = ospm
            if arch is not None:
                params["Arch"] = arch
            if variant is not None:
                params["Variant"] = variant

        if "auth_config" in kwargs:
            username = kwargs["auth_config"].get(["username"])
            password = kwargs["auth_config"].get(["password"])
            if username is None or password is None:
                raise ValueError("'auth_config' requires keys 'username' and 'password'")
            params["credentials"] = f'{username}:{password}'

        if "tls_verify" in kwargs:
            params["tlsVerify"] = kwargs.pop("tls_verify")

        response = self.client.post("/images/pull", params=params)
        body = response.json()

        if response.status_code != 200:
            raise APIError(response.url, response=response, explanation=body["error"])

        if not all_tags:
            return self.get(body["images"][0])

        images: List[Image] = []
        for name in body["images"]:
            images.append(self.get(name))
        return images

    def remove(
            self, image: str, force: bool = False, noprune: bool = False
    ) -> List[Dict[str, Union[str, int]]]:
        """Delete image from Podman service.

        Args:
            image: Name or Id of Image to remove
            force: delete Image if in use
            noprune: do not delete untagged parents. Ignored.

        Returns:
            List[Dict[Literal["Deleted", "Untagged", "Errors", "ExitCode"], Union[str, int]]]

        Raises:
            APIError: when service returns an error.

        Notes:
            The dictionaries with keys Errors and ExitCode are added.
        """
        _ = noprune

        params = {}
        if force:
            params["force"] = str(bool(force))

        response = self.client.delete(f"/images/{image}", params=params)
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        # Dict[Literal["Deleted", "Untagged", "Errors", "ExitCode"], Union[int, List[str]]]
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
            "term":    [term],
            "noTrunc": True,
        }
        if "limit" in kwargs:
            params["limit"] = kwargs.pop("limit")
        if "filters" in kwargs:
            params["filters"] = api.format_filters(kwargs.pop("filters"))

        response = self.client.get("/images/search", params=params)
        body = response.json()

        if response.status_code == 200:
            return body
        raise APIError(body["cause"], response=response, explanation=body["message"])

    @staticmethod
    def _build_context(dockerfile: Union[io.BytesIO, str]) -> IO:
        file = tempfile.NamedTemporaryFile()
        with tarfile.open(mode="w", fileobj=file) as tarball:
            if isinstance(dockerfile, io.BytesIO):
                info = tarfile.TarInfo("Dockerfile")
                info.size = len(dockerfile.getvalue())
                dockerfile.seek(0)
            else:
                info = tarball.gettarinfo(fileobj=dockerfile, arcname='Dockerfile')
            tarball.add(info, dockerfile)

        file.seek(0)
        return file
