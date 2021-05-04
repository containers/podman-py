#!/usr/bin/env python3
import podman

with podman.PodmanClient() as client:
    print("** Check Service Available")
    if client.ping():
        print("Service active")
    else:
        print(f"No service found @ {client.base_url}")

    print("\n** Print out some versions")
    version_report = client.version()
    print("Service Version: ", version_report["Version"])
    print("Service API: ", version_report["Components"][0]["Details"]["APIVersion"])
    print("Minimal API: ", version_report["Components"][0]["Details"]["MinAPIVersion"])

    print("\n** Pull latest alpine Image")
    image = client.images.pull("quay.io/libpod/alpine", tag="latest")
    print(image, image.id)
    image = client.images.pull("quay.io/libpod/alpine:latest")

    print("\n** Create Pod")
    pod = client.pods.create("demo_pod")
    print(pod, pod.name)

    print("\n** Create Container in Pod")
    container = client.containers.create(image, pod=pod)
    print(container, container.name, "Pod Id:", container.attrs["Pod"][:17])

    print("\n** Remove Pod and Container")
    pod.remove(force=True)

    print("\n** Remove Image and report existing Images")
    client.images.remove(image, force=True)
    for image in client.images.list():
        print("Image: ", ", ".join(image.tags))
