"""APIClient for connecting to Podman service."""
import urllib.parse
from typing import IO, Any, ClassVar, Dict, Iterable, List, Mapping, Optional, Tuple, Union

import requests
from requests import Response

from podman.api.uds import UDSAdapter
from podman.errors.exceptions import APIError
from podman.tlsconfig import TLSConfig

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


class APIClient(requests.Session):
    """Client for Podman service API."""

    # Abstract methods (delete,get,head,post) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=arguments-differ
    # pylint: disable=too-many-instance-attributes

    # TODO pull version from a future Version library
    api_version: str = "3.0.0"
    compatible_version: str = "1.40"

    default_timeout: float = 60.0

    supported_schemes: ClassVar[List[str]] = ("unix", "http+unix")

    required_headers: ClassVar[Dict[str, str]] = {
        "User-Agent": f"PodmanPy/{api_version}",
    }
    """These headers are included in all requests to service."""

    default_headers: ClassVar[Dict[str, str]] = {}
    """These headers are included in all requests to service.
       Headers provided in request will override.
    """

    def __init__(
        self,
        base_url: str = None,
        version: Optional[str] = None,
        timeout: Optional[float] = None,
        tls: Union[TLSConfig, bool] = False,
        user_agent: Optional[str] = None,
        num_pools: Optional[int] = None,
        credstore_env: Optional[Mapping[str, str]] = None,
        **kwargs,
    ):
        """Instantiate APIClient object.

        Raises:
            ValueError: when a parameter is incorrect.
        """
        super().__init__()

        _ = tls

        # FIXME map scheme unix:// -> http+unix://,
        # FIXME url quote slashes in netloc
        self.base_url = base_url

        self.version = version or APIClient.api_version
        self.path_prefix = f"/v{self.version}/libpod"
        self.compatible_version = (
            kwargs.get("compatible_version", None) or APIClient.compatible_version
        )
        self.compatible_prefix = f"/v{self.compatible_version}"

        uri = urllib.parse.urlparse(self.base_url)
        if uri.scheme not in APIClient.supported_schemes:
            raise ValueError(
                f"The scheme '{uri.scheme}' is not supported, only {APIClient.supported_schemes}"
            )

        self.uri = uri
        self.timeout = timeout or APIClient.default_timeout
        self.user_agent = user_agent or f"PodmanPy/{self.version}"
        self.pool_maxsize = num_pools or requests.adapters.DEFAULT_POOLSIZE
        self.credstore_env = credstore_env or {}

        if uri.scheme == "http+unix" or "unix":
            self.mount(uri.scheme, UDSAdapter())

    def delete(
        self,
        path: Union[str, bytes],
        params: Union[None, bytes, Mapping[str, str]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: _Timeout = None,
        stream: Optional[bool] = False,
        **kwargs,
    ) -> Response:
        """HTTP DELETE operation against configured Podman service.

        Args:
            path: Relative path to RESTful resource. base_url will be prepended to path.
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple
            stream: Return iterator for content vs reading all content into memory

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an Error.
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
    ) -> Response:
        """HTTP GET operation against configured Podman service.

        Args:
            path: Relative path to RESTful resource. base_url will be prepended to path.
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple
            stream: Return iterator for content vs reading all content into memory

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix with
                compatible prefix

        Raises:
            APIError: when service returns an Error.
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
    ) -> Response:
        """HTTP HEAD operation against configured Podman service.

        Args:
            path: Relative path to RESTful resource. base_url will be prepended to path.
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple
            stream: Return iterator for content vs reading all content into memory

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an Error.
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
    ) -> Response:
        """HTTP POST operation against configured Podman service.

        Args:
            path: Relative path to RESTful resource. base_url will be prepended to path.
            data: HTTP body for operation
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple
            stream: Return iterator for content vs reading all content into memory

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an Error.
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
    ) -> Response:
        """HTTP PUT operation against configured Podman service.

        Args:
            path: Relative path to RESTful resource. base_url will be prepended to path.
            data: HTTP body for operation
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple
            stream: Return iterator for content vs reading all content into memory

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an Error.
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
    ) -> Response:
        """HTTP operation against configured Podman service.

        Args:
            method: HTTP method to use for request
            path: Relative path to RESTful resource. base_url will be prepended to path.
            params: Optional parameters to include with URL.
            headers: Optional headers to include in request.
            timeout: Number of seconds to wait on request, or (connect timeout, read timeout) tuple

        Keyword Args:
            compatible: Will override the default path prefix with compatible prefix

        Raises:
            APIError: when service returns an Error.
        """
        if timeout is None:
            timeout = APIClient.default_timeout

        if not path.startswith("/"):
            path = f"/{path}"

        compatible = kwargs.get("compatible", False)
        path_prefix = self.compatible_prefix if compatible else self.path_prefix

        try:
            return self.request(
                method.upper(),
                self.base_url + path_prefix + path,
                params=params,
                data=data,
                headers=self._headers(headers or {}),
                timeout=timeout,
                stream=stream,
            )
        except OSError as e:
            raise APIError(path) from e

    @classmethod
    def _headers(cls, headers: Mapping[str, str]) -> Dict[str, str]:
        """Generate header dictionary for request.

        Args:
            headers: headers unique to this request.
        """
        hdrs = APIClient.default_headers.copy()
        hdrs.update(headers)
        hdrs.update(APIClient.required_headers)
        return hdrs
