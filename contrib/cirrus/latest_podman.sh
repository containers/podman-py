#!/bin/bash

set -xeo pipefail

systemctl enable sshd
systemctl start sshd
systemctl status sshd ||:

ssh-keygen -t ecdsa -b 521 -f /root/.ssh/id_ecdsa -P ""
cp /root/.ssh/authorized_keys /root/.ssh/authorized_keys%
cat /root/.ssh/id_ecdsa.pub >>/root/.ssh/authorized_keys

mkdir -p "$GOPATH/src/github.com/containers/"
cd "$GOPATH/src/github.com/containers/"

systemctl stop podman.socket ||:
dnf erase podman -y
git clone https://github.com/containers/podman.git

cd podman
make binaries
make install PREFIX=/usr

systemctl enable podman.socket podman.service
systemctl start podman.socket
systemctl status podman.socket ||:

podman --version
