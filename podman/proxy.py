import os
import subprocess
import requests_unixsocket


def create_forwarding_socket(
        host, user='root', socket_directory='/tmp',
        remote_socket_path='/run/podman/podman.sock'
) -> str:
    """
    Creates a socket that forwards to the Podman socket on the host.

    TODO:
        Directory for temporary socket should be different under Windows.
        If ssh keys are not correctly configured, it will ask you for a password. Disallow password altogether.
    """
    socket_name = f'podman_{host}.sock'
    socket_path = os.path.join(socket_directory, socket_name)

    cmd = f'ssh -fN -L{socket_path}:{remote_socket_path} {user}@{host}'.split(' ')

    subprocess.run(cmd)

    return socket_path

    print('Fetch the response!')
    session = requests_unixsocket.Session()

    response = session.get('http+unix://%2Ftmp%2Fpodman.sock/v1.24/libpod/images/json')
