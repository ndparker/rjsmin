# -*- coding: ascii -*-
#
# Copyright 2007 - 2025
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
=================
 Shell utilities
=================

Shell utilities.
"""
from __future__ import absolute_import

__author__ = "Andr\xe9 Malo"

import contextlib as _contextlib
import errno as _errno
import glob as _glob
import fnmatch as _fnmatch
import functools as _ft
import os as _os
import re as _re
import shutil as _shutil
import sys as _sys
import tempfile as _tempfile

from . import util as _util


root = _os.path.dirname(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
)


@_contextlib.contextmanager
def root_dir():
    """ Context manager to change into the root directory """
    assert root is not None

    old = _os.getcwd()
    try:
        _os.chdir(root)
        yield root
    finally:
        _os.chdir(old)


def _make_split_command():
    """
    Make split_command function

    The command splitter splits between tokens. Tokens are non-whitespace
    sequences or double quoted strings. Inside those double quotes can be
    escaped with a backslash. So have to be backslashes.

    Stolen from <http://opensource.perlig.de/svnmailer/>.

    Returns:
      callable: Parser for generic commandlines
    """
    argre = r'[^"\s]\S*|"[^\\"]*(?:\\[\\"][^\\"]*)*"'
    check = _re.compile(
        r'\s*(?:%(arg)s)(?:\s+(?:%(arg)s))*\s*$' % dict(arg=argre)
    ).match
    split = _re.compile(argre).findall
    strip = _ft.partial(_re.compile(r'\\([\\"])').sub, r'\1')

    def split_command(command):  # pylint: disable = redefined-outer-name
        """
        Split generic commandline into single arguments

        The command splitter splits between tokens. Tokens are non-whitespace
        sequences or double quoted strings. Inside those double quotes can be
        escaped with a backslash. So have to be backslashes.

        Stolen from <http://opensource.perlig.de/svnmailer/>.

        Parameters:
          command (str or iterable):
            The command string to split. If it's not a string, it's taken as a
            generic iterable and returned as a list.

        Returns:
          list: Command splitted parts
        """
        if not isinstance(command, _util.basestring_):
            return list(command)

        if not check(command):
            raise ValueError("Invalid command string %r" % (command,))

        return [
            strip(arg[1:-1]) if arg.startswith('"') else arg
            for arg in split(command)
        ]

    return split_command

split_command = _make_split_command()  # noqa


def _make_formatter(*args, **kwargs):
    """
    Make args / kwargs formatter

    Either args or kwargs or neither of them can be set. There cannot be set
    both of them.

    Returns:
      callable: Formatter, using either args or kwargs
    """
    # pylint: disable = no-else-return

    assert not (args and kwargs)

    if args:
        # tuples are given for the whole command string but applied per token.
        # We need to supply only the tuples which are needed for the current
        # token.
        args = list(args[::-1])
        pcents = _re.compile(r'%[^%]').findall

        def formatter(value):
            """ Tuple formatter """
            count = len(pcents(value))
            torepl = []
            while len(torepl) < count:
                torepl.append(args.pop())
            return value % tuple(torepl)
        return formatter

    elif kwargs:
        return lambda x: x % kwargs

    return lambda x: x


def _make_win32_command():
    r"""
    Make win32_command function

    >>> x = win32_command(r'''
    ...     command arg "arg 2" "" "arg %3"
    ...     "malic'ious argument\\\"&whoami"
    ... ''')
    >>> print(x[:42])
    command arg ^"arg^ 2^" ^"^" ^"arg^ ^%3^" ^
    >>> print(x[41:])
    ^"malic'ious^ argument\\\^"^&whoami^"

    """
    wsp, meta = r'\r\n\t\x0b\x0c\x08 ', r'()%!^"<>&|'
    slashsub = _ft.partial(_re.compile(r'(\\+)("|$)').sub, r'\1\1\2')
    metasub = _ft.partial(_re.compile(r'([%s%s])' % (wsp, meta)).sub, r'^\1')
    qsearch = _re.compile(r'[%s"]' % (wsp,)).search
    needq = lambda x: not x or qsearch(x)  # noqa pylint: disable = unnecessary-lambda-assignment

    def win32_command(command, *args, **kwargs):
        """
        Return a win32/cmd.exe suitable commandline

        :See: https://blogs.msdn.microsoft.com/twistylittlepassagesallalike/
              2011/04/23/everyone-quotes-command-line-arguments-the-wrong-way/

        Either args or kwargs or neither of them can be set. There cannot be
        set both of them.

        Parameters:
          command (str):
            Generic commandline, possibly containing substitutions, filled by
            args or kwargs. See `split_command` for generic commandline
            syntax.

          *args:
            Substitution positional arguments

          **kwargs
            Substitution keyword arguments

        Returns:
          str: Strictly quoted shell commandline for ``cmd.exe``
        """
        # pylint: disable = redefined-outer-name
        return ' '.join([metasub(
            '"%s"' % (slashsub(token).replace('"', '\\"'),)
            if needq(token) else token
        ) for token in map(_make_formatter(*args, **kwargs),
                           split_command(command))])

    return win32_command

win32_command = _make_win32_command()  # noqa


def _make_posix_command():
    r"""
    Make posix_command function

    >>> x = posix_command(r'''
    ...     command arg "arg 2" "" "arg $3"
    ...     "malic'ious argument\\\"&whoami"
    ... ''')
    >>> print(x)
    command arg 'arg 2' '' 'arg $3' 'malic'\''ious argument\"&whoami'

    """
    qsearch = _re.compile(r'[^a-zA-Z\d_./-]').search
    needq = lambda x: not x or qsearch(x)  # noqa pylint: disable = unnecessary-lambda-assignment

    def posix_command(command, *args, **kwargs):
        """
        Return a POSIX shell suitable commandline

        Either args or kwargs or neither of them can be set. There cannot be
        set both of them.

        Parameters:
          command (str):
            Generic commandline, possibly containing substitutions, filled by
            args or kwargs. See `split_command` for generic commandline
            syntax.

          *args:
            Substitution positional arguments

          **kwargs
            Substitution keyword arguments

        Returns:
          str: Strictly quoted shell commandline for POSIX shells
        """
        # pylint: disable = redefined-outer-name
        return ' '.join([
            "'%s'" % (token.replace("'", "'\\''")) if needq(token) else token
            for token in map(_make_formatter(*args, **kwargs),
                             split_command(command))
        ])
    return posix_command

posix_command = _make_posix_command()  # noqa

command = win32_command if _sys.platform.lower() == 'win32' else posix_command


def native(path):
    """
    Convert slash path to native

    Parameters:
      path (str):
        Path relative to the checkout root

    Returns:
      str: The native path
    """
    path = _os.path.sep.join(path.split('/'))
    return _os.path.normpath(_os.path.join(root, path))


def relative(path):
    """
    Convert native path into root-relative

    Parameters:
      path (str):
        Path relative to the checkout root

    Returns:
      str: The relative path - with slashes
    """
    return "/".join(pathparts(_os.path.relpath(native(path), native(root))))


def cp(src, dest):
    """
    Copy src to dest

    Parameters:
      src (str):
        Source path, relative to the checkout root

      dest (str):
        Dest path, relative to the checkout root
    """
    _shutil.copy2(native(src), native(dest))


def cp_r(src, dest, ignore=None):
    """
    Copy -r src to dest

    Parameters:
      src (str):
        Source path, relative to the checkout root

      dest (str):
        Dest path, relative to the checkout root

      ignore (callable):
        Ignore callback
    """
    _shutil.copytree(native(src), native(dest), ignore=ignore)


def rm(*dest):
    """
    Remove one or more files, ENOENT is not considered an error

    Parameters:
      *dest:
        Files to remove
    """
    if len(dest) == 1 and not isinstance(dest[0], _util.basestring_):
        dest = dest[0]

    for name in dest:
        try:
            _os.unlink(native(name))
        except OSError as e:
            if _errno.ENOENT != e.errno:
                raise


def rm_rf(*dest):
    """
    Remove one or more trees

    :Parameters:
      *dest:
        Paths to remove
    """
    if len(dest) == 1 and not isinstance(dest[0], _util.basestring_):
        dest = dest[0]

    for name in dest:
        name = native(name)
        if _os.path.islink(name):
            _os.unlink(name)

        elif _os.path.isfile(name):
            rm(name)

        elif _os.path.exists(name):
            for path in files(name, '*'):
                if not _os.path.islink(native(path)):
                    _os.chmod(native(path), 0o644)
            _shutil.rmtree(name)


def mkdir_p(*dirnames):
    """
    Create one or more directories

    Parameters:
      *dirnames:
        Directory names (the leaf directory)
    """
    if len(dirnames) == 1 and not isinstance(dirnames[0], _util.basestring_):
        dirnames = dirnames[0]

    for dirname in dirnames:
        try:
            _os.makedirs(dirname)
        except OSError as e:
            # makedirs throws OSError if the last dir segment exists
            if e.errno != _errno.EEXIST:
                raise


mkstemp = _tempfile.mkstemp
walk = _os.walk


def glob(*pattern, **kwargs):
    """
    glob(*pattern, prune=None, prune_base=('.git', '.svn', 'CVS')):

    Find files or directories with glob pattern (python 3.6+)

    Parameters:
      *pattern:
        Glob to match against

      prune (iterable):
        List of directory basenames to ignore.
        Default: None. Can be empty or ``None`` (meaning not to prune anything
        except prune_base)

      prune_base (iterable):
        Extra list of directory basenames to ignore.
        Default: ('.git', '.svn', 'CVS'). Can be empty or ``None`` (meaning
        not to prune anything except prune)

    Returns:
      iterable: Iterator over matching pathnames
    """
    for single in pattern:
        # pylint: disable = use-yield-from
        for item in _glob_single(single, **kwargs):
            yield item


def glob_escape(value):
    """
    Escape string for use in glob pattern (python 3.6+)

    Parameters:
      value (str):
        value to escape

    Returns:
      str: The escaped value
    """
    return _glob.escape(value)


def _glob_single(pattern, prune=None, prune_base=('.git', '.svn', 'CVS')):
    """
    Find files or directories with glob pattern (python 3.6+)

    Parameters:
      pattern (str):
        Glob to match against

      prune (iterable):
        List of directory basenames to ignore.
        Default: None. Can be empty or ``None`` (meaning not to prune anything
        except prune_base)

      prune_base (iterable):
        Extra list of directory basenames to ignore.
        Default: ('.git', '.svn', 'CVS'). Can be empty or ``None`` (meaning
        not to prune anything except prune)

    Returns:
      iterable: Iterator over matching pathnames
    """
    normroot = native(root + "/")
    pattern = _os.path.join(_glob.escape(normroot), pattern)
    toprune = set(prune or ()) | set(prune_base or ())

    for found in _glob.iglob(pattern, recursive=True):
        assert found.startswith(normroot)
        parts = pathparts(found[len(normroot):])
        if set(parts) & toprune:
            continue
        yield "/".join(parts)


def pathparts(path):
    """
    Return path parts

    If the path ends with a slash the last part will be an empty string

    Parameters:
      path (str):
        The path to split into parts

    Returns:
      list: The path parts
    """
    aslist = []
    head, tail = _os.path.split(path)
    if not tail:
        aslist.append(tail)
        head, tail = _os.path.split(head)
    while tail:
        aslist.append(tail)
        head, tail = _os.path.split(head)
    aslist.reverse()
    return aslist


def files(base, wildcard='[!.]*', recursive=1, prune=None,
          prune_base=('.git', '.svn', 'CVS')):
    """
    Determine a filelist

    Parameters:
      base (str):
        Base path to start from

      wildcard (str):
        Glob to match against

      recursive (bool):
        Deep walk into the tree? Default: true

      prune (iterable):
        List of directory basenames to ignore.
        Default: None. Can be empty or ``None`` (meaning not to prune anything
        except prune_base)

      prune_base (iterable):
        Extra list of directory basenames to ignore.
        Default: ('.git', '.svn', 'CVS'). Can be empty or ``None`` (meaning
        not to prune anything except prune)

    Returns:
      iterable: Iterator over matching pathnames
    """
    prune = tuple(prune_base or ()) + tuple(prune or ())
    for dirpath, dirnames, filenames in walk(native(base)):
        for item in prune:
            if item in dirnames:
                dirnames.remove(item)

        filenames.sort()
        for name in _fnmatch.filter(filenames, wildcard):
            dest = _os.path.join(dirpath, name)
            if dest.startswith(root):
                dest = dest.replace(root, '', 1)
            yield '/'.join(pathparts(dest))

        if not recursive:
            break
        dirnames.sort()


def dirs(base, wildcard='[!.]*', recursive=1, prune=None,
         prune_base=('.git', '.svn', 'CVS')):
    """
    Determine a directory list

    Parameters:
      base (str):
        Base path to start from

      wildcard (str):
        Glob to match against

      recursive (bool):
        Deep walk into the tree? Default: true

      prune (iterable):
        List of directory basenames to ignore.
        Default: None. Can be empty or ``None`` (meaning not to prune anything
        except prune_base)

      prune_base (iterable):
        Extra list of directory basenames to ignore.
        Default: ('.git', '.svn', 'CVS'). Can be empty or ``None`` (meaning
        not to prune anything except prune)

    Returns:
      iterable: Iterator over matching pathnames
    """
    prune = tuple(prune_base or ()) + tuple(prune or ())
    for dirpath, dirnames, _ in walk(native(base)):
        for item in prune:
            if item in dirnames:
                dirnames.remove(item)

        dirnames.sort()
        for name in _fnmatch.filter(dirnames, wildcard):
            dest = _os.path.join(dirpath, name)
            if dest.startswith(root):
                dest = dest.replace(root, '', 1)
            yield '/'.join(pathparts(dest))

        if not recursive:
            break


def frompath(executable):
    """
    Find executable in PATH

    Parameters:
      executable (str):
        Command to search for

    Returns:
      str: Full path or ``None``
    """
    # Based on distutils.spawn.find_executable.
    path = _os.environ.get('PATH', '')
    paths = [
        _os.path.expanduser(item)
        for item in path.split(_os.pathsep)
    ]
    ext = _os.path.splitext(executable)[1]
    exts = ['']
    if _sys.platform == 'win32' or _os.name == 'os2':
        eext = ['.exe', '.bat', '.py']
        if ext not in eext:
            exts.extend(eext)

    for ext in exts:
        if not _os.path.isfile(executable + ext):
            for path in paths:
                fname = _os.path.join(path, executable + ext)
                if _os.path.isfile(fname):
                    # the file exists, we have a shot at spawn working
                    return fname
        else:
            return executable + ext

    return None
