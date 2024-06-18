"""Helper functions for managing paths"""

import errno
import getpass
import os
import stat


def get_runtime_dir() -> str:
    """Returns the runtime directory for the current user"""
    try:
        return os.environ['XDG_RUNTIME_DIR']
    except KeyError:
        user = getpass.getuser()
        fallback = f'/tmp/podmanpy-runtime-dir-fallback-{user}'

        try:
            # This must be a real directory, not a symlink, so attackers can't
            # point it elsewhere. So we use lstat to check it.
            fallback_st = os.lstat(fallback)
        except OSError as e:
            if e.errno == errno.ENOENT:
                os.mkdir(fallback, 0o700)
            else:
                raise
        else:
            # The fallback must be a directory
            if not stat.S_ISDIR(fallback_st.st_mode):
                os.unlink(fallback)
                os.mkdir(fallback, 0o700)
            # Must be owned by the user and not accessible by anyone else
            elif (fallback_st.st_uid != os.getuid()) or (
                fallback_st.st_mode & (stat.S_IRWXG | stat.S_IRWXO)
            ):
                os.rmdir(fallback)
                os.mkdir(fallback, 0o700)

        return fallback


def get_xdg_config_home() -> str:
    """Returns the XDG_CONFIG_HOME directory for the current user"""
    try:
        return os.environ["XDG_CONFIG_HOME"]
    except KeyError:
        return os.path.join(os.path.expanduser("~"), ".config")
