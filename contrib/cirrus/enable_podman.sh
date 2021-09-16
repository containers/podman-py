#!/bin/bash

set -eo pipefail

systemctl enable podman.socket podman.service
systemctl start podman.socket
systemctl status podman.socket ||:

# log which version of podman we just enabled
echo "Locate podman: $(type -P podman)"
podman --version
