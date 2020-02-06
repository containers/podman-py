from http.client import HTTPException


class NotFoundError(HTTPException):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class ImageNotFound(NotFoundError):
    pass


class ContainerNotFound(NotFoundError):
    pass


class PodNotFound(NotFoundError):
    pass


class InternalServerError(HTTPException):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response
