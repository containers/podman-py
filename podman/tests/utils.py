import os
import re
import subprocess

from platform import freedesktop_os_release


def podman_version() -> tuple[int, ...]:
    cmd = ["podman", "info", "--format", "{{.Version.Version}}"]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
        assert proc.stdout is not None
        version = proc.stdout.read().decode("utf-8").strip()
    match = re.match(r"(\d+\.\d+\.\d+)", version)
    if not match:
        raise RuntimeError(f"Unable to detect podman version. Got \"{version}\"")
    version = match.group(1)
    return tuple(int(x) for x in version.split("."))


def is_root() -> bool:
    """Check if the current user is root.

    Returns:
        True if running as root (uid == 0), False otherwise.
    """
    return os.geteuid() == 0


OS_RELEASE = freedesktop_os_release()
PODMAN_VERSION = podman_version()
