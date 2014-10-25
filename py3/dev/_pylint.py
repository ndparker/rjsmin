# -*- coding: ascii -*-
#
# Copyright 2006 - 2014
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
=================================
 Support for code analysis tools
=================================

Support for code analysis tools.
"""
__author__ = "Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import re as _re
import sys as _sys

from _setup import term as _term
from _setup import shell as _shell


class NotFinished(Exception):
    """ Exception used for message passing in the stream filter """


class NotParseable(Exception):
    """ Exception used for message passing in the stream filter """


class SpecialMessage(Exception):
    """ Exception used for message passing in the stream filter """


class FilterStream(object):
    """ Stream filter """
    _LINERE = _re.compile(r'''
        (?P<name>[^:]+)
        :
        (?P<lineno>\d+)
        :\s+
        \[(?P<mid>[^\],]+)(?:,\s+(?P<func>[^\]]+))?\]
        \s+
        (?P<desc>.*)
    ''', _re.X)
    _SIMRE = _re.compile(r'in (?P<number>\d+) files')
    _CYCRE = _re.compile(r'\((?P<cycle>[^)]+)\)')

    def __init__(self, term, stream=_sys.stdout):
        self.written = False
        self._stream = stream
        self._lastname = None
        self._cycled = False
        self._term = dict(term)
        self._buffer = ''

    def write(self, towrite):
        """ Stream write function """
        self._buffer += towrite
        term = self._term

        while True:
            try:
                name, lineno, mid, func, desc = self._parse()
            except NotFinished:
                break
            except SpecialMessage as e:
                self._dospecial(e)
                continue
            except NotParseable as e:
                self._print_literal(str(e.args[0]))
                continue

            if name != self._lastname:
                if self._lastname is not None:
                    self._stream.write("\n")
                term['path'] = name
                self._stream.write(
                    "%(BOLD)s>>> %(path)s%(NORMAL)s\n" % term
                )
                self._lastname = name
                self.written = True

            term['mid'] = mid
            if mid.startswith('E') or mid.startswith('F'):
                self._stream.write("%(BOLD)s%(RED)s%(mid)s%(NORMAL)s" % term)
            elif mid == 'W0511':
                self._stream.write(
                    "%(BOLD)s%(GREEN)s%(mid)s%(NORMAL)s" % term
                )
            else:
                self._stream.write(
                    "%(BOLD)s%(YELLOW)s%(mid)s%(NORMAL)s" % term
                )

            if int(lineno) != 0:
                term['lineno'] = lineno
                self._stream.write(" (%(lineno)s" % term)
                if func:
                    term['func'] = func
                    self._stream.write(
                        ", %(BOLD)s%(YELLOW)s%(func)s%(NORMAL)s" % term
                    )
                self._stream.write(')')

            self._stream.write(": %s\n" % desc)
            self._stream.flush()

        return

    def _print_literal(self, line):
        """ Print literal """
        suppress = (
            line.startswith('Unable to get imported names for ') or
            line.startswith(
                "Exception exceptions.RuntimeError: 'generator "
                "ignored GeneratorExit' in <generator object at") or
            line.startswith(
                "Exception RuntimeError: 'generator "
                "ignored GeneratorExit' in <generator object") or
            not line.strip()
        )
        if not suppress:
            self._stream.write("%s\n" % line)
            self._stream.flush()
            self.written = True

    def _dospecial(self, e):
        """ Deal with special messages """
        if e.args[0] == 'R0401':
            pos = self._buffer.find('\n')
            _, self._buffer = (
                self._buffer[:pos + 1], self._buffer[pos + 1:]
            )
            term = self._term
            term['mid'] = e.args[0]
            if not self._cycled:
                self._cycled = True
                self._stream.write('\n')
                self._stream.write(
                    "%(BOLD)s%(YELLOW)s%(mid)s%(NORMAL)s" % term
                )
                self._stream.write(": Cyclic imports\n")
            match = self._CYCRE.search(e.args[1])
            term['cycle'] = match.group('cycle')
            self._stream.write("%(BOLD)s@@@ %(NORMAL)s%(cycle)s\n" % term)
            self._stream.flush()
            self.written = True

        elif e.args[0] == 'R0801':
            match = self._SIMRE.search(e.args[1])
            if not match:
                raise AssertionError(
                    'Could not determine number of similar files'
                )

            numfiles = int(match.group('number'))
            pos = -1
            for _ in range(numfiles + 1):
                pos = self._buffer.find('\n', pos + 1)
            if pos >= 0:
                lines = self._buffer[:pos + 1]
                self._buffer = self._buffer[pos + 1:]
                term = self._term

                self._stream.write("\n")
                for name in lines.splitlines()[1:]:
                    name = name.rstrip()[2:]
                    term['path'] = name
                    self._stream.write(
                        "%(BOLD)s=== %(path)s%(NORMAL)s\n" % term
                    )
                    self._lastname = name

                term['mid'] = e.args[0]
                self._stream.write(
                    "%(BOLD)s%(YELLOW)s%(mid)s%(NORMAL)s" % term
                )
                self._stream.write(": %s\n" % e.args[1])
                self._stream.flush()
                self.written = True

    def _parse(self):
        """ Parse output """
        if '\n' not in self._buffer:
            raise NotFinished()

        line = self._buffer[:self._buffer.find('\n') + 1]
        self._buffer = self._buffer[len(line):]
        line = line.rstrip()
        match = self._LINERE.match(line)
        if not match:
            raise NotParseable(line)

        mid = match.group('mid')
        if mid in ('R0801', 'R0401'):
            self._buffer = "%s\n%s" % (line, self._buffer)
            raise SpecialMessage(mid, match.group('desc'))

        return match.group('name', 'lineno', 'mid', 'func', 'desc')


def run(config, *args):
    """ Run pylint """
    try:
        from pylint import lint
        from pylint.reporters import text
    except ImportError:
        return 2

    if config is None:
        config = _shell.native('pylintrc')
    argv = [
        '--rcfile', config,
        '--reports', 'no',
    ]

    stream = FilterStream(_term.terminfo())

    old_stderr = _sys.stderr
    try:
        # pylint: disable = E1101
        _sys.stderr = stream
        from pylint import __pkginfo__
        if __pkginfo__.numversion >= (1, 0, 0):
            reporter = text.TextReporter(stream)
            argv.extend([
                '--msg-template',
                '{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'
            ])
        else:
            argv.extend([
                '--output-format', 'parseable',
                '--include-ids', 'yes'
            ])
            if __pkginfo__.numversion < (0, 13):
                lint.REPORTER_OPT_MAP['parseable'] = \
                    lambda: text.TextReporter2(stream)
                reporter = text.TextReporter2(stream)
            else:
                reporter = text.ParseableTextReporter(stream)
                lint.REPORTER_OPT_MAP['parseable'] = lambda: reporter

        for path in args:
            try:
                try:
                    lint.Run(argv + [path], reporter=reporter)
                except SystemExit:
                    pass  # don't accept the exit. strange errors happen...

                if stream.written:
                    print()
                    stream.written = False
            except KeyboardInterrupt:
                print()
                raise
    finally:
        _sys.stderr = old_stderr

    return 0
