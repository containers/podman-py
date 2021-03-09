"""Utility functions for working with tarball's."""
import os
import pathlib
import random
import shutil
import sys
import tarfile
import tempfile
from fnmatch import fnmatch
from typing import BinaryIO, List, Optional


def prepare_dockerignore(anchor: str) -> List[str]:
    """Read .dockerignore and return exclude list."""
    file = os.path.join(anchor, ".dockerignore")
    if not os.path.exists(file):
        return []

    with open(file, "r") as file:
        return list(
            filter(
                lambda l: len(l) > 0 and not l.startswith("#"),
                list(line.strip() for line in file.readlines()),
            )
        )


def prepare_dockerfile(anchor: str, dockerfile: str) -> str:
    """Ensure that Dockerfile or a proxy Dockerfile is in context_dir.

    Args:
        anchor: Build context directory
        dockerfile: Path to Dockerfile

    Returns:
        path to Dockerfile in root of context directory
    """
    anchor_path = pathlib.Path(anchor)
    dockerfile_path = pathlib.Path(dockerfile)

    if dockerfile_path.parent.samefile(anchor_path):
        return dockerfile

    proxy_path = anchor_path / f".dockerfile.{random.getrandbits(160):x}"
    shutil.copy2(dockerfile_path, proxy_path, follow_symlinks=False)
    return str(proxy_path)


def create_tar(
    anchor: str, name: Optional[str] = None, exclude: List[str] = None, gzip: bool = False
) -> BinaryIO:
    """Create a tarfile from context_dir to send to Podman service"""

    def add_filter(info: tarfile.TarInfo) -> Optional[tarfile.TarInfo]:
        """Filter files targeted to be added to tarfile.

        Args:
            info: Information on the file targeted to be added

        Returns:
            None: if file is not to be added
            TarInfo: when file is to be added. Modified as needed.

        Notes:
            exclude is captured from parent
        """
        if not (info.isfile() or info.isdir() or info.issym()):
            return None

        if _exclude_matcher(info.name, exclude):
            return None

        # Workaround https://bugs.python.org/issue32713. Fixed in Python 3.7
        if info.mtime < 0 or info.mtime > 8 ** 11 - 1:
            info.mtime = int(info.mtime)

        # do not leak client information to service
        info.uid = 0
        info.uname = info.gname = "root"

        if sys.platform == 'win32':
            info.mode = info.mode & 0o755 | 0o111
        return info

    if name is None:
        name = tempfile.NamedTemporaryFile()
    else:
        name = pathlib.Path(name)

    exclude.append(".dockerignore")
    exclude.append("!" + str(name))

    mode = "w:gz" if gzip else "w"
    with tarfile.open(name, mode) as tar:
        tar.add(anchor, arcname=os.path.basename(anchor), recursive=True, filter=add_filter)

    return open(name, "rb")


def _exclude_matcher(path: str, exclude: List[str]) -> bool:
    """Returns True if path matches an entry in exclude.

    Note:
        FIXME Not compatible, support !, **, etc
    """
    if len(exclude) == 0:
        return False

    for pattern in exclude:
        if fnmatch(path, pattern):
            return True
    return False
