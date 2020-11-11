# Welcome to Podman-Py

This python package is a set of bindings to use the new RESTful API in
[podman](https://github.com/containers/podman).  It is currently under
development and contributors are welcome!


## Project layout

```
.
├── bors.toml               // merge conflict checker
├── contrib                 // additional tooling related stuff
├── docs                    // documentation for this project
├── Makefile                // how to build stuff
├── mkdocs.yml              // documentation generator config for ReadTheDocs
├── podman                  // the actual source code
│   ├── api_connection.py   // the main class that connects to the libpod api
│   ├── errors              // error handling
│   ├── images              // interact with the images stored on your system
│   ├── pods                // interact with pods
│   ├── system              // info and management of podman<->OS integration, config, data storage etc.
│   └── tests               // automated tests, e.g. unit tests
├── README.md               // the github landing page info text
├── setup.py                // python packaging related config
├── tox.ini                 // automated test configuration
└── test-requirements.txt   // which packages to install to run the tests
```

## Architecture

As the current idea is basically a python wrapping around the libpod API,
there will be one main wrapper class `APIConnection` and helper functions
which can be used almost like the
[podman](https://github.com/containers/podman) CLI while generating the correct
API queries for the user under the hood.

As network connection management requires some statefulness the `ApiConnection`
object is built as a context manager and is expected to be used in a `with`
block, so Python can take care of the cleanup for the user.
