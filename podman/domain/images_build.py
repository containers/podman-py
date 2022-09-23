"""Mixin for Image build support."""
import json
import logging
import pathlib
import random
import re
import shutil
import tempfile
from typing import Any, Dict, Iterator, List, Tuple

import itertools

from podman import api
from podman.domain.images import Image
from podman.errors import BuildError, PodmanError, ImageNotFound

logger = logging.getLogger("podman.images")


class BuildMixin:
    """Class providing build method for ImagesManager."""

    # pylint: disable=too-many-locals,too-many-branches,too-few-public-methods,too-many-statements
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
            dockerfile (str) – full path to the Dockerfile / Containerfile
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
            layers (bool) - Cache intermediate layers during build.
            output (str) - specifies if any custom build output is selected for following build.
            outputformat (str) - The format of the output image's manifest and configuration data.

        Returns:
            first item is the podman.domain.images.Image built

            second item is the build logs

        Raises:
            BuildError: when there is an error during the build
            APIError: when service returns an error
            TypeError: when neither path nor fileobj is not specified
        """

        params = self._render_params(kwargs)

        body = None
        path = None
        if "fileobj" in kwargs:
            path = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
            filename = pathlib.Path(path.name) / params["dockerfile"]

            with open(filename, "w", encoding='utf-8') as file:
                shutil.copyfileobj(kwargs["fileobj"], file)
            body = api.create_tar(anchor=path.name, gzip=kwargs.get("gzip", False))
        elif "path" in kwargs:
            filename = pathlib.Path(kwargs["path"]) / params["dockerfile"]
            # The Dockerfile will be copied into the context_dir if needed
            params["dockerfile"] = api.prepare_containerfile(kwargs["path"], str(filename))

            excludes = api.prepare_containerignore(kwargs["path"])
            body = api.create_tar(
                anchor=kwargs["path"], exclude=excludes, gzip=kwargs.get("gzip", False)
            )

        post_kwargs = {}
        if kwargs.get("timeout"):
            post_kwargs["timeout"] = float(kwargs.get("timeout"))

        response = self.client.post(
            "/build",
            params=params,
            data=body,
            headers={
                "Content-type": "application/x-tar",
                # "X-Registry-Config": "TODO",
            },
            stream=True,
            **post_kwargs,
        )
        if hasattr(body, "close"):
            body.close()

        if hasattr(path, "cleanup"):
            path.cleanup()

        response.raise_for_status(not_found=ImageNotFound)

        image_id = unknown = None
        marker = re.compile(r"(^[0-9a-f]+)\n$")
        report_stream, stream = itertools.tee(response.iter_lines())
        for line in stream:
            result = json.loads(line)
            if "error" in result:
                raise BuildError(result["error"], report_stream)
            if "stream" in result:
                match = marker.match(result["stream"])
                if match:
                    image_id = match.group(1)
            unknown = line

        if image_id:
            return self.get(image_id), report_stream

        raise BuildError(unknown or "Unknown", report_stream)

    @staticmethod
    def _render_params(kwargs) -> Dict[str, List[Any]]:
        """Map kwargs to query parameters.

        All unsupported kwargs are silently ignored.
        """
        if "path" not in kwargs and "fileobj" not in kwargs:
            raise TypeError("Either path or fileobj must be provided.")

        if "gzip" in kwargs and "encoding" in kwargs:
            raise PodmanError("Custom encoding not supported when gzip enabled.")

        params = {
            "dockerfile": kwargs.get("dockerfile"),
            "forcerm": kwargs.get("forcerm"),
            "httpproxy": kwargs.get("http_proxy"),
            "networkmode": kwargs.get("network_mode"),
            "nocache": kwargs.get("nocache"),
            "platform": kwargs.get("platform"),
            "pull": kwargs.get("pull"),
            "q": kwargs.get("quiet"),
            "remote": kwargs.get("remote"),
            "rm": kwargs.get("rm"),
            "shmsize": kwargs.get("shmsize"),
            "squash": kwargs.get("squash"),
            "t": kwargs.get("tag"),
            "target": kwargs.get("target"),
            "layers": kwargs.get("layers"),
            "output": kwargs.get("output"),
            "outputformat": kwargs.get("outputformat"),
        }

        if "buildargs" in kwargs:
            params["buildargs"] = json.dumps(kwargs.get("buildargs"))
        if "cache_from" in kwargs:
            params["cachefrom"] = json.dumps(kwargs.get("cache_from"))

        if "container_limits" in kwargs:
            params["cpuperiod"] = kwargs["container_limits"].get("cpuperiod")
            params["cpuquota"] = kwargs["container_limits"].get("cpuquota")
            params["cpusetcpus"] = kwargs["container_limits"].get("cpusetcpus")
            params["cpushares"] = kwargs["container_limits"].get("cpushares")
            params["memory"] = kwargs["container_limits"].get("memory")
            params["memswap"] = kwargs["container_limits"].get("memswap")

        if "extra_hosts" in kwargs:
            params["extrahosts"] = json.dumps(kwargs.get("extra_hosts"))
        if "labels" in kwargs:
            params["labels"] = json.dumps(kwargs.get("labels"))

        if params["dockerfile"] is None:
            params["dockerfile"] = f".containerfile.{random.getrandbits(160):x}"

        # Remove any unset parameters
        return dict(filter(lambda i: i[1] is not None, params.items()))
