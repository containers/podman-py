# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

from sphinx.domains.python import PythonDomain

sys.path.insert(0, os.path.abspath('../..'))


# -- Project information -----------------------------------------------------

project = 'Podman Python SDK'
copyright = '2021, Red Hat Inc'
author = 'Red Hat Inc'

# The full version, including alpha/beta/rc tags
version = '3.2.1.0'
release = version

add_module_names = False

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
# sphinx.ext.autodoc: Include documentation from docstrings
# sphinx.ext.napoleon: Support for NumPy and Google style docstrings
# sphinx.ext.viewcode: Add links to highlighted source code
# isort: unique-list
extensions = ['sphinx.ext.napoleon', 'sphinx.ext.autodoc', 'sphinx.ext.viewcode']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
# isort: unique-list
exclude_patterns = [
    'podman.api.*rst',
    'podman.rst',
    'podman.version.rst',
    'podman.tlsconfig.rst',
    'podman.errors.rst',
    'podman.domain.rst',
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'
html_favicon = '_static/podman-logo.ico'
html_theme_options = {
    'description': 'Develop scripted Podman operations',
    'fixed_sidebar': False,
    'github_banner': True,
    'github_repo': 'podman-py',
    'github_user': 'containers',
    'logo': "podman-logo.png",
    'logo_name': True,
    'show_powered_by': False,
    'extra_nav_links': {
        'Report PodmanPy Issue': 'https://github.com/containers/podman-py/issues',
        'Podman Reference': 'https://docs.podman.io',
        'Podman on github': 'https://github.com/containers/podman',
    },
}

html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html',
    ]
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

#  -- autoclass settings ------------------------------------------------------	s
autodoc_member_order = "groupwise"
autodoc_default_options = {
    'members': True,
    'inherited-members': True,
    'show-inheritance': True,
}
autoclass_content = "both"

#  -- Napoleon settings ------------------------------------------------------	s
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True


class PatchedPythonDomain(PythonDomain):
    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        if 'refspecific' in node:
            del node['refspecific']
        return super(PatchedPythonDomain, self).resolve_xref(
            env, fromdocname, builder, typ, target, node, contnode
        )


def skip(app, what, name, obj, would_skip, options):
    # isort: unique-list
    cls = ['ApiConnection', 'DockerClient', 'DockerException']

    if name in cls:
        return True

    return None


def setup(app):
    app.connect("autodoc-skip-member", skip)
    app.add_domain(PatchedPythonDomain, override=True)
