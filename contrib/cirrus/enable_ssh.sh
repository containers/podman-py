#!/bin/bash

set -eo pipefail

systemctl enable sshd
systemctl start sshd
systemctl status sshd ||:

ssh-keygen -t ecdsa -b 521 -f /root/.ssh/id_ecdsa -P ""
cp /root/.ssh/authorized_keys /root/.ssh/authorized_keys%
cat /root/.ssh/id_ecdsa.pub >>/root/.ssh/authorized_keys
