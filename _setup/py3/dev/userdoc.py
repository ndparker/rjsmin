# -*- coding: ascii -*-
#
# Copyright 2009, 2010, 2011
# Andr\xe9 Malo or his licensors, as applicable
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
===================
 User doc builders
===================

User doc builders.
"""
__author__ = "Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import os as _os

from _setup import shell as _shell
from _setup import term as _term


def sphinx(**kwargs):
    """ Run sphinx """
    prog = _shell.frompath('sphinx-build')
    if prog is None:
        _term.red("sphinx-build not found")
        return False

    env = dict(_os.environ)

    argv = [
        prog, '-a',
        '-d', _os.path.join(kwargs['build'], 'doctrees'),
        '-b', 'html',
        kwargs['source'],
        kwargs['target'],
    ]

    return not _shell.spawn(*argv, **{'env': env})
