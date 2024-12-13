#!/bin/bash

set -xeo pipefail

systemctl stop podman.socket || :

dnf remove podman -y
dnf copr enable rhcontainerbot/podman-next -y
dnf install podman -y
