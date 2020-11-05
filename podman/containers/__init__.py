"""containers provides the operations against containers for a Podman service.
"""

import json


def list_containers(api, all_=None):
    """List all images for a Podman service."""
    query = {}
    if all_:
        query["all"] = True
    response = api.get("/containers/json", query)
    return json.loads(str(response.read(), "utf-8"))


__all__ = [
    "list_containers",
]
