from http.client import HTTPException


class EntityNotFound(Exception):
    """An entity does not exist on podman"""

    def __init__(self, response):
        self.response = response
        msg = "{} ({}).".format(
                response.json()["message"],
            )
        super(EntityNotFound, self).__init__(msg)


class EndpointNotFound(Exception):
    """HTTP request returned a http.HTTPStatus.NOT_FOUND."""

    def __init__(self, method, url, msg, response):
        self.response = response
        msg = "Endpoint Not Found: {} {}".format(
                method,
                url,
                msg,
            )
        super(EndpointNotFound, self).__init__(msg)


class InternalServerError(Exception):
    """Podman service reported an internal error."""

    def __init__(self, method, url, msg, response):
        self.response = response
        msg = "Request {} {}: {}".format(method, url, msg)
        super().__init__(msg)
