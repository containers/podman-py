"""Model and Manager for Image resources."""
import logging
from typing import Any, Dict, Iterator, List, Optional, Union

from podman import api
from podman.domain.manager import PodmanResource
from podman.errors import ImageNotFound

logger = logging.getLogger("podman.images")


class Image(PodmanResource):
    """Details and configuration for an Image managed by the Podman service."""

    def __repr__(self) -> str:
        return f"""<{self.__class__.__name__}: '{"', '".join(self.tags)}'>"""

    @property
    def labels(self):
        """dict[str, str]: Return labels associated with Image."""
        image_labels = self.attrs.get("Labels")
        if image_labels is None or len(image_labels) == 0:
            return {}

        return image_labels

    @property
    def tags(self):
        """list[str]: Return tags from Image."""
        repo_tags = self.attrs.get("RepoTags")
        if repo_tags is None or len(repo_tags) == 0:
            return []

        return [tag for tag in repo_tags if tag != "<none>:<none>"]

    def history(self) -> List[Dict[str, Any]]:
        """Returns history of the Image.

        Raises:
            APIError: when service returns an error
        """

        response = self.client.get(f"/images/{self.id}/history")
        response.raise_for_status(not_found=ImageNotFound)
        return response.json()

    def remove(
        self, **kwargs
    ) -> List[Dict[api.Literal["Deleted", "Untagged", "Errors", "ExitCode"], Union[str, int]]]:
        """Delete image from Podman service.

        Podman only

        Keyword Args:
            force: Delete Image even if in use
            noprune: Ignored.

        Returns:
            Report on which images were deleted and untagged, including any reported errors.

        Raises:
            ImageNotFound: when image does not exist
            APIError: when service returns an error
        """
        return self.manager.remove(self.id, **kwargs)

    def save(
        self,
        chunk_size: Optional[int] = api.DEFAULT_CHUNK_SIZE,
        named: Union[str, bool] = False,  # pylint: disable=unused-argument
    ) -> Iterator[bytes]:
        """Returns Image as tarball.

        Format is set to docker-archive, this allows load() to import this tarball.

        Args:
            chunk_size: If None, data will be streamed in received buffer size.
                If not None, data will be returned in sized buffers. Default: 2MB
            named: Ignored.

        Raises:
            APIError: when service returns an error
        """
        response = self.client.get(
            f"/images/{self.id}/get", params={"format": ["docker-archive"]}, stream=True
        )
        response.raise_for_status(not_found=ImageNotFound)
        return response.iter_content(chunk_size=chunk_size)

    def tag(
        self,
        repository: str,
        tag: Optional[str],
        force: bool = False,  # pylint: disable=unused-argument
    ) -> bool:
        """Tag Image into repository.

        Args:
            repository: The repository for tagging Image.
            tag: optional tag name.
            force: Ignore client errors

        Returns:
            True, when operational succeeds.

        Raises:
            ImageNotFound: when service cannot find image
            APIError: when service returns an error
        """
        params = {"repo": repository, "tag": tag}
        response = self.client.post(f"/images/{self.id}/tag", params=params)
        if response.ok:
            return True

        if force and response.status_code <= 500:
            return False

        response.raise_for_status(not_found=ImageNotFound)
        return False
