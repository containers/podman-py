"""Model and Manager for Manifest resources."""

import logging
import urllib.parse
from contextlib import suppress
from typing import Any, Optional, Union

from podman import api
from podman.domain.images import Image
from podman.domain.manager import Manager, PodmanResource
from podman.errors import ImageNotFound

logger = logging.getLogger("podman.manifests")


class Manifest(PodmanResource):
    """Details and configuration for a manifest managed by the Podman service."""

    @property
    def id(self):
        """str: Returns the identifier of the manifest list."""
        with suppress(KeyError, TypeError, IndexError):
            digest = self.attrs["manifests"][0]["digest"]
            if digest.startswith("sha256:"):
                return digest[7:]
            return digest
        return self.name

    @property
    def name(self):
        """str: Returns the human-formatted identifier of the manifest list."""
        return self.attrs.get("names")

    @property
    def quoted_name(self):
        """str: name quoted as path parameter."""
        return urllib.parse.quote_plus(self.name)

    @property
    def names(self):
        """list[str]: Returns the identifier of the manifest."""
        return self.name

    @property
    def media_type(self):
        """Optional[str]: Returns the Media/MIME type for this manifest."""
        return self.attrs.get("mediaType")

    @property
    def version(self):
        """int: Returns the schema version type for this manifest."""
        return self.attrs.get("schemaVersion")

    def add(self, images: list[Union[Image, str]], **kwargs) -> None:
        """Add Image to manifest list.

        Args:
            images: List of Images to be added to manifest.

        Keyword Args:
            all (bool):
            annotation (dict[str, str]):
            arch (str):
            features (list[str]):
            os (str):
            os_version (str):
            variant (str):

        Raises:
            ImageNotFound: when Image(s) could not be found
            APIError: when service reports an error
        """
        data = {
            "all": kwargs.get("all"),
            "annotation": kwargs.get("annotation"),
            "arch": kwargs.get("arch"),
            "features": kwargs.get("features"),
            "images": [],
            "os": kwargs.get("os"),
            "os_version": kwargs.get("os_version"),
            "variant": kwargs.get("variant"),
            "operation": "update",
        }
        for item in images:
            # avoid redefinition of the loop variable, then ensure it's an image
            img_item = item
            if isinstance(img_item, Image):
                img_item = img_item.attrs["RepoTags"][0]
            data["images"].append(img_item)

        data = api.prepare_body(data)
        response = self.client.put(f"/manifests/{self.quoted_name}", data=data)
        response.raise_for_status(not_found=ImageNotFound)
        return self.reload()

    def push(
        self,
        destination: str,
        all: Optional[bool] = None,  # pylint: disable=redefined-builtin
        **kwargs,
    ) -> None:
        """Push a manifest list or image index to a registry.

        Args:
            destination: Target for push.
            all: Push all images.

        Keyword Args:
            auth_config (Mapping[str, str]: Override configured credentials. Must include
                username and password keys.

        Raises:
            NotFound: when the Manifest could not be found
            APIError: when service reports an error
        """
        auth_config: Optional[dict[str, str]] = kwargs.get("auth_config")

        headers = {
            # A base64url-encoded auth configuration
            "X-Registry-Auth": api.encode_auth_header(auth_config) if auth_config else ""
        }

        params = {
            "all": all,
            "destination": destination,
        }

        destination_quoted = urllib.parse.quote_plus(destination)
        response = self.client.post(
            f"/manifests/{self.quoted_name}/registry/{destination_quoted}",
            params=params,
            headers=headers,
        )
        response.raise_for_status()

    def remove(self, digest: str) -> None:
        """Remove Image digest from manifest list.

        Args:
            digest: Image digest to be removed. Should a full Image reference be provided,
                the digest will be parsed out.

        Raises:
            ImageNotFound: when the Image could not be found
            APIError: when service reports an error
        """
        if "@" in digest:
            digest = digest.split("@", maxsplit=2)[1]

        data = {"operation": "remove", "images": [digest]}
        data = api.prepare_body(data)

        response = self.client.put(f"/manifests/{self.quoted_name}", data=data)
        response.raise_for_status(not_found=ImageNotFound)
        return self.reload()

    def reload(self) -> None:
        """Refresh this object's data from the service."""
        latest = self.manager.get(self.name)
        self.attrs = latest.attrs


class ManifestsManager(Manager):
    """Specialized Manager for Manifest resources."""

    @property
    def resource(self):
        """Type[Manifest]: prepare_model() will create Manifest classes."""
        return Manifest

    def create(
        self,
        name: str,
        images: Optional[list[Union[Image, str]]] = None,
        all: Optional[bool] = None,  # pylint: disable=redefined-builtin
    ) -> Manifest:
        """Create a Manifest.

        Args:
            name: Name of manifest list.
            images: Images or Image identifiers to be included in the manifest.
            all: When True, add all contents from images given.

        Raises:
            ValueError: when no names are provided
            NotFoundImage: when a given image does not exist
        """
        params: dict[str, Any] = {}
        if images is not None:
            params["images"] = []
            for item in images:
                # avoid redefinition of the loop variable, then ensure it's an image
                img_item = item
                if isinstance(img_item, Image):
                    img_item = img_item.attrs["RepoTags"][0]
                params["images"].append(img_item)

        if all is not None:
            params["all"] = all

        name_quoted = urllib.parse.quote_plus(name)
        response = self.client.post(f"/manifests/{name_quoted}", params=params)
        response.raise_for_status(not_found=ImageNotFound)

        body = response.json()
        manifest = self.get(body["Id"])
        manifest.attrs["names"] = name

        if manifest.attrs["manifests"] is None:
            manifest.attrs["manifests"] = []
        return manifest

    def exists(self, key: str) -> bool:
        key = urllib.parse.quote_plus(key)
        response = self.client.get(f"/manifests/{key}/exists")
        return response.ok

    def get(self, key: str) -> Manifest:
        """Returns the manifest by name.

        To have Manifest conform with other PodmanResource's, we use the key that
        retrieved the Manifest be its name.

        Args:
            key: Manifest name for which to search

        Raises:
            NotFound: when manifest could not be found
            APIError: when service reports an error
        """
        quoted_key = urllib.parse.quote_plus(key)
        response = self.client.get(f"/manifests/{quoted_key}/json")
        response.raise_for_status()

        body = response.json()
        if "names" not in body:
            body["names"] = key
        return self.prepare_model(attrs=body)

    def list(self, **kwargs) -> list[Manifest]:
        """Not Implemented."""

        raise NotImplementedError("Podman service currently does not support listing manifests.")

    def remove(self, name: Union[Manifest, str]) -> dict[str, Any]:
        """Delete the manifest list from the Podman service."""
        if isinstance(name, Manifest):
            name = name.name

        response = self.client.delete(f"/manifests/{name}")
        response.raise_for_status(not_found=ImageNotFound)

        body = response.json()
        body["ExitCode"] = response.status_code
        return body
