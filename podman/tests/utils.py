import pathlib
import csv

try:
    from platform import freedesktop_os_release
except ImportError:

    def freedesktop_os_release() -> dict[str, str]:
        """This is a fallback for platforms that don't have the freedesktop_os_release function.
        Python < 3.10
        """
        path = pathlib.Path("/etc/os-release")
        with open(path, "r") as f:
            reader = csv.reader(f, delimiter="=")
            return dict(reader)


OS_RELEASE = freedesktop_os_release()
