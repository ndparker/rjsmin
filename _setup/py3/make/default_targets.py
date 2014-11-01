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
 Simple make base
==================

Simple make base.
"""
__author__ = "Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import os as _os
import sys as _sys

from _setup import make as _make
from _setup import shell as _shell


class MakefileTarget(_make.Target):
    """ Create a make file """
    NAME = 'makefile'

    def run(self):
        def escape(value):
            """ Escape for make and shell """
            return '"%s"' % value.replace(
                '\\', '\\\\').replace(
                '"', '\\"').replace(
                '$', '\\$$')
        def decorate(line, prefix='# ', width=78, char='~', padding=' '):
            """ Decorate a line """
            line = line.center(width - len(prefix))
            return '%s%s%s%s%s%s' % (
                prefix,
                char * (len(line) - len(line.lstrip()) - len(padding)),
                padding,
                line.strip(),
                padding,
                char * (len(line) - len(line.rstrip()) - len(padding)),
            )

        python = escape(_sys.executable)
        script = escape(_sys.argv[0])
        targets = self.runner.targetinfo()
        names = []
        for name, info in list(targets.items()):
            if not info['hide']:
                names.append(name)
        names.sort()

        fp = open(_shell.native('Makefile'), 'w', encoding='utf-8')
        print(decorate("Generated Makefile, DO NOT EDIT"), file=fp)
        print(decorate("python %s %s" % (
            _os.path.basename(script), self.NAME
        )), file=fp)
        print(file=fp)
        print("_default_:", file=fp)
        print("\t@%s %s" % (python, script), file=fp)
        for name in names:
            print("\n", file=fp)
            print("# %s" % \
                targets[name]['desc'].splitlines()[0].strip(), file=fp)
            print("%s:" % name, file=fp)
            print("\t@%s %s %s" % (python, script, escape(name)), file=fp)
        print(file=fp)
        extension = self.extend(names)
        if extension is not None:
            print(extension, file=fp)
            print(file=fp)
        print(".PHONY: _default_ %s\n\n" % ' '.join(names), file=fp)
        fp.close()

    def extend(self, names):
        pass


class CleanTarget(_make.Target):
    """ Clean the mess """
    NAME = 'clean'
    _scm, _dist = True, False

    def run(self):
        self.runner.run_clean(scm=self._scm, dist=self._dist)


class DistCleanTarget(CleanTarget):
    """ Clean as freshly unpacked dist package """
    NAME = 'distclean'
    _scm, _dist = False, True


class ExtraCleanTarget(CleanTarget):
    """ Clean everything """
    NAME = 'extraclean'
    _scm, _dist = True, True
