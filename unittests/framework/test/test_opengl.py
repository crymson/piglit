# Copyright (c) 2015-2016 Intel Corporation

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

"""Test the opengl module."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)
import operator
import subprocess
import textwrap
try:
    from unittest import mock
except ImportError:
    import mock

import pytest

from framework.test import opengl
from framework.test.base import TestIsSkip as _TestIsSkip

from .. import utils

# pylint: disable=no-self-use,attribute-defined-outside-init,protected-access
# pylint: disable=invalid-name


def _has_wflinfo():
    """Return True if wflinfo is available in PATH."""
    try:
        subprocess.check_call(['wflinfo', '--help'])
    except subprocess.CalledProcessError:
        return False
    except OSError as e:
        if e.errno != 2:
            raise
        return False
    return True


@pytest.mark.skipif(not _has_wflinfo(), reason="Tests require wflinfo binary.")
class TestWflInfo(object):
    """Tests for the WflInfo class."""

    class TestAttributes(object):
        """test for attribute assignments."""

        @pytest.yield_fixture(autouse=True)
        def patch(self):
            """Mock a few things for testing purposes."""
            # This is pretty ugly, but as a Borb with a private shared state,
            # the only way to test this module is to actually replace the
            # shared_state with a mock value so it's reset after each test
            with mock.patch.dict('framework.test.opengl.OPTIONS.env',
                                 {'PIGLIT_PLATFORM': 'foo'}), \
                    mock.patch(
                        'framework.test.opengl.WflInfo._WflInfo__shared_state',
                        {}):
                yield

        def setup(self):
            """Setup each instance, patching necissary bits."""
            self._test = opengl.WflInfo()

        def test_gl_extension(self):
            """test.opengl.WflInfo.gl_extensions: Provides list of gl
            extensions.
            """
            rv = (b'foo\nbar\nboink\nOpenGL extensions: '
                  b'GL_foobar GL_ham_sandwhich\n')
            expected = set(['GL_foobar', 'GL_ham_sandwhich'])

            with mock.patch('framework.test.opengl.subprocess.check_output',
                            mock.Mock(return_value=rv)):
                assert self._test.gl_extensions == expected

        def test_gl_version(self):
            """test.opengl.WflInfo.gl_version: Provides a version number."""
            rv = textwrap.dedent("""\
                Waffle platform: gbm
                Waffle api: gl
                OpenGL vendor string: Intel Open Source Technology Center
                OpenGL renderer string: Mesa DRI Intel(R) Haswell Mobile
                OpenGL version string: 18 (Core Profile) Mesa 11.0.4
                OpenGL context flags: 0x0
            """).encode('utf-8')
            with mock.patch('framework.test.opengl.subprocess.check_output',
                            mock.Mock(return_value=rv)):
                assert self._test.gl_version == 18.0

        def test_gles_version(self):
            """test.opengl.WflInfo.gles_version: Provides a version number."""
            rv = textwrap.dedent("""\
                Waffle platform: gbm
                Waffle api: gles3
                OpenGL vendor string: Intel Open Source Technology Center
                OpenGL renderer string: Mesa DRI Intel(R) Haswell Mobile
                OpenGL version string: OpenGL ES 7.1 Mesa 11.0.4
            """).encode('utf-8')
            with mock.patch('framework.test.opengl.subprocess.check_output',
                            mock.Mock(return_value=rv)):
                assert self._test.gles_version == 7.1

        def test_glsl_version(self):
            """test.opengl.WflInfo.glsl_version: Provides a version number."""
            rv = textwrap.dedent("""\
                Waffle platform: gbm
                Waffle api: gl
                OpenGL vendor string: Intel Open Source Technology Center
                OpenGL renderer string: Mesa DRI Intel(R) Haswell Mobile
                OpenGL version string: 1.1 (Core Profile) Mesa 11.0.4
                OpenGL context flags: 0x0
                OpenGL shading language version string: 9.30
                OpenGL extensions: this is some extension strings.
            """).encode('utf-8')
            with mock.patch('framework.test.opengl.subprocess.check_output',
                            mock.Mock(return_value=rv)):
                assert self._test.glsl_version == 9.3

        def test_glsl_es_version_1(self):
            """test.opengl.WflInfo.glsl_es_version: works with gles2."""
            rv = textwrap.dedent("""\
                Waffle platform: gbm
                Waffle api: gles2
                OpenGL vendor string: Intel Open Source Technology Center
                OpenGL renderer string: Mesa DRI Intel(R) Haswell Mobile
                OpenGL version string: OpenGL ES 3.0 Mesa 11.0.4
                OpenGL shading language version string: OpenGL ES GLSL ES 1.0.17
                OpenGL extensions: this is some extension strings.
            """).encode('utf-8')
            with mock.patch('framework.test.opengl.subprocess.check_output',
                            mock.Mock(return_value=rv)):
                assert self._test.glsl_es_version == 1.0

        def test_glsl_es_version_3plus(self):
            """test.opengl.WflInfo.glsl_es_version: works with gles3."""
            rv = textwrap.dedent("""\
                Waffle platform: gbm
                Waffle api: gles3
                OpenGL vendor string: Intel Open Source Technology Center
                OpenGL renderer string: Mesa DRI Intel(R) Haswell Mobile
                OpenGL version string: OpenGL ES 3.0 Mesa 11.0.4
                OpenGL shading language version string: OpenGL ES GLSL ES 5.00
                OpenGL extensions: this is some extension strings.
            """).encode('utf-8')
            with mock.patch('framework.test.opengl.subprocess.check_output',
                            mock.Mock(return_value=rv)):
                assert self._test.glsl_es_version == 5.0

        def test_gl_version_patch(self):
            """test.opengl.WflInfo.gl_version: Works with patch versions."""
            rv = textwrap.dedent("""\
                Waffle platform: gbm
                Waffle api: gl
                OpenGL vendor string: Intel Open Source Technology Center
                OpenGL renderer string: Mesa DRI Intel(R) Haswell Mobile
                OpenGL version string: 18.0.1 (Core Profile) Mesa 11.0.4
                OpenGL context flags: 0x0
            """).encode('utf-8')
            with mock.patch('framework.test.opengl.subprocess.check_output',
                            mock.Mock(return_value=rv)):
                assert self._test.gl_version == 18.0

        def test_glsl_version_patch(self):
            """test.opengl.WflInfo.glsl_version: Works with patch versions."""
            rv = textwrap.dedent("""\
                Waffle platform: gbm
                Waffle api: gl
                OpenGL vendor string: Intel Open Source Technology Center
                OpenGL renderer string: Mesa DRI Intel(R) Haswell Mobile
                OpenGL version string: 1.1 (Core Profile) Mesa 11.0.4
                OpenGL context flags: 0x0
                OpenGL shading language version string: 9.30.7
                OpenGL extensions: this is some extension strings.
            """).encode('utf-8')
            with mock.patch('framework.test.opengl.subprocess.check_output',
                            mock.Mock(return_value=rv)):
                assert self._test.glsl_version == 9.3

        def test_leading_junk(self):
            """test.opengl.WflInfo.gl_version: Handles leading junk."""
            rv = textwrap.dedent("""\
                Warning: I'm a big fat warnngs
                Waffle platform: gbm
                Waffle api: gl
                OpenGL vendor string: Intel Open Source Technology Center
                OpenGL renderer string: Mesa DRI Intel(R) Haswell Mobile
                OpenGL version string: 18.0.1 (Core Profile) Mesa 11.0.4
                OpenGL context flags: 0x0
            """).encode('utf-8')
            with mock.patch('framework.test.opengl.subprocess.check_output',
                            mock.Mock(return_value=rv)):
                assert self._test.gl_version == 18.0

        def test_mixed_junk(self):
            """test.opengl.WflInfo.gl_version: Handles mixed junk."""
            rv = textwrap.dedent("""\
                Waffle platform: gbm
                Waffle api: gl
                Warning: I'm a big fat warnngs
                OpenGL vendor string: Intel Open Source Technology Center
                OpenGL renderer string: Mesa DRI Intel(R) Haswell Mobile
                Warning: I'm a big fat warnngs
                Warning: I'm a big fat warnngs
                OpenGL version string: 18.0.1 (Core Profile) Mesa 11.0.4
                OpenGL context flags: 0x0
            """).encode('utf-8')
            with mock.patch('framework.test.opengl.subprocess.check_output',
                            mock.Mock(return_value=rv)):
                assert self._test.gl_version == 18.0

    class TestWAFFLEINFO_GL_ERROR(object):
        """Test class for WflInfo when "WFLINFO_GL_ERROR" is returned."""

        @pytest.yield_fixture(autouse=True)
        def patch(self):
            """Setup each instance, patching necissary bits."""
            rv = textwrap.dedent("""\
                Waffle platform: glx
                Waffle api: gles3
                OpenGL vendor string: WFLINFO_GL_ERROR
                OpenGL renderer string: Mesa DRI Intel(R) Haswell Mobile
                OpenGL version string: WFLINFO_GL_ERROR
                OpenGL context flags: 0x0\n
                OpenGL shading language version string: WFLINFO_GL_ERROR
                OpenGL extensions: WFLINFO_GL_ERROR
            """).encode('utf-8')

            with mock.patch.dict('framework.test.opengl.OPTIONS.env',
                                 {'PIGLIT_PLATFORM': 'foo'}), \
                    mock.patch(
                        'framework.test.opengl.subprocess.check_output',
                        mock.Mock(return_value=rv)):
                yield

        @pytest.fixture(scope='class')
        def inst(self):
            return opengl.WflInfo()

        def test_gl_version(self, inst):
            """test.opengl.WflInfo.gl_version: handles WFLINFO_GL_ERROR
            correctly.
            """
            assert inst.gl_version is None

        def test_gles_version(self, inst):
            """test.opengl.WflInfo.gles_version: handles WFLINFO_GL_ERROR
            correctly.
            """
            assert inst.gles_version is None

        def test_glsl_version(self, inst):
            """test.opengl.WflInfo.glsl_version: handles WFLINFO_GL_ERROR
            correctly.
            """
            assert inst.glsl_version is None

        def test_glsl_es_version(self, inst):
            """test.opengl.WflInfo.glsl_es_version: handles WFLINFO_GL_ERROR
            correctly.
            """
            assert inst.glsl_es_version is None

        def test_gl_extensions(self, inst):
            """test.opengl.WflInfo.gl_extensions: handles WFLINFO_GL_ERROR
            correctly.
            """
            assert inst.gl_extensions == set()

    class TestOSError(object):
        """Tests for the Wflinfo functions to handle OSErrors."""

        # pylint: disable=pointless-statement

        @pytest.yield_fixture(autouse=True, scope='class')
        def patch(self):
            """Setup the class, patching as necessary."""
            # pylint: disable=bad-continuation
            with mock.patch.dict(
                    'framework.test.opengl.OPTIONS.env',
                    {'PIGLIT_PLATFORM': 'foo'}), \
                    mock.patch(
                        'framework.test.opengl.subprocess.check_output',
                        mock.Mock(side_effect=OSError(2, 'foo'))), \
                    mock.patch(
                        'framework.test.opengl.WflInfo._WflInfo__shared_state',
                        {}):
                yield

        @pytest.fixture
        def inst(self):
            return opengl.WflInfo()

        def test_gl_extensions(self, inst):
            """test.opengl.WflInfo.gl_extensions: Handles OSError "no file"
            gracefully.
            """
            inst.gl_extensions

        def test_gl_version(self, inst):
            """test.opengl.WflInfo.get_gl_version: Handles OSError "no file"
            gracefull.
            """
            inst.gl_version

        def test_gles_version(self, inst):
            """test.opengl.WflInfo.get_gles_version: Handles OSError "no file"
            gracefully.
            """
            inst.gles_version

        def test_glsl_version(self, inst):
            """test.opengl.WflInfo.glsl_version: Handles OSError "no file"
            gracefully.
            """
            inst.glsl_version

        def test_glsl_es_version(self, inst):
            """test.opengl.WflInfo.glsl_es_version: Handles OSError "no file"
            gracefully.
            """
            inst.glsl_es_version

    class TestCalledProcessError(object):
        """Tests for the WflInfo functions to handle OSErrors."""

        # pylint: disable=pointless-statement

        @pytest.yield_fixture(autouse=True, scope='class')
        def patch(self):
            """Setup the class, patching as necessary."""
            # pylint: disable=bad-continuation
            with mock.patch.dict(
                    'framework.test.opengl.OPTIONS.env',
                    {'PIGLIT_PLATFORM': 'foo'}), \
                    mock.patch(
                        # pylint: disable=line-too-long
                        'framework.test.opengl.subprocess.check_output',
                        mock.Mock(side_effect=subprocess.CalledProcessError(1, 'foo'))), \
                    mock.patch(
                        'framework.test.opengl.WflInfo._WflInfo__shared_state',
                        {}):
                yield

        @pytest.fixture
        def inst(self):
            return opengl.WflInfo()

        def test_gl_extensions(self, inst):
            """test.opengl.WflInfo.gl_extensions: Handles CalledProcessError
            gracefully.
            """
            inst.gl_extensions

        def test_gl_version(self, inst):
            """test.opengl.WflInfo.get_gl_version: Handles CalledProcessError
            gracefully.
            """
            inst.gl_version

        def test_gles_version(self, inst):
            """test.opengl.WflInfo.gles_version: Handles CalledProcessError
            gracefully.
            """
            inst.gles_version

        def test_glsl_version(self, inst):
            """test.opengl.WflInfo.glsl_version: Handles CalledProcessError
            gracefully.
            """
            inst.glsl_version

        def test_glsl_es_version(self, inst):
            """test.opengl.WflInfo.glsl_es_version: Handles CalledProcessError
            gracefully.
            """
            inst.glsl_es_version


class TestFastSkipMixin(object):  # pylint: disable=too-many-public-methods
    """Tests for the FastSkipMixin class."""

    class _Test(opengl.FastSkipMixin, utils.Test):
        pass

    @pytest.fixture
    def inst(self):
        return self._Test(['foo'])

    @pytest.yield_fixture(autouse=True, scope='module')
    def patch(self):
        """Create a Class with FastSkipMixin, but patch various bits."""
        _mock_wflinfo = mock.Mock(spec=opengl.WflInfo)
        _mock_wflinfo.gl_version = 3.3
        _mock_wflinfo.gles_version = 3.0
        _mock_wflinfo.glsl_version = 3.3
        _mock_wflinfo.glsl_es_version = 2.0
        _mock_wflinfo.gl_extensions = set(['bar'])

        with mock.patch.object(self._Test, '_FastSkipMixin__info',
                               _mock_wflinfo):
            yield

    def test_api(self):
        """Tests that the api works.

        Since you're not suppoed to be able to pass gl and gles version, this
        uses two seperate constructor calls.
        """
        self._Test(['foo'], gl_required={'foo'}, gl_version=3, glsl_version=2)
        self._Test(['foo'], gl_required={'foo'}, gles_version=3,
                   glsl_es_version=2)

    def test_should_skip(self, inst):
        """test.opengl.FastSkipMixin.is_skip: Skips when requires is missing
        from extensions.
        """
        inst.gl_required.extensions.add('foobar')
        with pytest.raises(_TestIsSkip):
            inst.is_skip()

    def test_should_not_skip(self, inst):
        """test.opengl.FastSkipMixin.is_skip: runs when requires is in
        extensions.
        """
        inst.gl_required.extensions.add('bar')
        inst.is_skip()


class TestExtensionSkip(object):
    """Tests for the ExtensionSkip class."""

    def test_extension_empty(self):
        """If extensions pased to .test() are empty don't raise."""
        inst = opengl.ExtensionsSkip()
        inst.test(set())

    def test_requires_empty(self):
        inst = opengl.ExtensionsSkip()
        inst.test(['bar'])

    def test_in(self):
        inst = opengl.ExtensionsSkip(['bar'])
        inst.test(['bar'])

    def test_not_in(self):
        inst = opengl.ExtensionsSkip(['foo'])
        with pytest.raises(opengl.FastSkip):
            inst.test(['bar'])


def _version_name(val):
    if isinstance(val, (float, bool)):
        return val
    return val.__name__


class TestVersionSkip(object):
    """Tests for the version skip class."""

    @pytest.mark.parametrize('op, required, available, skip', [
        (operator.ge, 3.0, 2.0, True),
        (operator.ge, 3.0, 3.0, False),
        (operator.ge, 3.0, 4.0, False),
        (operator.gt, 3.0, 2.0, True),
        (operator.gt, 3.0, 3.0, True),
        (operator.gt, 3.0, 4.0, False),
        (operator.eq, 3.0, 2.0, True),
        (operator.eq, 3.0, 3.0, False),
        (operator.eq, 3.0, 4.0, True),
        (operator.lt, 3.0, 2.0, False),
        (operator.lt, 3.0, 3.0, True),
        (operator.lt, 3.0, 4.0, True),
        (operator.le, 3.0, 2.0, False),
        (operator.le, 3.0, 3.0, False),
        (operator.le, 3.0, 4.0, True),
    ], ids=_version_name)
    def test_version(self, op, required, available, skip):
        inst = opengl.VersionSkip(op, required)
        if skip:
            with pytest.raises(opengl.FastSkip):
                inst.test(available)
        else:
            inst.test(available)

    def test_version_unset(self):
        inst = opengl.VersionSkip(operator.lt, 3.0)
        inst.test(None)


class TestFastSkipMixinDisabled(object):
    """Tests for the sub version."""

    @pytest.yield_fixture(autouse=True, scope='class')
    def patch(self):
        """Create a Class with FastSkipMixin, but patch various bits."""
        _mock_wflinfo = mock.Mock(spec=opengl.WflInfo)
        _mock_wflinfo.gl_version = 3.3
        _mock_wflinfo.gles_version = 3.0
        _mock_wflinfo.glsl_version = 3.3
        _mock_wflinfo.glsl_es_version = 2.0
        _mock_wflinfo.gl_extensions = set(['bar'])

        with mock.patch.object(self._Test, '_FastSkipMixin__info',
                               _mock_wflinfo):
            yield

    class _Test(opengl.FastSkipMixin, utils.Test):
        pass

    def test_api(self):
        """Tests that the api works.

        Since you're not suppoed to be able to pass gl and gles version, this
        uses two seperate constructor calls.
        """
        self._Test(['foo'], gl_required={'foo'}, gl_version=3, glsl_version=2)
        self._Test(['foo'], gl_required={'foo'}, gles_version=3,
                   glsl_es_version=2)
