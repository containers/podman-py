Podman: Python scripting for Podman services
==============================================
.. image:: https://img.shields.io/pypi/l/podman.svg
    :target: https://pypi.org/project/podman/

.. image:: https://img.shields.io/pypi/wheel/podman.svg
    :target: https://pypi.org/project/podman/

.. image:: https://img.shields.io/pypi/pyversions/podman.svg
    :target: https://pypi.org/project/podman/

PodmanPy is a Python3 module that allows you to write Python scripts that access resources
maintained by a Podman service. It leverages the Podman service RESTful API.

Podman services are addressed using a URL where the scheme signals to the client how to connect to
service. Supported schemes are: ``http+ssh``, ``http+unix`` or ``tcp``. Formats are the following styles:

 - ``http+ssh://[<login>@]<hostname>[:<port>]/<full filesystem path>``

   - ``http+ssh://alice@api.example:22/run/user/1000/podman/podman.sock``
   - The scheme ``ssh`` is excepted as an alias

 - ``http+unix://<full filesystem path>``

   - ``http+unix:///run/podman/podman.sock``
   - The scheme ``unix`` is excepted as an alias

 - ``tcp://<hostname>:<port>``

   - ``tcp://api.example:8888``

Example
-------
.. code-block:: python
   :linenos:

    import podman

    with podman.Client() as client:
        if client.ping():
            images = client.images.list()
            for image in images:
                print(image.id)

.. toctree::
   :caption: Podman Client
   :maxdepth: 2

   podman.client

.. toctree::
   :caption: Podman Entities
   :glob:
   :hidden:

   podman.domain.containers
   podman.domain.containers_manager
   podman.domain.images
   podman.domain.images_manager
   podman.domain.events*
   podman.domain.manifests*
   podman.domain.networks*
   podman.domain.pods*
   podman.domain.secrets*
   podman.domain.system*
   podman.domain.volume*
   podman.errors.exceptions

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
