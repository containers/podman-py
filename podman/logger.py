import os
import logging


LOGLEVEL = os.environ.get("PODMAN_LOGLEVEL", "INFO")
logger = logging.getLogger("Podman Lib")
logger.setLevel(LOGLEVEL)
