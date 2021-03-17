import setuptools

import podman

long_description = "Python bindings to manage containers using Podman's new RESTful API."
setuptools.setup(
    name="podman",
    version=podman.__version__,
    author="Brent Baude",
    author_email="bbaude@redhat.com",
    description="bindings for Podman V2 API",
    long_description=long_description,
    url="https://github.com/containers/podman-py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
