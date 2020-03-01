# flake8: noqa
from .unixconn import UnixHTTPAdapter

try:
    from .sshconn import SSHHTTPAdapter
except ImportError:
    pass
