"""PodmanPy Tests."""

# Do not auto-update these from version.py,
#   as test code should be changed to reflect changes in Podman API versions
BASE_SOCK = "unix:///run/api.sock"
LIBPOD_URL = "http://%2Frun%2Fapi.sock/v5.8.0/libpod"
COMPATIBLE_URL = "http://%2Frun%2Fapi.sock/v1.40"


def normalized_url(url: str) -> str:
    """Normalize URLs when comparing requests_mock request history (%2F vs %2f)."""
    return url.lower()
