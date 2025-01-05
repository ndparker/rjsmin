# -*- coding: ascii -*-
u"""
:Copyright:

 Copyright 2019 - 2025
 Andr\xe9 Malo or his licensors, as applicable

:License:

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

=====================
 C ext special tests
=====================

C ext special tests.
"""
__author__ = u"Andr\xe9 Malo"

from pytest import raises

import rjsmin as _rjsmin

# pylint: disable = protected-access
py_jsmin = _rjsmin._make_jsmin(python_only=True)
py_jsmin2 = _rjsmin.jsmin_for_posers

import _rjsmin

c_jsmin = _rjsmin.jsmin

from . import _util as _test


def test_keep_bang_comments():
    """keep_bang_comments argument error"""
    with raises(RuntimeError) as e:
        c_jsmin("", keep_bang_comments=_test.badbool)
    assert e.value.args == ("yoyo",)


def test_input_type():
    """input type must be a string or bytes"""
    with raises(TypeError):
        c_jsmin(None)

    with raises(TypeError):
        py_jsmin(None)

    with raises(TypeError):
        py_jsmin2(None)
