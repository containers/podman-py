import pathlib
import csv
import re
import subprocess

try:
    from platform import freedesktop_os_release
except ImportError:

    def freedesktop_os_release() -> dict[str, str]:
        """This is a fallback for platforms that don't have the freedesktop_os_release function.
        Python < 3.10
        """
        path = pathlib.Path("/etc/os-release")
        with open(path) as f:
            reader = csv.reader(f, delimiter="=")
            return dict(reader)


def podman_version() -> tuple[int, ...]:
    cmd = ["podman", "info", "--format", "{{.Version.Version}}"]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
        version = proc.stdout.read().decode("utf-8").strip()
    match = re.match(r"(\d+\.\d+\.\d+)", version)
    if not match:
        raise RuntimeError(f"Unable to detect podman version. Got \"{version}\"")
    version = match.group(1)
    return tuple(int(x) for x in version.split("."))


OS_RELEASE = freedesktop_os_release()
PODMAN_VERSION = podman_version()
