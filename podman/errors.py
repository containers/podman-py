"""
Errors module is used to extend HTTPException for Podman API.
"""
from http.client import HTTPException


class PodmanException(Exception):
    """
    A base class from which all other exceptions inherit.

    If you want to catch all errors that the podman client might raise,
    catch this base exception.
    """


class NotFoundError(HTTPException):
    """ HTTP request returned a http.HTTPStatus.NOT_FOUND. """

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class ImageNotFound(NotFoundError):
    """
    HTTP request returned a http.HTTPStatus.NOT_FOUND.
    Specialized for Image not found.
    """


class ContainerNotFound(NotFoundError):
    """
    HTTP request returned a http.HTTPStatus.NOT_FOUND.
    Specialized for Container not found.
    """


class PodNotFound(NotFoundError):
    """
    HTTP request returned a http.HTTPStatus.NOT_FOUND.
    Specialized for Pod not found.
    """


class InternalServerError(HTTPException):
    """ Podman service reported an internal error. """
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class InvalidArgument(PodmanException):
    pass


# Podman errors
# TODO: Remove unnecessary errors and unify with those already existing
def create_api_error_from_http_exception(e):
    """ Create a suitable APIError from requests.exceptions.HTTPError. """
    response = e.response
    try:
        explanation = response.json()['message']
    except ValueError:
        explanation = (response.content or '').strip()
    cls = APIError
    if response.status_code == 404:
        if explanation and ('No such image' in str(explanation) or
                            'not found: does not exist or no pull access'
                            in str(explanation) or
                            'repository does not exist' in str(explanation)):
            cls = ImageNotFound
        else:
            cls = NotFound
    raise cls(e, response=response, explanation=explanation)


class APIError(PodmanException):
    """
    An HTTP error from the API.
    """
    def __init__(self, message, response=None, explanation=None):
        # requests 1.2 supports response as a keyword argument, but
        # requests 1.1 doesn't
        super(APIError, self).__init__(message)
        self.response = response
        self.explanation = explanation

    def __str__(self):
        message = super().__str__()

        if self.is_client_error():
            message = '{0} Client Error: {1}'.format(
                self.response.status_code, self.response.reason)

        elif self.is_server_error():
            message = '{0} Server Error: {1}'.format(
                self.response.status_code, self.response.reason)

        if self.explanation:
            message = '{0} ("{1}")'.format(message, self.explanation)

        return message

    @property
    def status_code(self):
        if self.response is not None:
            return self.response.status_code

    def is_error(self):
        return self.is_client_error() or self.is_server_error()

    def is_client_error(self):
        if self.status_code is None:
            return False
        return 400 <= self.status_code < 500

    def is_server_error(self):
        if self.status_code is None:
            return False
        return 500 <= self.status_code < 600


class NotFound(APIError):
    pass


class ImageNotFound(NotFound):
    pass


class InvalidVersion(PodmanException):
    pass


class InvalidRepository(PodmanException):
    pass


class InvalidConfigFile(PodmanException):
    pass


class InvalidArgument(PodmanException):
    pass


class DeprecatedMethod(PodmanException):
    pass


class NullResource(PodmanException, ValueError):
    pass


class ContainerError(PodmanException):
    """
    Represents a container that has exited with a non-zero exit code.
    """
    def __init__(self, container, exit_status, command, image, stderr):
        self.container = container
        self.exit_status = exit_status
        self.command = command
        self.image = image
        self.stderr = stderr

        err = ": {}".format(stderr) if stderr is not None else ""
        msg = ("Command '{}' in image '{}' returned non-zero exit "
               "status {}{}").format(command, image, exit_status, err)

        super().__init__(msg)


class StreamParseError(RuntimeError):
    def __init__(self, reason):
        self.msg = reason


class BuildError(PodmanException):
    def __init__(self, reason, build_log):
        super().__init__(reason)
        self.msg = reason
        self.build_log = build_log


class ImageLoadError(PodmanException):
    pass


def create_unexpected_kwargs_error(name, kwargs):
    quoted_kwargs = ["'{}'".format(k) for k in sorted(kwargs)]
    text = ["{}() ".format(name)]
    if len(quoted_kwargs) == 1:
        text.append("got an unexpected keyword argument ")
    else:
        text.append("got unexpected keyword arguments ")
    text.append(', '.join(quoted_kwargs))
    return TypeError(''.join(text))


class MissingContextParameter(PodmanException):
    def __init__(self, param):
        self.param = param

    def __str__(self):
        return ("missing parameter: {}".format(self.param))


class ContextAlreadyExists(PodmanException):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return ("context {} already exists".format(self.name))


class ContextException(PodmanException):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return (self.msg)


class ContextNotFound(PodmanException):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Context '{self.name}' not found"
