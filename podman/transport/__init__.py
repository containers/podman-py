# flake8: noqa
from .unixconn import UnixHTTPAdapter

try:
    from .sshadapter import SSHHTTPAdapter
except ImportError:
    pass
