"""PodmanPy Tests."""

# Do not auto-update these from version.py,
#   as test code should be changed to reflect changes in Podman API versions
BASE_SOCK = "unix:///run/api.sock"
LIBPOD_URL = "http://%2Frun%2Fapi.sock/v5.2.0/libpod"
COMPATIBLE_URL = "http://%2Frun%2Fapi.sock/v1.40"
