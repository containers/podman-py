"""Mixin for Image build support."""
import itertools
import json
import re
from typing import Iterator, Tuple

from podman import api
from podman.domain.images import Image
from podman.errors.exceptions import APIError, BuildError, PodmanError


class BuildMixin:
    """Class providing build operation for ImageManager."""

    # pylint: disable=too-many-locals,too-many-branches,too-few-public-methods
    def build(self, **kwargs) -> Tuple[Image, Iterator[bytes]]:
        """Returns built image.

        Keyword Args:
            path (str) – Path to the directory containing the Dockerfile
            fileobj – A file object to use as the Dockerfile. (Or an IO object)
            tag (str) – A tag to add to the final image
            quiet (bool) – Whether to return the status
            nocache (bool) – Don’t use the cache when set to True
            rm (bool) – Remove intermediate containers. Default True
            timeout (int) – HTTP timeout
            custom_context (bool) – Optional if using fileobj (ignored)
            encoding (str) – The encoding for a stream. Set to gzip for compressing (ignored)
            pull (bool) – Downloads any updates to the FROM image in Dockerfile
            forcerm (bool) – Always remove intermediate containers, even after unsuccessful builds
            dockerfile (str) – path within the build context to the Dockerfile
            buildargs (Mapping[str,str) – A dictionary of build arguments
            container_limits (Dict[str, Union[int,str]]) –
                A dictionary of limits applied to each container created by the build process.
                    Valid keys:

                    - memory (int): set memory limit for build
                    - memswap (int): Total memory (memory + swap), -1 to disable swap
                    - cpushares (int): CPU shares (relative weight)
                    - cpusetcpus (str): CPUs in which to allow execution, For example, "0-3", "0,1"
                    - cpuperiod (int): CPU CFS (Completely Fair Scheduler) period (Podman only)
                    - cpuquota (int): CPU CFS (Completely Fair Scheduler) quota (Podman only)
            shmsize (int) – Size of /dev/shm in bytes. The size must be greater than 0.
                If omitted the system uses 64MB
            labels (Mapping[str,str]) – A dictionary of labels to set on the image
            cache_from (List[str]) – A list of image's identifier used for build cache resolution
            target (str) – Name of the build-stage to build in a multi-stage Dockerfile
            network_mode (str) – networking mode for the run commands during build
            squash (bool) – Squash the resulting images layers into a single layer.
            extra_hosts (Dict[str,str]) – Extra hosts to add to /etc/hosts in building
                containers, as a mapping of hostname to IP address.
            platform (str) – Platform in the format os[/arch[/variant]].
            isolation (str) – Isolation technology used during build. (ignored)
            use_config_proxy (bool) – (ignored)
            http_proxy (bool) - Inject http proxy environment variables into container (Podman only)

        Returns:
            first item is Image built
            second item is the build logs

        Raises:
            BuildError: when there is an error during the build.
            APIError: when service returns an error.
            TypeError: when neither path nor fileobj is not specified.
        """
        if "path" not in kwargs and "fileobj" not in kwargs:
            raise TypeError("Either path or fileobj must be provided.")

        if "gzip" in kwargs and "encoding" in kwargs:
            raise PodmanError("Custom encoding not supported when gzip enabled.")

        # All unsupported kwargs are silently ignored
        params = {
            "dockerfile": kwargs.get("dockerfile", None),
            "forcerm": kwargs.get("forcerm", None),
            "httpproxy": kwargs.get("http_proxy", None),
            "networkmode": kwargs.get("network_mode", None),
            "nocache": kwargs.get("nocache", None),
            "platform": kwargs.get("platform", None),
            "pull": kwargs.get("pull", None),
            "q": kwargs.get("quiet", None),
            "remote": kwargs.get("remote", None),
            "rm": kwargs.get("rm", None),
            "shmsize": kwargs.get("shmsize", None),
            "squash": kwargs.get("squash", None),
            "t": kwargs.get("tag", None),
            "target": kwargs.get("target", None),
        }

        if "buildargs" in kwargs:
            params["buildargs"] = json.dumps(kwargs.get("buildargs"))

        if "cache_from" in kwargs:
            params["cacheform"] = json.dumps(kwargs.get("cache_from"))

        if "container_limits" in kwargs:
            params["cpuperiod"] = kwargs["container_limits"].get("cpuperiod", None)
            params["cpuquota"] = kwargs["container_limits"].get("cpuquota", None)
            params["cpusetcpus"] = kwargs["container_limits"].get("cpusetcpus", None)
            params["cpushares"] = kwargs["container_limits"].get("cpushares", None)
            params["memory"] = kwargs["container_limits"].get("memory", None)
            params["memswap"] = kwargs["container_limits"].get("memswap", None)

        if "extra_hosts" in kwargs:
            params["extrahosts"] = json.dumps(kwargs.get("extra_hosts"))

        if "labels" in kwargs:
            params["labels"] = json.dumps(kwargs.get("labels"))

        params = dict(filter(lambda e: e[1] is not None, params.items()))

        context_dir = params.pop("path", None)
        timeout = params.pop("timeout", api.DEFAULT_TIMEOUT)

        body = None
        if context_dir:
            # The Dockerfile will be copied into the context_dir if needed
            params["dockerfile"] = api.prepare_dockerfile(context_dir, params["dockerfile"])

            excludes = api.prepare_dockerignore(context_dir)
            body = api.create_tar(context_dir, exclude=excludes, gzip=kwargs.get("gzip", False))

        response = self.client.post(
            "/build",
            params=params,
            data=body,
            headers={
                "Content-type": "application/x-tar",
                "X-Registry-Config": "TODO",
            },
            stream=True,
            timeout=timeout,
        )
        if hasattr(body, "close"):
            body.close()

        if response.status_code != 200:
            body = response.json()
            raise APIError(body["cause"], response=response, explanation=body["message"])

        image_id = unknown = None
        marker = re.compile(r'(^Successfully built |sha256:)([0-9a-f]+)$')
        report_stream, stream = itertools.tee(response.iter_lines())
        for line in stream:
            result = json.loads(line)
            if "error" in result:
                raise BuildError(result["error"], report_stream)
            if "stream" in result:
                match = marker.match(result["stream"])
                if match:
                    image_id = match.group(2)
            unknown = line

        if image_id:
            return self.get(image_id), report_stream

        raise BuildError(unknown or 'Unknown', report_stream)
