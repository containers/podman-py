"""Utility functions for dealing with stdout and stderr."""

HEADER_SIZE = 8
STDOUT = 1
STDERR = 2


# pylint: disable=line-too-long
def demux_output(data_bytes):
    """Demuxes the output of a container stream into stdout and stderr streams.

    Stream data is expected to be in the following format:
    - 1 byte: stream type (1=stdout, 2=stderr)
    - 3 bytes: padding
    - 4 bytes: payload size (big-endian)
    - N bytes: payload data
    ref: https://docs.podman.io/en/latest/_static/api.html?version=v5.0#tag/containers/operation/ContainerAttachLibpod

    Args:
        data_bytes: Bytes object containing the combined stream data.

    Returns:
        A tuple containing two bytes objects: (stdout, stderr).
    """
    stdout = b""
    stderr = b""
    while len(data_bytes) >= HEADER_SIZE:
        # Extract header information
        header, data_bytes = data_bytes[:HEADER_SIZE], data_bytes[HEADER_SIZE:]
        stream_type = header[0]
        payload_size = int.from_bytes(header[4:HEADER_SIZE], "big")
        # Check if data is sufficient for payload
        if len(data_bytes) < payload_size:
            break  # Incomplete frame, wait for more data

        # Extract and process payload
        payload = data_bytes[:payload_size]
        if stream_type == STDOUT:
            stdout += payload
        elif stream_type == STDERR:
            stderr += payload
        else:
            # todo: Handle unexpected stream types
            pass

        # Update data for next frame
        data_bytes = data_bytes[payload_size:]

    return stdout, stderr
