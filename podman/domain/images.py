"""Model and Manager for Image resources."""
from typing import Any, Dict, Iterator, List, Optional, Union

from podman.domain.manager import PodmanResource
from podman.errors.exceptions import APIError, ImageNotFound


class Image(PodmanResource):
    """Details and configuration for an Image managed by the Podman service.

    Attributes:
        labels: Image labels
        tags: Image tags
    """

    def __repr__(self) -> str:
        return "<%s: '%s'>" % (self.__class__.__name__, "', '".join(self.tags))

    @property
    def labels(self) -> Dict[str, str]:
        """Returns labels associated with Image."""
        return self.attrs.get("Labels", {})

    @property
    def tags(self) -> List[str]:
        """Returns tags from Image."""
        if "RepoTags" in self.attrs:
            return [tag for tag in self.attrs["RepoTags"] if tag != "<none>:<none>"]
        return []

    def history(self) -> List[Dict[str, Any]]:
        """Returns history of the Image.

        Raises:
            APIError: when service returns an error.
        """

        response = self.client.get(f"/images/{self.id}/history")
        body = response.json()

        if response.status_code == 200:
            return body

        if response.status_code == 404:
            raise ImageNotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def save(
        self, chunk_size: Optional[int] = 2097152, named: Union[str, bool] = False
    ) -> Iterator[bytes]:
        """Returns Image as tarball.

        Args:
            chunk_size: If None, data will be streamed in received buffer size.
                If not None, data will be returned in sized buffers. Default: 2MB
            named: When False, tarball will not retain repository and tag information.
                When True, first tag is used to identify the Image.
                when str, value is used as tag to identify the Image.
                Always ignored.

        Raises:
            APIError: when service returns an error.
        """
        _ = named

        response = self.client.get(f"/images/{self.id}/get", stream=True)

        if response.status_code == 200:
            return response.iter_content(chunk_size=chunk_size)

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def tag(self, repository: str, tag: Optional[str], force: bool = False) -> bool:
        """Tag Image into repository.

        Args:
            repository: The repository for tagging Image.
            tag: optional tag name.
            force: force tagging. Always ignored.

        Returns:
            True, when operational succeeds.

        Raises:
            ImageNotFound: when service cannot find image.
            APIError: when service returns an error.
        """
        _ = force

        params = {"repo": repository}
        if tag is not None:
            params["tag"] = tag

        response = self.client.post(f"/images/{self.id}/tag", params=params)

        if response.status_code == 201:
            return True

        error = response.json()
        if response.status_code == 404:
            raise ImageNotFound(error["cause"], response=response, explanation=error["message"])
        raise APIError(error["cause"], response=response, explanation=error["message"])
