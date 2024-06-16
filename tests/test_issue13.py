# -*- coding: ascii -*-
u"""
:Copyright:

 Copyright 2019 - 2024
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

========
 Basics
========

test for basics.
"""
__author__ = u"Andr\xe9 Malo"

import os as _os

import rjsmin as _rjsmin

# pylint: disable = protected-access
py_jsmin = _rjsmin._make_jsmin(python_only=True)
py_jsmin2 = _rjsmin.jsmin_for_posers

import _rjsmin

c_jsmin = _rjsmin.jsmin


def load(name):
    """Load a file"""
    with open(_os.path.join(_os.path.dirname(__file__), name), 'rb') as fp:
        return fp.read()


def save(name, value):
    """Load a file"""
    with open(_os.path.join(_os.path.dirname(__file__), name), 'wb') as fp:
        fp.write(value)


def test_issue():
    """Test issue"""
    inp = load('js/issue13.js')
    exp = load('js/issue13.min.js')
    # save('js/issue13.min.js', py_jsmin(inp))
    assert py_jsmin(inp) == exp
    assert py_jsmin2(inp) == exp
    assert c_jsmin(inp) == exp

    inp = inp.decode('latin-1')
    exp = exp.decode('latin-1')
    assert py_jsmin(inp) == exp
    assert py_jsmin2(inp) == exp
    assert c_jsmin(inp) == exp


def test_issue_bang():
    """Test issue with bang comments"""
    inp = load('js/issue13.js')
    exp = load('js/issue13.bang.js')
    # save('js/issue13.bang.js', py_jsmin(inp, keep_bang_comments=True))
    assert py_jsmin(inp, keep_bang_comments=True) == exp
    assert py_jsmin2(inp, keep_bang_comments=True) == exp
    assert c_jsmin(inp, keep_bang_comments=True) == exp

    inp = inp.decode('latin-1')
    exp = exp.decode('latin-1')
    assert py_jsmin(inp, keep_bang_comments=True) == exp
    assert py_jsmin2(inp, keep_bang_comments=True) == exp
    assert c_jsmin(inp, keep_bang_comments=True) == exp
