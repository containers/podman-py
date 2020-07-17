SOCKETNOTFOUND = '''Socket was not found at the path: {}

    Check if the systemd services are up and running with either:
        systemctl status --user podman.socket
            or
        systemctl status podman.socket

    If they're up but this message still shows up consider increase the TIMEOUT
    value at the podman.http.HTTPConnectionSocket class.
'''


class SchemaNotSupported(NotImplementedError):

    def __init__(self, schema, supported_schemas):
        self.schema = schema
        msg = (
            'Schema {} is not yet supported.\n'
            'Currently Supported Schemas: {}'
            ).format(self.schema, supported_schemas)
        super(SchemaNotSupported, self).__init__(msg)


class SocketFileNotFound(FileNotFoundError):

    def __init__(self, file_path):
        msg = SOCKETNOTFOUND.format(
            file_path
            )
        super(SocketFileNotFound, self).__init__(msg)
