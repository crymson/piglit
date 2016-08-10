# Copyright (c) 2015 Intel Corporation

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

"""Piglit integration for Khronos CTS tests.

By default this will run GLES2, GLES3, GLES31, and GLESEXT test cases. Those
desiring to run only a subset of them should consider using the -t or -x
options to include or exclude tests.

For example:
./piglit run cts_gles -c foo -t ES3- would run only ES3 tests (note the dash to
exclude ES31 tests)

This integration requires some configuration in piglit.conf, or the use of
environment variables.

In piglit.conf one should set the following:
[cts_gles]:bin -- Path to the glcts binary
[cts_gles]:extra_args -- any extra arguments to be passed to cts (optional)

Alternatively (or in addition, since environment variables have precedence),
one could set:
PIGLIT_CTS_GLES_BIN -- environment equivalent of [cts_gles]:bin
PIGLIT_CTS_GLES_EXTRA_ARGS -- environment equivalent of [cts_gles]:extra_args

"""

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)
import itertools

from framework.test import deqp

__all__ = ['profile']

_CTS_BIN = deqp.get_option('PIGLIT_CTS_GLES_BIN', ('cts_gles', 'bin'),
                           required=True)

_EXTRA_ARGS = deqp.get_option('PIGLIT_CTS_GLES_EXTRA_ARGS',
                              ('cts_gles', 'extra_args'),
                              default='').split()


class _CTSMixin(object):
    """Mixin that provides the shared bits for the GL CTS class."""

    deqp_bin = _CTS_BIN

    @property
    def extra_args(self):
        return super(_CTSMixin, self).extra_args + \
            [x for x in _EXTRA_ARGS if not x.startswith('--deqp-case')]


class DEQPCTSSingleTest(_CTSMixin, deqp.DEQPSingleTest):
    """Class For running the GL CTS tests in a one test per process mode."""
    pass


class DEQPCTSGroupTest(_CTSMixin, deqp.DEQPGroupTest):
    """Class For running the GL CTS tests in a multiple tests per process mode.
    """
    pass


# Add all of the suites by default, users can use filters to remove them.
profile = deqp.make_profile(  # pylint: disable=invalid-name
    itertools.chain(
        deqp.iter_deqp_test_cases(
            deqp.gen_caselist_txt(_CTS_BIN, 'ES2-CTS-cases.txt', _EXTRA_ARGS)),
        deqp.iter_deqp_test_cases(
            deqp.gen_caselist_txt(_CTS_BIN, 'ES3-CTS-cases.txt', _EXTRA_ARGS)),
        deqp.iter_deqp_test_cases(
            deqp.gen_caselist_txt(_CTS_BIN, 'ES31-CTS-cases.txt', _EXTRA_ARGS)),
        deqp.iter_deqp_test_cases(
            deqp.gen_caselist_txt(_CTS_BIN, 'ESEXT-CTS-cases.txt',
                                  _EXTRA_ARGS)),
    ),
    single=DEQPCTSSingleTest, group=DEQPCTSGroupTest)
