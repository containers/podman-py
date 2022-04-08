"""APIClient for connecting to Podman service."""
import json
import urllib.parse
from typing import Any, ClassVar, IO, Iterable, List, Mapping, Optional, Tuple, Type, Union

import requests
from requests.adapters import HTTPAdapter

from podman import api
from podman.api.ssh import SSHAdapter
from podman.api.uds import UDSAdapter
from podman.errors import APIError, NotFound
from podman.tlsconfig import TLSConfig
from podman.version import __version__

_Data = Union[
    None,
    str,
    bytes,
    Mapping[str, Any],
    Iterable[Tuple[str, Optional[str]]],
    IO,
]
"""Type alias for request data parameter."""

_Timeout = Union[None, float, Tuple[float, float], Tuple[float, None]]
"""Type alias for request timeout parameter."""


class APIResponse:
    """APIResponse proxy requests.Response objects.

    Override raise_for_status() to implement Podman API binding errors.
    All other methods and attributes forwarded to original Response.
    """

    def __init__(self, response: requests.Response):
        """Initialize APIResponse.

        Args:
            response: the requests.Response to provide implementation
        """
        self._response = response

    def __getattr__(self, item: str):
        """Forward any query for an attribute not defined in this proxy class to wrapped class."""
        return getattr(self._response, item)

    def raise_for_status(self, not_found: Type[APIError] = NotFound) -> None:
        """Raises exception when Podman service reports one."""
        if self.status_code < 400:
            return

        try:
            body = self.json()
            cause = body["cause"]
            message = body["message"]
        except (json.decoder.JSONDecodeError, KeyError):
            cause = message = self.text

        if self.status_code == requests.codes.not_found:
            raise not_found(cause, response=self._response, explanation=message)
        raise APIError(cause, response=self._response, explanation=message)


class APIClient(requests.Session):
    """Client for Podman service API."""

    # Abstract methods (delete,get,head,post) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=too-many-instance-attributes,arguments-differ,arguments-renamed

    supported_schemes: ClassVar[List[str]] = (
        "unix",
        "http+unix",
        "ssh",
        "http+ssh",
        "tcp",
        "http",
    )

    def __init__(
        self,
        base_url: str = None,
        version: Optional[str] = None,
        timeout: Optional[float] = None,
        tls: Union[TLSConfig, bool] = False,
        user_agent: Optional[str] = None,
        num_pools: Optional[int] = None,
        credstore_env: Optional[Mapping[str, str]] = None,
        use_ssh_client=True,
        max_pools_size=None,
        **kwargs,
    ):  # pylint: disable=unused-argument
        """Instantiate APIClient object.

        Args:
            base_url: Address to use for connecting to Podman service.
            version: Override version prefix for Podman resource URLs.
            timeout: Time in seconds to allow for Podman service operation.
            tls: Configuration for TLS connections.
            user_agent: Override User-Agent HTTP header.
            num_pools: The number of connection pools to cache.
            credstore_env: Environment for storing credentials.
            use_ssh_client: Use system ssh agent rather than ssh module. Always, True.
            max_pool_size: Override number of connections pools to maintain.
                Default: requests.adapters.DEFAULT_POOLSIZE

        Keyword Args:
            compatible_version (str): Override version prefix for compatible resource URLs.
            identity (str): Provide SSH key to authenticate SSH connection.

        Raises:
            ValueError: when a parameter is incorrect
        """
        super().__init__()
        self.base_url = self._normalize_url(base_url)

        adapter_kwargs = kwargs.copy()
        if num_pools is not None:
            adapter_kwargs["pool_connections"] = num_pools
        if max_pools_size is not None:
            adapter_kwargs["pool_maxsize"] = max_pools_size
        if timeout is not None:
            adapter_kwargs["timeout"] = timeout

        if self.base_url.scheme == "http+unix":
            self.mount("http://", UDSAdapter(self.base_url.geturl(), **adapter_kwargs))
            self.mount("https://", UDSAdapter(self.base_url.geturl(), **adapter_kwargs))

        elif self.base_url.scheme == "http+ssh":
            self.mount("http://", SSHAdapter(self.base_url.geturl(), **adapter_kwargs))
            self.mount("https://", SSHAdapter(self.base_url.geturl(), **adapter_kwargs))

        elif self.base_url.scheme == "http":
            self.mount("http://", HTTPAdapter(**adapter_kwargs))
            self.mount("https://", HTTPAdapter(**adapter_kwargs))
        else:
            assert False, "APIClient.supported_schemes changed without adding a branch here."

        self.version = version or api.VERSION
        self.path_prefix = f"/v{self.version}/libpod/"
        self.compatible_version = kwargs.get("compatible_version", api.COMPATIBLE_VERSION)
        self.compatible_prefix = f"/v{self.compatible_version}/"

        self.timeout = timeout
        self.pool_maxsize = num_pools or requests.adapters.DEFAULT_POOLSIZE
        self.credstore_env = credstore_env or {}

        self.user_agent = user_agent or (
            f"PodmanPy/{__version__} (API v{self.version}; Compatible v{self.compatible_version})"
        )
        self.headers.update({"User-Agent": self.user_agent})

    @staticmethod
    def _normalize_url(base_url: str) -> urllib.parse.ParseResult:
        uri = urllib.parse.urlparse(base_url)
        if uri.scheme not in APIClient.supported_schemes:
            raise ValueError(
                f"The scheme '{uri.scheme}' must be one of {APIClient.supported_schemes}"
            )

        # Normalize URL scheme, needs to match up with adapter mounts
        if uri.scheme == "unix":
            uri = uri._replace(scheme="http+unix")
        elif uri.scheme == "ssh":
            uri = uri._replace(scheme="http+ssh")
        elif uri.scheme == "tcp":
            uri = uri._replace(scheme="http")

        # Normalize URL netloc, needs to match up with transport adapters expectations
        if uri.netloc == "":
            uri = uri._replace(netloc=uri.path)._replace(path="")
        if "/" in uri.netloc:
            uri = uri._replace(netloc=urllib.parse.quote_plus(uri.netloc))

        return uri

    def delete(
        self,
        path: Union[str, bytes],
        params: Union[None, bytes, Mapping[str, str]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: _Timeout = None,
        stream: Optional[bool] = False,
        **kwargs,
    ) -> APIResponse:
        """HTTP DELETE operation against configured Podman service.

        Args:
            path: Relative path to RESTful resource.
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple
            stream: Return iterator for content vs reading all content into memory

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an error
        """
        return self._request(
            "DELETE",
            path=path,
            params=params,
            headers=headers,
            timeout=timeout,
            stream=stream,
            **kwargs,
        )

    def get(
        self,
        path: Union[str, bytes],
        params: Union[None, bytes, Mapping[str, List[str]]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: _Timeout = None,
        stream: Optional[bool] = False,
        **kwargs,
    ) -> APIResponse:
        """HTTP GET operation against configured Podman service.

        Args:
            path: Relative path to RESTful resource.
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple
            stream: Return iterator for content vs reading all content into memory

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an error
        """
        return self._request(
            "GET",
            path=path,
            params=params,
            headers=headers,
            timeout=timeout,
            stream=stream,
            **kwargs,
        )

    def head(
        self,
        path: Union[str, bytes],
        params: Union[None, bytes, Mapping[str, str]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: _Timeout = None,
        stream: Optional[bool] = False,
        **kwargs,
    ) -> APIResponse:
        """HTTP HEAD operation against configured Podman service.

        Args:
            path: Relative path to RESTful resource.
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple
            stream: Return iterator for content vs reading all content into memory

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an error
        """
        return self._request(
            "HEAD",
            path=path,
            params=params,
            headers=headers,
            timeout=timeout,
            stream=stream,
            **kwargs,
        )

    def post(
        self,
        path: Union[str, bytes],
        params: Union[None, bytes, Mapping[str, str]] = None,
        data: _Data = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: _Timeout = None,
        stream: Optional[bool] = False,
        **kwargs,
    ) -> APIResponse:
        """HTTP POST operation against configured Podman service.

        Args:
            path: Relative path to RESTful resource.
            data: HTTP body for operation
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple
            stream: Return iterator for content vs reading all content into memory

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an error
        """
        return self._request(
            "POST",
            path=path,
            params=params,
            data=data,
            headers=headers,
            timeout=timeout,
            stream=stream,
            **kwargs,
        )

    def put(
        self,
        path: Union[str, bytes],
        params: Union[None, bytes, Mapping[str, str]] = None,
        data: _Data = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: _Timeout = None,
        stream: Optional[bool] = False,
        **kwargs,
    ) -> APIResponse:
        """HTTP PUT operation against configured Podman service.

        Args:
            path: Relative path to RESTful resource.
            data: HTTP body for operation
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple
            stream: Return iterator for content vs reading all content into memory

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an error
        """
        return self._request(
            "PUT",
            path=path,
            params=params,
            data=data,
            headers=headers,
            timeout=timeout,
            stream=stream,
            **kwargs,
        )

    def _request(
        self,
        method: str,
        path: Union[str, bytes],
        data: _Data = None,
        params: Union[None, bytes, Mapping[str, str]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: _Timeout = None,
        stream: Optional[bool] = None,
        **kwargs,
    ) -> APIResponse:
        """HTTP operation against configured Podman service.

        Args:
            method: HTTP method to use for request
            path: Relative path to RESTful resource.
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an error
        """
        # Only set timeout if one is given, lower level APIs will not override None
        timeout_kw = {}
        timeout = timeout or self.timeout
        if timeout_kw is not None:
            timeout_kw["timeout"] = timeout

        compatible = kwargs.get("compatible", False)
        path_prefix = self.compatible_prefix if compatible else self.path_prefix

        path = path.lstrip("/")  # leading / makes urljoin crazy...

        # TODO should we have an option for HTTPS support?
        # Build URL for operation from base_url
        uri = urllib.parse.ParseResult(
            "http",
            self.base_url.netloc,
            urllib.parse.urljoin(path_prefix, path),
            self.base_url.params,
            self.base_url.query,
            self.base_url.fragment,
        )

        try:
            return APIResponse(
                self.request(
                    method.upper(),
                    uri.geturl(),
                    params=params,
                    data=data,
                    headers=(headers or {}),
                    stream=stream,
                    **timeout_kw,
                )
            )
        except OSError as e:
            raise APIError(uri.geturl(), explanation=f"{method.upper()} operation failed") from e
