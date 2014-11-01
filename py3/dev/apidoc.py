# -*- coding: ascii -*-
#
# Copyright 2007, 2008, 2009, 2010, 2011
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
==================
 API doc builders
==================

API doc builders.
"""
__author__ = "Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import os as _os
import re as _re

from _setup import shell as _shell
from _setup import term as _term
from _setup import util as _util


def _cleanup_epydoc(target):
    """
    Cleanup epydoc generated files

    This removes the epydoc-footer. It changes every release because of the
    timestamp. That creates bad diffs (accidently it's also invalid html).
    """
    search = _re.compile(r'<table[^<>]+width="100%%"').search
    for filename in _shell.files(target, '*.html'):
        fp = open(filename, 'r', encoding='latin-1')
        try:
            html = fp.read()
        finally:
            fp.close()
        match = search(html)
        if match:
            start = match.start()
            end = html.find('</table>', start)
            if end >= 0:
                end += len('</table>') + 1
        html = html[:start] + html[end:]
        fp = open(filename, 'w', encoding='latin-1')
        try:
            fp.write(html)
        finally:
            fp.close()


_VERSION_SEARCH = _re.compile(
    r'\bversion\s+(?P<major>\d+)\.(?P<minor>\d+)'
).search
def epydoc(**kwargs):
    """ Run epydoc """
    # pylint: disable = R0912
    prog = kwargs.get('epydoc') or 'epydoc'
    if not _os.path.dirname(_os.path.normpath(prog)):
        prog = _shell.frompath(prog)
    if not prog:
        _term.red("%(epydoc)s not found",
            epydoc=kwargs.get('epydoc') or 'epydoc',
        )
        return False

    version = _VERSION_SEARCH(_shell.spawn(prog, "--version", stdout=True))
    if version is not None:
        try:
            version = tuple(map(int, version.group('major', 'minor')))
        except (TypeError, ValueError):
            version = None
    if version is None:
        _term.red("%(prog)s version not recognized" % locals())
        return False

    if version < (3, 0):
        _term.red("%(prog)s is too old %(version)r < (3, 0)" % locals())
        return False

    env = dict(_os.environ)

    prepend = kwargs.get('prepend')
    if prepend:
        toprepend = _os.pathsep.join(map(str, prepend))
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = _os.pathsep.join((
                toprepend, env['PYTHONPATH']
            ))
        else:
            env['PYTHONPATH'] = toprepend

    append = kwargs.get('append')
    if append:
        toappend = _os.pathsep.join(map(str, append))
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = _os.pathsep.join((
                env['PYTHONPATH'], toappend
            ))
        else:
            env['PYTHONPATH'] = toappend

    moreenv = kwargs.get('env')
    if moreenv:
        env.update(moreenv)

    config = kwargs.get('config') or _shell.native('docs/epydoc.conf')

    argv = [prog, '--config', config]
    res = not _shell.spawn(*argv, **{'env': env})
    if res:
        cfg = _util.SafeConfigParser()
        cfg.read(config)
        try:
            target = dict(cfg.items('epydoc'))['target']
        except KeyError:
            pass
        else:
            _cleanup_epydoc(target)
    return res
