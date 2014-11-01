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

import sys as _sys

from _setup import term as _term


class Failure(SystemExit):
    """ Failure exception """


def fail(reason):
    """ Fail for a reason """
    raise Failure(reason)


def warn(message, name=None):
    """ Warn """
    _term.red("%(NAME)sWarning: %(msg)s",
        NAME=name and "%s:" % name or '', msg=message
    )


def fatal(reason):
    """ Fatal error, immediate stop """
    print(reason, file=_sys.stderr)
    _sys.exit(1)


class Target(object):
    """ Target base class """
    NAME = None
    DEPS = None
    HIDDEN = False

    ERROR = None

    def __init__(self, runner):
        """ Base __init__ """
        self.runner = runner
        self.init()

    def init(self):
        """ Default init hook """
        pass

    def run(self):
        """ Default run hook """
        pass

    def clean(self, scm=True, dist=False):
        """ Default clean hook """
        pass


class _Runner(object):
    """ Runner """

    def __init__(self, *targetscollection):
        """ Initialization """
        tdict = {}
        if not targetscollection:
            import __main__
            targetscollection = [__main__]

        from _setup.make import default_targets
        if default_targets not in targetscollection:
            targetscollection.append(default_targets)

        for targets in targetscollection:
            for value in list(vars(targets).values()):
                if isinstance(value, type) and issubclass(value, Target) and \
                        value.NAME is not None:
                    if value.NAME in tdict:
                        if issubclass(value, tdict[value.NAME]):
                            pass # override base target
                        elif issubclass(tdict[value.NAME], value):
                            continue # found base later. ignore
                        else:
                            warn('Ambiguous target name', value.NAME)
                            continue
                    tdict[value.NAME] = value
        self._tdict = tdict
        self._itdict = {}

    def print_help(self):
        """ Print make help """
        import textwrap as _textwrap

        targets = self.targetinfo()
        keys = []
        for key, info in list(targets.items()):
            if not info['hide']:
                keys.append(key)
        keys.sort()
        length = max(list(map(len, keys)))
        info = []
        for key in keys:
            info.append("%s%s" % (
                (key + " " * length)[:length + 2],
                _textwrap.fill(
                    targets[key]['desc'].strip(),
                    subsequent_indent=" " * (length + 2)
                ),
            ))
        print("Available targets:\n\n" + "\n".join(info))

    def targetinfo(self):
        """ Extract target information """
        result = {}
        for name, cls in list(self._tdict.items()):
            result[name] = {
                'desc': cls.__doc__ or "no description",
                'hide': cls.HIDDEN,
                'deps': cls.DEPS or (),
            }
        return result

    def _topleveltargets(self):
        """ Find all top level targets """
        rev = {} # key is a dep of [values]
        all_ = self.targetinfo()
        for target, info in list(all_.items()):
            for dep in info['deps']:
                if dep not in all_:
                    fatal("Unknown target '%s' (dep of %s) -> exit" % (
                        dep, target
                    ))
                rev.setdefault(dep, []).append(target)
        return [target for target, info in list(rev.items()) if not info]

    def _run(self, target, seen=None):
        """ Run a target """
        if target.DEPS:
            self(*target.DEPS, **{'seen': seen})

        if not target.HIDDEN:
            _term.yellow(">>> %(name)s", name=target.NAME)

        try:
            result = target.run()
        except KeyboardInterrupt:
            result, target.ERROR = False, "^C -> exit"
        except Failure as e:
            result, target.ERROR = False, "%s: %s" % (target.NAME, e)
        except (SystemExit, MemoryError):
            raise
        except:
            import traceback
            target.ERROR = "%s errored:\n%s" % (target.NAME, ''.join(
                traceback.format_exception(*_sys.exc_info())
            ))
            result = False
        else:
            if result is None:
                result = True
        return result

    def _clean(self, target, scm, dist, seen=None):
        """ Run a target """
        if target.DEPS:
            self.run_clean(
                *target.DEPS, **{'scm': scm, 'dist': dist, 'seen': seen}
            )

        try:
            result = target.clean(scm, dist)
        except KeyboardInterrupt:
            result, target.ERROR = False, "^C -> exit"
        except Failure as e:
            result, target.ERROR = False, "%s: %s" % (target.NAME, e)
        except (SystemExit, MemoryError):
            raise
        except:
            import traceback
            target.ERROR = "%s errored:\n%s" % (target.NAME, ''.join(
                traceback.format_exception(*_sys.exc_info())
            ))
            result = False
        else:
            if result is None:
                result = True
        return result

    def _make_init(self, seen):
        """ Make init mapper """
        def init(target):
            """ Return initialized target """
            if target not in seen:
                try:
                    seen[target] = self._tdict[target](self)
                except KeyError:
                    fatal("Unknown target '%s' -> exit" % target)
            else:
                seen[target] = None
            return seen[target]
        return init

    def run_clean(self, *targets, **kwargs):
        """ Run targets """
        def pop(name, default=None):
            """ Pop """
            if name in kwargs:
                value = kwargs[name]
                del kwargs[name]
                if value is None:
                    return default
                return value
            else:
                return default
        seen = pop('seen', {})
        scm = pop('scm', True)
        dist = pop('dist', False)
        if kwargs:
            raise TypeError('Unknown keyword parameters')

        if not targets:
            top_targets = self._topleveltargets()
            targets = self.targetinfo()
            for item in top_targets:
                del targets[item]
            targets = list(targets.keys())
            targets.sort()
            top_targets.sort()
            targets = top_targets + targets

        init = self._make_init(seen)
        for name in targets:
            target = init(name)
            if target is not None:
                if not self._clean(target, scm=scm, dist=dist, seen=seen):
                    msg = target.ERROR
                    if msg is None:
                        msg = "Clean target %s returned error -> exit" % name
                    fatal(msg)

    def __call__(self, *targets, **kwargs):
        """ Run targets """
        if 'seen' in kwargs:
            seen = kwargs['seen']
            del kwargs['seen']
        else:
            seen = None
        if seen is None:
            seen = self._itdict
        if kwargs:
            raise TypeError('Unknown keyword parameters')

        init = self._make_init(seen)
        for name in targets:
            target = init(name)
            if target is not None:
                if not self._run(target, seen):
                    msg = target.ERROR
                    if msg is None:
                        msg = "Target %s returned error -> exit" % name
                    fatal(msg)


def main(*args, **kwargs):
    """
    main(argv=None, *args, name=None)

    Main start point. This function parses the command line and executes the
    targets given through `argv`. If there are no targets given, a help output
    is generated.

    :Parameters:
      `argv` : sequence
        Command line arguments. If omitted or ``None``, they are picked from
        ``sys.argv``.

      `args` : ``tuple``
        The list of modules with targets. If omitted, ``__main__``
        is imported and treated as target module. Additionally the mechanism
        always adds the `_setup.make` module (this one) to the list in order
        to grab some default targets.

      `name` : ``str``
        Name of the executing module. If omitted or ``None``, ``'__main__'``
        is assumed. If the final name is not ``'__main__'``, the function
        returns immediately.
    """
    try:
        name = kwargs['name']
    except KeyError:
        name = '__main__'
    else:
        del kwargs['name']
        if name is None:
            name = '__main__'

    try:
        argv = kwargs['argv']
    except KeyError:
        if not args:
            args = (None,)
    else:
        del kwargs['argv']
        args = (argv,) + args

    if kwargs:
        raise TypeError("Unrecognized keyword arguments for main()")

    if name == '__main__':
        argv, args = args[0], args[1:]
        if argv is None:
            argv = _sys.argv[1:]

        runner = _Runner(*args)
        if argv:
            runner(*argv)
        else:
            runner.print_help()
