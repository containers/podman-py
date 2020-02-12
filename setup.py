import setuptools

long_description = "Python bindings to manage containers using Podman's new RESTful API."
setuptools.setup(
    name="podman",
    version="0.0.1",
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
    install_requires=[
        'requests >= 2.14.2, != 2.18.0',
    ]
)
