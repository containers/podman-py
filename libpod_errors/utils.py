from libpod_errors import ErrNoSuchImage, ErrGeneric, ErrInternal
from json import loads


def process_image_error(response):
    d = loads(response.read())
    if response.status == 404:
        raise ErrNoSuchImage(d.get("cause", ""), d.get("message", ""))
    return process_pass_fail(response.status, d)


def process_pass_fail(code, data):
    if 199 < code < 299:
        return data
    if 299 < code < 499:
        raise ErrGeneric(data.get("cause", ""), data.get("message", ""))
    if code > 499:
        raise ErrInternal(data.get("cause", ""), data.get("message", ""))
