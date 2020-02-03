from libpod_errors import process_image_error


def list(context):
    with context.get_connection() as conn:
        return conn.do_request("GET", "images/json")


def inspect(context, name):
    endpoint = "images/{}/json"
    path_params = [name]
    with context.get_connection() as conn:
        r = conn.do_request("GET", endpoint, path_params=path_params)
        return process_image_error(r)


def remove(context, name, force=False):
    endpoint = "images/{}"
    path_params = [name]
    query_params = {"force": force}
    with context.get_connection() as conn:
        r = conn.do_request("DELETE", endpoint, path_params=path_params, query_params=query_params)
        return process_image_error(r)
