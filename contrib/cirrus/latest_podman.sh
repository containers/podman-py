#!/bin/bash

set -xeo pipefail

mkdir -p "$GOPATH/src/github.com/containers/"
cd "$GOPATH/src/github.com/containers/"

dnf erase podman -y
git clone https://github.com/containers/podman.git

cd podman
make binaries
make install PREFIX=/usr

systemctl enable podman.socket podman.service
systemctl start podman.socket
