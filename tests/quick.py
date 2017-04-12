# -*- coding: utf-8 -*-

"""A quicker profile than all.

This profile filters out a number of very slow tests, and tests that are very
exhaustively tested, since they add a good deal of runtime to piglit.

There are 18000+ auto-generated tests that are exhaustive, but for quick.py we
don't want that level of exhaustiveness, so this filter removes 80% in a random
(but deterministic) way.
"""

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)
import random

from framework import grouptools
from framework.test import (GleanTest, PiglitGLTest)
from tests.all import profile as _profile

__all__ = ['profile']

# See the note in all.py about this warning
# pylint: disable=bad-continuation


class FilterVsIn(object):
    """Filter out 80% of the Vertex Attrib 64 vs_in tests."""

    def __init__(self):
        self.random = random.Random()
        self.random.seed(42)

    def __call__(self, name, _):
        if 'vs_in' in name:
            # 20%
            return self.random.random() <= .2
        return True


profile = _profile.copy('OpenGL: Piglit Quick')  # pylint: disable=invalid-name

GleanTest.GLOBAL_PARAMS += ["--quick"]

# Set the --quick flag on a few image_load_store_tests
with profile.test_list.group_manager(
        PiglitGLTest,
        grouptools.join('spec', 'arb_shader_image_load_store')) as g:
    with profile.test_list.allow_reassignment:
        g(['arb_shader_image_load_store-coherency', '--quick'], 'coherency')
        g(['arb_shader_image_load_store-host-mem-barrier', '--quick'],
          'host-mem-barrier')
        g(['arb_shader_image_load_store-max-size', '--quick'], 'max-size')
        g(['arb_shader_image_load_store-semantics', '--quick'], 'semantics')
        g(['arb_shader_image_load_store-shader-mem-barrier', '--quick'],
          'shader-mem-barrier')

# Set the --quick flag on the image_size test
with profile.test_list.group_manager(
        PiglitGLTest,
        grouptools.join('spec', 'arb_shader_image_size')) as g:
    with profile.test_list.allow_reassignment:
        g(['arb_shader_image_size-builtin', '--quick'], 'builtin')

# These take too long
profile.filters.append(lambda n, _: '-explosion' not in n)
profile.filters.append(FilterVsIn())
