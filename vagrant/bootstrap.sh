#!/bin/sh
# Install development version of Podman

echo "DISABLE CONTAINER TOOLS"
echo "======================="
sudo dnf -y module disable container-tools

echo "INSTALL DNF-COMMAND"
echo "==================="
sudo dnf -y install 'dnf-command(copr)'

echo "ADD SELINUX!"
echo "============"
sudo dnf -y copr enable rhcontainerbot/container-selinux

echo "ADD KUBIC REPO"
echo "=============="
cd /etc/yum.repos.d
sudo wget https://download.opensuse.org/repositories/devel:kubic:libcontainers:testing/CentOS_8/devel:kubic:libcontainers:testing.repo

echo "INSTALL PODMAN"
echo "=============="
sudo dnf -y install podman

echo "CREATE PODMAN SERVICE"
sudo cp /tmp/podman.service /etc/systemd/system/podman.service

# Start the HTTP api
echo "START PODMAN API"