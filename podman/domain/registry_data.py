"""Module for tracking registry metadata."""

import logging
from typing import Any
from collections.abc import Mapping

from podman import api
from podman.domain.images import Image
from podman.domain.manager import PodmanResource
from podman.errors import InvalidArgument

logger = logging.getLogger("podman.images")


class RegistryData(PodmanResource):
    """Registry metadata about Image."""

    def __init__(self, image_name: str, *args, **kwargs) -> None:
        """Initialize RegistryData object.

        Args:
            image_name: Name of Image.

        Keyword Args:
            client (APIClient): Configured connection to a Podman service.
            collection (Manager): Manager of this category of resource,
                named `collection` for compatibility

        """
        super().__init__(*args, **kwargs)
        self.image_name = image_name

        self.attrs = kwargs.get("attrs")
        if self.attrs is None:
            self.attrs = self.manager.get(image_name).attrs

    def _get_version(self) -> dict[str, Any]:
        """Fetch version information from the Podman service.

        Returns an empty dict when no client is configured.

        Raises:
            APIError: when service reports an error
        """
        if self.podman_client is not None:
            return self.podman_client.version()
        if self.client is None:
            return {}

        response = self.client.get("/version")
        response.raise_for_status()
        return response.json()

    @property
    def id(self) -> str | None:  # pylint: disable=invalid-name
        """str: Returns the identifier / digest for the registry image."""
        if self.attrs.get("Id"):
            return self.attrs["Id"]

        descriptor = self.attrs.get("Descriptor")
        if isinstance(descriptor, dict) and descriptor.get("digest"):
            return descriptor["digest"]

        if self.attrs.get("digest"):
            return self.attrs["digest"]

        return self._resolve_manifest_digest()

    def _resolve_manifest_digest(self) -> str | None:
        """Resolve digest from manifests list."""
        manifests = self.attrs.get("manifests")
        if not isinstance(manifests, list) or not manifests:
            return None

        version = self._get_version()
        host_os = version.get("Os")
        host_arch = version.get("Arch")
        if host_os and host_arch:
            for manifest in manifests:
                if not isinstance(manifest, dict):
                    continue
                platform_info = manifest.get("platform") or {}
                if (
                    platform_info.get("os") == host_os
                    and platform_info.get("architecture") == host_arch
                ):
                    return manifest.get("digest")

        first_entry = manifests[0]
        if isinstance(first_entry, dict):
            return first_entry.get("digest")
        return None

    @property
    def short_id(self) -> str | None:
        """str: Returns truncated identifier."""
        if self.id is None:
            return None
        if self.id.startswith("sha256:"):
            return self.id[:17]
        return self.id[:10]

    @staticmethod
    def _match_platform_entry(
        platform_info: Mapping[str, Any], target_platform: Mapping[str, Any]
    ) -> bool:
        """Check if platform_info matches target_platform."""
        if platform_info.get("os") != target_platform.get("os"):
            return False
        if platform_info.get("architecture") != target_platform.get("architecture"):
            return False
        if "variant" in target_platform and target_platform["variant"] != platform_info.get(
            "variant"
        ):
            return False
        return True

    def pull(self, platform: str | None = None) -> Image:
        """Returns Image pulled by identifier.

        Args:
            platform: Platform for which to pull Image. Default: None (all platforms.)
        """
        repository, _ = api.parse_repository(self.image_name)
        pull_target = None
        if platform is not None and isinstance(self.attrs.get("manifests"), list):
            target_platform = self._parse_platform(platform)
            for manifest in self.attrs["manifests"]:
                if isinstance(manifest, dict) and isinstance(manifest.get("platform"), dict):
                    if self._match_platform_entry(manifest["platform"], target_platform):
                        pull_target = manifest.get("digest")
                        break

        if pull_target is None:
            pull_target = self.id
        if pull_target is None:
            _, pull_target = api.parse_repository(self.image_name)

        return self.manager.pull(repository, tag=pull_target, platform=platform)

    def _parse_platform(self, platform: str | Mapping[str, Any] | None) -> dict[str, str]:
        """Parse platform argument into standardized dict format."""
        invalid_platform = InvalidArgument(f"'{platform}' is not a valid platform descriptor.")

        if platform is None:
            platform = {}

        if isinstance(platform, Mapping):
            parsed = dict(platform)
            if not {"os", "architecture"} <= parsed.keys():
                version = self._get_version()
                parsed["os"] = parsed.get("os", version.get("Os"))
                parsed["architecture"] = parsed.get("architecture", version.get("Arch"))
            return parsed

        if isinstance(platform, str):
            elements = platform.split("/")
            if not (1 <= len(elements) <= 3) or not elements[0]:
                raise invalid_platform

            parsed = {"os": elements[0]}
            if len(elements) > 1:
                parsed["architecture"] = elements[1]
            if len(elements) > 2:
                parsed["variant"] = elements[2]
            return parsed

        raise invalid_platform

    def has_platform(self, platform: str | Mapping[str, Any]) -> bool:
        """Returns True if platform is available for Image.

        Args:
            platform: Name as os[/arch[/variant]] or Mapping[str,Any]

        Returns:
            True if platform is available

        Raises:
            InvalidArgument: when platform value is not valid
            APIError: when service reports an error
        """
        parsed_platform = self._parse_platform(platform)

        # Check in manifest list (from libpod /manifests/{name}/json)
        manifests = self.attrs.get("manifests")
        if isinstance(manifests, list):
            for manifest in manifests:
                if isinstance(manifest, dict) and isinstance(manifest.get("platform"), dict):
                    if self._match_platform_entry(manifest["platform"], parsed_platform):
                        return True
            return False

        # Check in Platforms list (from Docker /distribution/{name}/json)
        platforms = self.attrs.get("Platforms")
        if isinstance(platforms, list):
            for platform_entry in platforms:
                if isinstance(platform_entry, dict):
                    if self._match_platform_entry(platform_entry, parsed_platform):
                        return True
            return False

        # Fallback to local image attrs (Os, Architecture)
        if "Os" in self.attrs or "Architecture" in self.attrs:
            return parsed_platform.get("os") == self.attrs.get("Os") and parsed_platform.get(
                "architecture"
            ) == self.attrs.get("Architecture")

        return False

    def reload(self, **kwargs) -> None:
        """Refresh this object's registry data from the service."""
        latest = self.manager.get_registry_data(self.image_name, **kwargs)
        self.attrs = latest.attrs
