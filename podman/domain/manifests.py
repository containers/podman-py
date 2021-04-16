"""Model and Manager for Manifest resources."""
import logging
import urllib.parse
from contextlib import suppress
from typing import List, Optional, Type, Union

import requests

from podman import api
from podman.domain.images import Image
from podman.domain.manager import Manager, PodmanResource
from podman.errors import APIError, ImageNotFound, NotFound

logger = logging.getLogger("podman.manifests")


class Manifest(PodmanResource):
    """Details and configuration for a manifest managed by the Podman service."""

    @property
    def id(self) -> str:
        """Returns the identifier of the manifest."""
        with suppress(KeyError, TypeError):
            return self.attrs["manifests"][0]["digest"]
        return ""

    @property
    def name(self) -> str:
        """Returns the identifier of the manifest."""
        try:
            if len(self.names[0]) == 0:
                raise ValueError("Manifest attribute 'names' is empty.")
            return self.names[0]
        except (TypeError, IndexError) as e:
            raise ValueError("Manifest attribute 'names' is missing.") from e

    @property
    def quoted_name(self) -> str:
        return urllib.parse.quote_plus(self.name)

    @property
    def names(self) -> List[str]:
        """Returns the identifier of the manifest."""
        return self.attrs.get("names")

    @property
    def media_type(self) -> Optional[str]:
        """Returns the Media/MIME type for this manifest."""
        return self.attrs.get("mediaType")

    @property
    def version(self) -> int:
        """Returns the schema version type for this manifest."""
        return self.attrs.get("schemaVersion")

    def add(self, images: List[Union[Image, str]], **kwargs) -> None:
        """Add Image to manifest list.

        Args:
            images: List of Images to be added to manifest.

        Keyword Args:
            all (bool):
            annotation (Dict[str, str]):
            arch (str):
            features (List[str]):
            os (str):
            os_version (str):
            variant (str):

        Raises:
            ImageNotFound: When Image(s) could not be found
            APIError: When service reports an error
        """
        params = {
            "all": kwargs.get("all"),
            "annotation": kwargs.get("annotation"),
            "arch": kwargs.get("arch"),
            "features": kwargs.get("features"),
            "images": list(),
            "os": kwargs.get("os"),
            "os_version": kwargs.get("os_version"),
            "variant": kwargs.get("variant"),
        }
        for item in images:
            if isinstance(item, Image):
                item = item.attrs["RepoTags"][0]
            params["images"].append(item)

        data = api.prepare_body(params)
        response = self.client.post(f"/manifests/{self.quoted_name}/add", data=data)

        if response.status_code == requests.codes.okay:
            return self.reload()

        body = response.json()
        if response.status_code == requests.codes.not_found:
            raise ImageNotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def push(
        self, destination: str, all: Optional[bool] = None  # pylint: disable=redefined-builtin
    ) -> None:
        """Push a manifest list or image index to a registry.

        Args:
            destination: Target for push.
            all: Push all images.

        Raises:
            NotFound: When the Manifest could not be found
            APIError: When service reports an error
        """
        params = {
            "all": all,
            "destination": destination,
        }
        response = self.client.post(f"/manifests/{self.quoted_name}/push", params=params)

        if response.status_code == requests.codes.okay:
            return

        body = response.json()
        if response.status_code == requests.codes.not_found:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def remove(self, digest: str) -> None:
        """Remove Image digest from manifest list.

        Args:
            digest: Image digest to be removed. Should a full Image reference be provided
                the digest will be parsed out.

        Raises:
            ImageNotFound: When the Image could not be found
            APIError: When service reports an error
        """
        if "@" in digest:
            digest = digest.split("@", maxsplit=2)[1]

        response = self.client.delete(f"/manifests/{self.quoted_name}", params={"digest": digest})

        if response.status_code == requests.codes.okay:
            return self.reload()

        body = response.json()
        if response.status_code == requests.codes.not_found:
            raise ImageNotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def reload(self) -> None:
        """Refresh this object's data from the service."""
        latest = self.manager.get(self.name)
        self.attrs = latest.attrs


class ManifestsManager(Manager):
    """Specialized Manager for Manifest resources."""

    @property
    def resource(self) -> Type[PodmanResource]:
        return Manifest

    def exists(self, key: str) -> bool:
        key = urllib.parse.quote_plus(key)
        response = self.client.get(f"/manifests/{key}/exists")
        return response.status_code == requests.codes.no_content

    def create(
        self,
        names: List[str],
        images: Optional[List[Union[Image, str]]] = None,
        all: Optional[bool] = None,  # pylint: disable=redefined-builtin
    ) -> Manifest:
        """Create a Manifest.

        Args:
            names: Identifiers to be added to the manifest. There must be at least one.
            images: Images or Image identifiers to be included in the manifest.
            all: When True, add all contents from images given.

        Raises:
            ValueError: When no names are provided.
            NotFoundImage: When a given image does not exist.
        """
        if names is None or len(names) == 0:
            raise ValueError("At least one manifest name is required.")

        params = {"name": names}
        if images is not None:
            params["image"] = list()
            for item in images:
                if isinstance(item, Image):
                    item = item.attrs["RepoTags"][0]
                params["image"].append(item)

        if all is not None:
            params["all"] = all

        response = self.client.post("/manifests/create", params=params)
        body = response.json()

        if response.status_code == requests.codes.okay:
            manifest = self.get(body["Id"])
            manifest.attrs["names"] = names
            return manifest

        if response.status_code == requests.codes.not_found:
            raise ImageNotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def get(self, key: str) -> Manifest:
        """Returns the manifest by name.

        Args:
            key: Manifest name for which to search

        Raises:
            NotFound: When manifest could not be found.
            APIError: When service reports an error.

        Notes:
            To have Manifest more conform with other PodmanResource's, we use the key that
                retrieved the Manifest be its name.
        """
        quoted_key = urllib.parse.quote_plus(key)
        response = self.client.get(f"/manifests/{quoted_key}/json")
        body = response.json()

        if response.status_code == requests.codes.okay:
            body["names"] = [key]
            return self.prepare_model(attrs=body)

        if response.status_code == requests.codes.not_found:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def list(self, **kwargs) -> List[Manifest]:
        """Not Implemented."""

        raise NotImplementedError("Podman service currently does not support listing manifests.")
