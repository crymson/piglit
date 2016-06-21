# Copyright (c) 2013-2014 Intel Corporation
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# This permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHOR(S) BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
# AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF
# OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

""" Test integreation for the X Test Suite """

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)
import os
import re
import subprocess
import itertools

from framework import grouptools, exceptions, core
from framework.options import OPTIONS
from framework.profile import TestProfile, Test

__all__ = ['profile']

X_TEST_SUITE = core.PIGLIT_CONFIG.required_get('xts', 'path')


class XTSProfile(TestProfile):  # pylint: disable=too-few-public-methods
    """ A subclass of TestProfile that provides a setup hook for XTS """
    def _pre_run_hook(self):
        """ This hook sets the XTSTest.results_path variable

        Setting this variable allows images created by XTS to moved into the
        results directory

        """
        try:
            os.mkdir(os.path.join(OPTIONS.result_dir, 'images'))
        except OSError as e:
            # If the exception is not 'directory already exists', raise the
            # exception
            if e.errno != 17:
                raise


class XTSTest(Test):  # pylint: disable=too-few-public-methods
    """ X Test Suite class

    Runs a single test or subtest from XTS.

    Arguments:
    name -- the name of the test
    testname -- the name of the test file
    testnum -- the number of the test file

    """
    def __init__(self, name, testname, testnum):
        super(XTSTest, self).__init__(
            ['./' + os.path.basename(name), '-i', str(testnum)])
        self.testname = '{0}-{1}'.format(testname, testnum)
        self.cwd = os.path.dirname(os.path.realpath(name))
        self.test_results_file = os.path.join(self.cwd, self.testname)
        self.env.update(
            {"TET_RESFILE": self.test_results_file,
             "XT_RESET_DELAY": '0',
             "XT_FONTPATH_GOOD": '/usr/share/fonts/X11/misc',
             "XT_FONTPATH": os.path.join(X_TEST_SUITE, 'xts5', 'fonts'),
             # XXX: Are the next 3 necissary?
             "XT_LOCAL": 'Yes',
             "XT_TCP": 'No',
             "XT_DISPLAYHOST": ''})

    def _process_log_for_images(self, log):
        """ Parse the image logfile """
        images = []
        search = re.compile('See file (Err[0-9]+.err)')

        for line in log.splitlines():
            match = search.search(line)
            if match is not None:
                # Can we parse any other useful information out to give a
                # better description of each image?
                desc = match.group(1)

                # The error logs are text, with a header with width, height,
                # and depth, then run-length-encoded pixel values (in
                # hexadecimal).  Use xtsttopng to convert the error log to a
                # pair of PNGs so we can put them in the summary.
                command = ['xtsttopng', os.path.join(self.cwd, match.group(1))]
                try:
                    out = subprocess.check_output(command, cwd=self.cwd)
                except OSError:
                    images.append({'image_desc': 'image processing failed'})
                    continue

                # Each Err*.err log contains a rendered image, and a reference
                # image that it was compared to.  We relocate the to our tree
                # with more useful names.  (Otherwise, since tests generate
                # error logs with numbers sequentially starting from 0, each
                # subtest with an error would overwrite the previous test's
                # images).
                ref_path = os.path.join(
                    OPTIONS.result_dir, 'images', '{1}-{2}-ref.png'.format(
                        self.testname, match.group(1)))
                render_path = os.path.join(
                    OPTIONS.result_dir, 'images', '{1}-{2}-render.png'.format(
                        self.testname, match.group(1)))

                split = out.splitlines()
                os.rename(os.path.join(self.cwd, split[0]), render_path)
                os.rename(os.path.join(self.cwd, split[1]), ref_path)

                images.append({'image_desc': desc,
                               'image_ref': ref_path,
                               'image_render': render_path})

        return images

    def interpret_result(self):
        super(XTSTest, self).interpret_result()

        try:
            with open(self.test_results_file, 'r') as rfile:
                log = rfile.read()
                self.result.out = log
                os.remove(self.test_results_file)
        except IOError:
            self.result.err = "No results file found"

        if self.result.returncode == 0:
            if re.search('FAIL', self.result.out) is not None:
                self.result.result = 'fail'
            elif re.search('PASS', self.result.out) is not None:
                self.result.result = 'pass'
            else:
                self.result.result = 'fail'
        elif self.result.returncode == 77:
            self.result.result = 'skip'
        elif self.result.returncode == 1:
            if re.search('Could not open all VSW5 fonts', log):
                self.result.result = 'warn'
            else:
                self.result.result = 'fail'

        self.result.images = self._process_log_for_images(log)


class RendercheckTest(Test):
    def __init__(self, args):
        super(RendercheckTest, self).__init__(['rendercheck'] + args)
        self.testname = "rendercheck " + " ".join(args)

    def interpret_result(self):
        super(RendercheckTest, self).interpret_result()

        if self.result.returncode == 0:
            self.result.result = 'pass'
        elif self.result.returncode == 77:
            self.result.result = 'skip'


def _populate_profile_xts(profile):
    fpath = os.path.join(X_TEST_SUITE, 'xts5')
    for dirpath, _, filenames in os.walk(fpath):
        for fname in filenames:
            # only look at the .m test files
            testname, ext = os.path.splitext(fname)
            if ext != '.m':
                continue

            # incrementing number generator
            counts = itertools.count(start=1)

            # Walk the file looking for >>ASSERTION, each of these corresponds
            # to a generated subtest, there can be multiple subtests per .m
            # file
            with open(os.path.join(dirpath, fname), 'r') as rfile:
                for line in rfile:
                    if line.startswith('>>ASSERTION'):
                        num = next(counts)
                        group = grouptools.join(
                            grouptools.from_path(
                                os.path.relpath(dirpath, X_TEST_SUITE)),
                            testname, str(num))

                        profile.test_list[group] = XTSTest(
                            os.path.join(dirpath, testname),
                            testname,
                            num)


def _add_rendercheck_test(profile, path, args):
    test = RendercheckTest(args.split(' '))
    group_path = 'rendercheck/' + path
    group = grouptools.join(*(group_path.split('/')))
    profile.test_list[group] = test


def _populate_profile_rendercheck(profile):
    _add_rendercheck_test(profile, 'blend/All/a8r8g8b8', '-t blend -f a8r8g8b8')
    _add_rendercheck_test(profile, 'blend/All/x8r8g8b8', '-t blend -f a8r8g8b8,x8r8g8b8')
    _add_rendercheck_test(profile, 'blend/All/a2r10g10b10', '-t blend -f a8r8g8b8,a2r10g10b10')
    _add_rendercheck_test(profile, 'blend/Clear', '-t blend -o clear')
    _add_rendercheck_test(profile, 'blend/Src', '-t blend -o src')
    _add_rendercheck_test(profile, 'blend/Over', '-t blend -o over')
    _add_rendercheck_test(profile, 'composite/All/a8r8g8b8', '-t composite -f a8r8g8b8')
    _add_rendercheck_test(profile, 'composite/All/x8r8g8b8', '-t composite -f a8r8g8b8,x8r8g8b8')
    _add_rendercheck_test(profile, 'composite/All/a2r10g10b10', '-t composite -f a8r8g8b8,a2r10g10b10')
    _add_rendercheck_test(profile, 'ca composite/All/a8r8g8b8', '-t cacomposite -f a8r8g8b8')
    _add_rendercheck_test(profile, 'ca composite/All/a8', '-t cacomposite -f a8r8g8b8,a8')
    _add_rendercheck_test(profile, 'ca composite/All/x8r8g8b8', '-t cacomposite -f a8r8g8b8,x8r8g8b8')
    _add_rendercheck_test(profile, 'ca composite/All/a2r10g10b10', '-t cacomposite -f a8r8g8b8,a2r10g10b10')
    _add_rendercheck_test(profile, 'fill', '-t fill')
    _add_rendercheck_test(profile, 'bug7366', '-t bug7366')
    _add_rendercheck_test(profile, 'destination coordinates', '-t dcoords')
    _add_rendercheck_test(profile, 'source coordinates', '-t scoords')
    _add_rendercheck_test(profile, 'mask coordinates', '-t mcoords')
    _add_rendercheck_test(profile, 'translated source coordinates', '-t tscoords')
    _add_rendercheck_test(profile, 'translated mask coordinates', '-t tmcoords')
    _add_rendercheck_test(profile, 'triangles', '-t triangles')
    _add_rendercheck_test(profile, 'LibreOffice xRGB', '-t libreoffice_xrgb')
    _add_rendercheck_test(profile, 'GTK ARGB vs xBGR', '-t gtk_argb_xbgr')
    _add_rendercheck_test(profile, 'large blend source', '-t large_blend_src')


def _populate_profile():
    """ Populate the profile attribute """
    # Add all tests to the profile
    profile = XTSProfile()  # pylint: disable=redefined-outer-name
    _populate_profile_xts(profile)
    _populate_profile_rendercheck(profile)
    return profile


if not os.path.exists(X_TEST_SUITE):
    raise exceptions.PiglitFatalError('XTest suite not found.')

profile = _populate_profile()  # pylint: disable=invalid-name
