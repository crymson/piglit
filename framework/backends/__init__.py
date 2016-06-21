# Copyright (c) 2014-2016 Intel Corporation

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Provides a module like interface for backends.

This package provides an abstract interface for working with backends, which
implement various functions as provided in the Registry class, and then provide
a Registry instance as REGISTRY, which maps individual objects to objects that
piglit expects to use. This module then provides a thin abstraction layer so
that piglit is never aware of what backend it's using, it just asks for an
object and receives one.

Most consumers will want to import framework.backends and work directly with
the helper functions here. For some more detailed uses (test cases especially)
the modules themselves may be used.

When this module is loaded it will search through framework/backends for python
modules (those ending in .py), and attempt to import them. Then it will look
for an attribute REGISTRY in those modules, and if it as a
framework.register.Registry instance, it will add the name of that module (sans
.py) as a key, and the instance as a value to the BACKENDS dictionary. Each of
the helper functions in this module uses that dictionary to find the function
that a user actually wants.

"""

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)
import os
import importlib

import six

from .register import Registry
from .compression import COMPRESSION_SUFFIXES

__all__ = [
    'BACKENDS',
    'BackendError',
    'BackendNotImplementedError',
    'get_backend',
    'load',
    'set_meta',
]


class BackendError(Exception):
    pass


class BackendNotImplementedError(NotImplementedError):
    pass


def _register():
    """Register backends.

    Walk through the list of backends and register them to a name in a
    dictionary, so that they can be referenced from helper functions.

    """
    registry = {}

    for module in os.listdir(os.path.dirname(os.path.abspath(__file__))):
        module, extension = os.path.splitext(module)
        if extension == '.py':
            mod = importlib.import_module('framework.backends.{}'.format(module))
            if hasattr(mod, 'REGISTRY') and isinstance(mod.REGISTRY, Registry):
                registry[module] = mod.REGISTRY

    return registry


BACKENDS = _register()


def get_backend(backend):
    """Returns a BackendInstance based on the string passed.

    If the backend isn't a known module, then a BackendError will be raised, it
    is the responsibility of the caller to handle this error.

    If the backend module exists, but there is not active implementation then a
    BackendNotImplementedError will be raised, it is also the responsibility of
    the caller to handle this error.

    """
    try:
        inst = BACKENDS[backend].backend
    except KeyError:
        raise BackendError('Unknown backend: {}'.format(backend))

    if inst is None:
        raise BackendNotImplementedError(
            'Backend for {} is not implemented'.format(backend))

    return inst


def load(file_path):
    """Wrapper for loading runs.

    This function will attempt to determine how to load the file (based on file
    extension), and then pass the file path into the appropriate loader, and
    then return the TestrunResult instance.

    """
    def get_extension(file_path):
        """Get the extension name to use when searching for a loader.

        This function correctly handles compression suffixes, as long as they
        are valid.

        """
        def _extension(file_path):
            """Helper function to get the extension string."""
            compression = 'none'
            name, extension = os.path.splitext(file_path)

            # If we hit a compressed suffix, get an additional suffix to test
            # with.
            # i.e: Use .json.gz rather that .gz
            if extension in COMPRESSION_SUFFIXES:
                compression = extension[1:]  # Drop the leading '.'
                # Remove any trailing '.', this fixes a bug where the filename
                # is 'foo.json..xz, or similar
                extension = os.path.splitext(name.rstrip('.'))[1]

            return extension, compression

        if not os.path.isdir(file_path):
            return _extension(file_path)
        else:
            for file_ in os.listdir(file_path):
                if file_.startswith('result') and not file_.endswith('.old'):
                    return _extension(file_)

        tests = os.path.join(file_path, 'tests')
        if os.path.exists(tests):
            return _extension(os.listdir(tests)[0])
        else:
            # At this point we have failed to find any sort of backend, just
            # except and die
            raise BackendError("No backend found for any file in {}".format(
                file_path))

    extension, compression = get_extension(file_path)

    for backend in six.itervalues(BACKENDS):
        if extension in backend.extensions:
            loader = backend.load

            if loader is None:
                raise BackendNotImplementedError(
                    'Loader for {} is not implemented'.format(extension))

            return loader(file_path, compression)

    raise BackendError(
        'No module supports file extensions "{}"'.format(extension))
