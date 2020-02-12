"""
Combines all api mixins from the single resources into the final api client class.
"""
from ..resources import (
    ImageApiMixin
)

class PodmanAPIClient(
    # BuildApiMixin,
    # ConfigApiMixin,
    # ContainerApiMixin,
    # DaemonApiMixin,
    # ExecApiMixin,
    ImageApiMixin,
    # NetworkApiMixin,
    # PluginApiMixin,
    # SecretApiMixin,
    # ServiceApiMixin,
    # VolumeApiMixin
):
    """
    A low-level client for the Podman Remote API.

    Example:

    >>> from podman.api import PodmanAPIClient
    >>> client = PodmanAPIClient(url='unix://run/podman/podman.sock')
    >>> client.version()
    {u'ApiVersion': u'1.33',
     u'Arch': u'amd64',
     u'BuildTime': u'2017-11-19T18:46:37.000000000+00:00',
     u'GitCommit': u'f4ffd2511c',
     u'GoVersion': u'go1.9.2',
     u'KernelVersion': u'4.14.3-1-ARCH',
     u'MinAPIVersion': u'1.12',
     u'Os': u'linux',
     u'Version': u'17.10.0-ce'}
    """
    pass

