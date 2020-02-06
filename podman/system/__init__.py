from http import HTTPStatus


def version(api, verify_version=False):
    response = api.request("GET", "/_ping")
    response.read()
    if response.getcode() == HTTPStatus.OK:
        return response.headers

    # TODO: verify api.base and header[Api-Version] compatible


__all__ = [version]

