# Copyright (c) 2014 Intel Corporation

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

""" Provides test for the framework.profile modules """

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)
import sys
import copy

try:
    from unittest import mock
except ImportError:
    import mock

import nose.tools as nt

from . import utils
from framework import grouptools, dmesg, profile, exceptions, options
from framework.test import GleanTest

# pylint: disable=invalid-name,line-too-long,protected-access

# Don't print sys.stderr to the console
sys.stderr = sys.stdout


@utils.nose.no_error
def test_initialize_testprofile():
    """profile.TestProfile: class initializes"""
    profile.TestProfile()


@nt.raises(exceptions.PiglitFatalError)
def test_load_test_profile_no_profile():
    """profile.load_test_profile: Loading a module with no profile name exits

    Because load_test_profile uses test.{} to load a module we need a module in
    tests that doesn't have a profile attribute. The only module that currently
    meets that requirement is __init__.py

    """
    profile.load_test_profile('__init__')


@nt.raises(exceptions.PiglitFatalError)
def test_load_test_profile_no_module():
    """profile.load_test_profile: Trying to load a non-existant module exits"""
    profile.load_test_profile('this_module_will_never_ever_exist')


def test_load_test_profile_returns():
    """profile.load_test_profile: returns a TestProfile instance"""
    profile_ = profile.load_test_profile('sanity')
    nt.ok_(isinstance(profile_, profile.TestProfile))


def test_testprofile_default_dmesg():
    """profile.TestProfile: Dmesg initializes False"""
    profile_ = profile.TestProfile()
    nt.ok_(isinstance(profile_.dmesg, dmesg.DummyDmesg))


@utils.nose.Skip.platform('linux')
def test_testprofile_set_dmesg_true():
    """profile.TestProfile: Dmesg returns an appropriate dmesg is set to True"""
    profile_ = profile.TestProfile()
    profile_.dmesg = True
    nt.ok_(isinstance(profile_.dmesg, dmesg.LinuxDmesg))


@utils.nose.Skip.platform('linux')
def test_testprofile_set_dmesg_false():
    """profile.TestProfile: Dmesg returns a DummyDmesg if set to False"""
    profile_ = profile.TestProfile()
    profile_.dmesg = True
    profile_.dmesg = False
    nt.ok_(isinstance(profile_.dmesg, dmesg.DummyDmesg))


def test_testprofile_update_test_list():
    """profile.TestProfile.update(): updates TestProfile.test_list"""
    profile1 = profile.TestProfile()
    group1 = grouptools.join('group1', 'test1')
    group2 = grouptools.join('group1', 'test2')

    profile1.test_list[group1] = utils.piglit.Test(['test1'])


    profile2 = profile.TestProfile()
    profile2.test_list[group1] = utils.piglit.Test(['test3'])
    profile2.test_list[group2] = utils.piglit.Test(['test2'])

    with profile1.test_list.allow_reassignment:
        profile1.update(profile2)

    nt.assert_dict_equal(dict(profile1.test_list), dict(profile2.test_list))


class TestPrepareTestListMatches(object):
    """Create tests for TestProfile.prepare_test_list filtering"""
    def __init__(self):
        self.data = profile.TestDict()
        self.data[grouptools.join('group1', 'test1')] = utils.piglit.Test(['thingy'])
        self.data[grouptools.join('group1', 'group3', 'test2')] = utils.piglit.Test(['thing'])
        self.data[grouptools.join('group3', 'test5')] = utils.piglit.Test(['other'])
        self.data[grouptools.join('group4', 'Test9')] = utils.piglit.Test(['is_caps'])
        self.opts = None
        self.__patcher = mock.patch('framework.profile.options.OPTIONS',
                                    new_callable=options._Options)

    def setup(self):
        self.opts = self.__patcher.start()

    def teardown(self):
        self.__patcher.stop()

    def test_matches_filter_mar_1(self):
        """profile.TestProfile.prepare_test_list: 'not env.filter or matches_any_regex()' env.filter is False

        Nothing should be filtered.

        """
        profile_ = profile.TestProfile()
        profile_.test_list = self.data
        profile_._prepare_test_list()

        nt.assert_dict_equal(dict(profile_.test_list), dict(self.data))

    def test_matches_filter_mar_2(self):
        """profile.TestProfile.prepare_test_list: 'not env.filter or matches_any_regex()' mar is False"""
        self.opts.include_filter = ['test5']

        profile_ = profile.TestProfile()
        profile_.test_list = self.data
        profile_._prepare_test_list()

        baseline = {grouptools.join('group3', 'test5'): utils.piglit.Test(['other'])}

        nt.assert_dict_equal(dict(profile_.test_list), baseline)

    def test_matches_env_exclude(self):
        """profile.TestProfile.prepare_test_list: 'not path in env.exclude_tests'"""
        self.opts.exclude_tests.add(grouptools.join('group3', 'test5'))  # pylint: disable=no-member

        baseline = copy.deepcopy(self.data)
        del baseline[grouptools.join('group3', 'test5')]

        profile_ = profile.TestProfile()
        profile_.test_list = self.data
        profile_._prepare_test_list()

        nt.assert_dict_equal(dict(profile_.test_list), dict(baseline))

    def test_matches_exclude_mar(self):
        """profile.TestProfile.prepare_test_list: 'not matches_any_regexp()'"""
        self.opts.exclude_filter = ['test5']

        baseline = copy.deepcopy(self.data)
        del baseline[grouptools.join('group3', 'test5')]

        profile_ = profile.TestProfile()
        profile_.test_list = self.data
        profile_._prepare_test_list()

        nt.assert_dict_equal(dict(profile_.test_list), dict(baseline))

    def test_matches_include_caps(self):
        """profile.TestProfile.prepare_test_list: matches capitalized tests"""
        self.opts.exclude_filter = ['test9']

        profile_ = profile.TestProfile()
        profile_.test_list = self.data
        profile_._prepare_test_list()

        nt.assert_not_in(grouptools.join('group4', 'Test9'), profile_.test_list)


@utils.nose.no_error
def test_testdict_group_manager_no_name_args_eq_one():
    """profile.TestDict.group_manager: no name and len(args) == 1 is valid"""
    prof = profile.TestDict()
    with prof.group_manager(utils.piglit.Test, 'foo') as g:
        g(['a'])


def test_testprofile_testdict_manager_no_name_args_gt_one():
    """profile.TestDict.group_manager: no name and len(args) > 1 is valid"""
    prof = profile.TestDict()
    with prof.group_manager(utils.piglit.Test, 'foo') as g:
        g(['a', 'b'])

    nt.assert_in(grouptools.join('foo', 'a b'), prof)


@utils.nose.no_error
def test_testdict_group_manager_name():
    """profile.TestDict.group_manager: name plus len(args) > 1 is valid"""
    prof = profile.TestDict()
    with prof.group_manager(utils.piglit.Test, 'foo') as g:
        g(['a', 'b'], 'a')


def test_testdict_group_manager_is_added():
    """profile.TestDict.group_manager: Tests are added to the profile"""
    prof = profile.TestDict()
    with prof.group_manager(utils.piglit.Test, 'foo') as g:
        g(['a', 'b'], 'a')

    nt.assert_in(grouptools.join('foo', 'a'), prof)


def test_testdict_groupmanager_kwargs():
    """profile.TestDict.group_manager: Extra kwargs are passed to the Test"""
    prof = profile.TestDict()
    with prof.group_manager(utils.piglit.Test, 'foo') as g:
        g(['a'], run_concurrent=True)

    test = prof[grouptools.join('foo', 'a')]
    nt.assert_equal(test.run_concurrent, True)


def test_testdict_groupmanager_default_args():
    """profile.TestDict.group_manager: group_manater kwargs are passed to the Test"""
    prof = profile.TestDict()
    with prof.group_manager(utils.piglit.Test, 'foo', run_concurrent=True) as g:
        g(['a'])

    test = prof[grouptools.join('foo', 'a')]
    nt.assert_equal(test.run_concurrent, True)


def test_testdict_groupmanager_kwargs_overwrite():
    """profile.TestDict.group_manager: default_args are overwritten by kwargs"""
    prof = profile.TestDict()
    with prof.group_manager(utils.piglit.Test, 'foo', run_concurrent=True) as g:
        g(['a'], run_concurrent=False)

    test = prof[grouptools.join('foo', 'a')]
    nt.assert_equal(test.run_concurrent, False)


def test_testdict_groupmanager_name_str():
    """profile.TestDict.group_manager: if args is a string it is not joined"""
    prof = profile.TestDict()
    # Yes, this is really about supporting gleantest anyway.
    with prof.group_manager(GleanTest, 'foo') as g:
        g('abc')

    nt.ok_(grouptools.join('foo', 'abc') in prof)


@nt.raises(exceptions.PiglitFatalError)
def test_testdict_key_not_string():
    """profile.TestDict: If key value isn't a string an exception is raised.

    This throws a few different things at the key value and expects an error to
    be raised. It isn't a perfect test, but it was the best I could come up
    with.

    """
    test = profile.TestDict()

    for x in [None, utils.piglit.Test(['foo']), ['a'], {'a': 1}]:
        test[x] = utils.piglit.Test(['foo'])


@nt.raises(exceptions.PiglitFatalError)
def test_testdict_value_not_valid():
    """profile.TestDict: If the value isn't a Test an exception is raised.

    Like the key test this isn't perfect, but it does try the common mistakes.

    """
    test = profile.TestDict()

    for x in [{}, 'a']:
        test['foo'] = x


@nt.raises(exceptions.PiglitFatalError)
def test_testdict_reassignment():
    """profile.TestDict: reassigning a key raises an exception"""
    test = profile.TestDict()
    test['foo'] = utils.piglit.Test(['foo'])
    test['foo'] = utils.piglit.Test(['foo', 'bar'])


@nt.raises(exceptions.PiglitFatalError)
def test_testdict_reassignment_lower():
    """profile.TestDict: reassigning a key raises an exception (capitalization is ignored)"""
    test = profile.TestDict()
    test['foo'] = utils.piglit.Test(['foo'])
    test['Foo'] = utils.piglit.Test(['foo', 'bar'])


def test_testdict_allow_reassignment():
    """profile.TestDict: allow_reassignment works"""
    test = profile.TestDict()
    test['a'] = utils.piglit.Test(['foo'])
    with test.allow_reassignment:
        test['a'] = utils.piglit.Test(['bar'])

    nt.ok_(test['a'].command == ['bar'])


def test_testdict_allow_reassignment_with_groupmanager():
    """profile.TestDict: allow_reassignment wrapper works with groupmanager"""
    testname = grouptools.join('a', 'b')
    prof = profile.TestDict()
    prof[testname] = utils.piglit.Test(['foo'])
    with prof.allow_reassignment:
        with prof.group_manager(utils.piglit.Test, 'a') as g:
            g(['bar'], 'b')

    nt.ok_(prof[testname].command == ['bar'])


def test_testdict_allow_reassignemnt_stacked():
    """profile.profile.TestDict.allow_reassignment: check stacking cornercase

    There is an odd corner case in the original (obvious) implementation of this
    function, If one opens two context managers and then returns from the inner
    one assignment will not be allowed, even though one is still inside the
    first context manager.

    """
    test = profile.TestDict()
    test['a'] = utils.piglit.Test(['foo'])
    with test.allow_reassignment:
        with test.allow_reassignment:
            pass
        test['a'] = utils.piglit.Test(['bar'])

    nt.ok_(test['a'].command == ['bar'])


@nt.raises(exceptions.PiglitFatalError)
def test_testdict_update_reassignment():
    """profile.TestDict.update: Does not implictly allow reassignment"""
    test1 = utils.piglit.Test(['test1'])
    test2 = utils.piglit.Test(['test2'])

    td1 = profile.TestDict()
    td1['test1'] = test1

    td2 = profile.TestDict()
    td2['test1'] = test2

    td1.update(td2)


class TestTestDictReorder(object):
    """Tests for TestDict.reorder."""
    def __init__(self):
        self.list = profile.TestDict()
        self.list['a'] = utils.piglit.Test(['foo'])
        self.list['b'] = utils.piglit.Test(['foo'])
        self.list['c'] = utils.piglit.Test(['foo'])
        self.list['d'] = utils.piglit.Test(['foo'])
        self.list['e'] = utils.piglit.Test(['foo'])
        self.list['f'] = utils.piglit.Test(['foo'])
        self.list['g'] = utils.piglit.Test(['foo'])

    def test_reorder_all(self):
        """profile.TestDict.reorder: reorder when keys match"""
        order = ['g', 'f', 'e', 'd', 'c', 'b', 'a']
        self.list.reorder(order)
        utils.asserts.list_eq(self.list.keys(), order)

    def test_reorder_some(self):
        """profile.TestDict.reorder: reroder when only some keys are provided"""
        order = ['g', 'f', 'e']
        self.list.reorder(order)
        utils.asserts.list_eq(self.list.keys(), order)

    @nt.raises(exceptions.PiglitFatalError)
    def test_reorder_error(self):
        """profile.TestDict.reorder: fail when non-existant test is passed and allow_missing=False"""
        order = ['x', 'f', 'e']
        self.list.reorder(order)
        utils.asserts.list_eq(self.list.keys(), order)
