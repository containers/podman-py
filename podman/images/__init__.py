import json
import logging

import errors


def list(api):
    response = api.request("GET", api.join("/images/json"))
    return json.loads(response.read())


def inspect(api, name):
    try:
        response = api.request(
            "GET", api.join("/images/{}/json".format(api.quote(name)))
        )
        return json.loads(response.read())
    except errors.NotFoundError as e:
        _report_not_found(e, e.response)


def remove(api, name, force=None):
    path = ""
    if force is not None:
        path = api.join("/images/", api.quote(name), {"force": force})
    else:
        path = api.join("/images/", api.quote(name))

    try:
        response = api.request("DELETE", path)
        return json.loads(response.read())
    except errors.NotFoundError as e:
        _report_not_found(e, e.response)


def _report_not_found(e, response):
    body = json.loads(response.read())
    logging.info(body["cause"])
    raise errors.ImageNotFound(body["message"]) from e
