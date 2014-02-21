#!/usr/bin/env python

# This code is original from jsmin.c by Douglas Crockford. This is a
# playground port for understanding the semantics by Andr\xe9 Malo. Here's the
# jsmin.c license:
#
# /* jsmin.c
#    2007-01-08
#
# Copyright (c) 2002 Douglas Crockford  (www.crockford.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# The Software shall be used for Good, not Evil.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# */

import re as _re
try:
    import cStringIO as _string_io
except ImportError:
    try:
        import StringIO as _string_io
    except ImportError:
        import io as _string_io


class JSMinError(Exception):
    """ Minifier base error """

class UnterminatedComment(JSMinError):
    """ Unterminated comment """

class UnterminatedRegex(JSMinError):
    """ Unterminated Regex literal """

class UnterminatedString(JSMinError):
    """ Unterminated String literal """


class PrintableLookAheadStream(object):
    """ Stream wrapper providing get and peek methods """

    def __init__(self, stream):
        """ Initialization """
        self._stream = stream
        self._looked = None

    def get(self):
        """ Get one character """
        char, self._looked = self._looked, None
        if char is not None:
            return char
        char = self._stream.read(1)
        if not char:
            raise EOFError()
        if char == '\r':
            return '\n'
        if ord(char) >= 32 or char == '\n':
            return char
        return ' '

    def peek(self):
        """ Peek one character ahead """
        self._looked = self.get()
        return self._looked


def m(regex):
    """ Regex -> matcher """
    return _re.compile(regex).match


def next_char(stream):
    """ Next character leaving out comments """
    get, peek = stream.get, stream.peek
    char = get()
    if char == '/':
        try:
            c_next = peek()
        except EOFError:
            return char
        if c_next == '/':   # // comment
            while char != '\n':
                char = get()
        elif c_next == '*': #  /* comment */
            get()
            try:
                while not(char == '*' and peek() == '/'):
                    char = get()
                get()
                char = ' '
            except EOFError:
                raise UnterminatedComment()
    return char


def action3(stream, out, first, second,
            pre_regex_match=m(r'[(,=:\[!&|?{};\n]')):
    """ throw away second, skip comments and regexps """
    try:
        second = next_char(stream)
    except EOFError:
        out.write(first)
        raise
    if second == '/' and pre_regex_match(first):
        # Regex found. Parse it till the end.
        write, get = out.write, stream.get
        write(first)
        write(second)
        try:
            first = get()
            while first != '/':
                if first == '\\':
                    write(first)
                    first = get()
                elif first == '[':
                    write(first)
                    first = get()
                    while first != ']':
                        if first == '\\':
                            write(first)
                            first = get()
                        write(first)
                        first = get()
                write(first)
                first = get()
            second = next_char(stream)
        except EOFError:
            raise UnterminatedRegex()
    return first, second


def action2(stream, out, first, second):
    """ shift, skip strings, comments and regexps """
    first = second
    if first in (r''''"'''):
        quote = first
        write, get = out.write, stream.get
        write(first)
        try:
            first = get()
            while first != quote:
                if first == '\\':
                    write(first)
                    first = get()
                write(first)
                first = get()
        except EOFError:
            raise UnterminatedString()
    return action3(stream, out, first, second)


def action1(stream, out, first, second):
    """ write, shift, skip strings, comments and regexps """
    out.write(first)
    return action2(stream, out, first, second)


def jsmin_stream(stream, out,
                 id_literal=m(r'[a-zA-Z0-9_$\\\177-\377]'),
                 open_match=m(r'[{\[(+-]'),
                 close_match=m(r'[}\])+"\047-]')):
    """
    JSMin after jsmin.c by Douglas Crockford

    http://www.crockford.com/javascript/jsmin.c
    """
    # pylint: disable = R0912
    stream = PrintableLookAheadStream(stream)
    try:
        first, second = action3(stream, out, '\n', None)
        while 1:
            if first == ' ':
                if id_literal(second):
                    first, second = action1(stream, out, first, second)
                else:
                    first, second = action2(stream, out, first, second)
            elif first == '\n':
                if open_match(second):
                    first, second = action1(stream, out, first, second)
                elif second == ' ':
                    first, second = action3(stream, out, first, second)
                elif id_literal(second):
                    first, second = action1(stream, out, first, second)
                else:
                    first, second = action2(stream, out, first, second)
            elif second == ' ':
                if id_literal(first):
                    first, second = action1(stream, out, first, second)
                else:
                    first, second = action3(stream, out, first, second)
            elif second == '\n':
                if close_match(first):
                    first, second = action1(stream, out, first, second)
                elif id_literal(first):
                    first, second = action1(stream, out, first, second)
                else:
                    first, second = action3(stream, out, first, second)
            else:
                first, second = action1(stream, out, first, second)
    except EOFError:
        pass # done.


def jsmin(script):
    """
    Minify JS

    :Parameters:
      `script` : ``str``
        JS to minify

    :Return: Minified JS
    :Rtype: ``str``
    """
    out = _string_io.StringIO()
    jsmin_stream(_string_io.StringIO(script), out)
    return out.getvalue().strip()


if __name__ == '__main__':
    import sys as _sys
    _sys.stdout.write(jsmin(_sys.stdin.read()))
