#!/usr/bin/env python
# -*- coding: ascii -*-
#
# Copyright 2011, 2012
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
 Benchmark jsmin implementations
=================================

Benchmark jsmin implementations.

Usage::

    bench.py [-c COUNT] jsfile ...

    -c COUNT  number of runs per jsfile and minifier. Defaults to 10.

"""
__author__ = "Andr\xe9 Malo"
__author__ = getattr(__author__, 'decode', lambda x: __author__)('latin-1')
__docformat__ = "restructuredtext en"
__license__ = "Apache License, Version 2.0"
__version__ = "1.0.0"

import sys as _sys
import time as _time

class jsmins(object):
    from bench import jsmin as p_01_simple_port
    if _sys.version_info >= (2, 4):
        from bench import jsmin_2_0_2 as p_02_jsmin_2_0_2
    else:
        print("jsmin_2_0_2 available for python 2.4 and later...")
    if _sys.version_info < (3, 0):
        try:
            import slimit as _slimit_0_7
        except ImportError:
            print("slimit_0_7 not installed for python %d.%d..." %
                _sys.version_info[:2]
            )
        else:
            class p_03_slimit_0_7(object):
                pass
            p_03_slimit_0_7 = p_03_slimit_0_7()
            p_03_slimit_0_7.jsmin = _slimit_0_7.minify
            class p_04_slimit_0_7_mangle(object):
                pass
            p_04_slimit_0_7_mangle = p_04_slimit_0_7_mangle()
            p_04_slimit_0_7_mangle.jsmin = \
                lambda x, s=_slimit_0_7: s.minify(x, True)
    else:
        print("slimit_0_7 not available for python 3...")

    import rjsmin as p_05_rjsmin
    try:
        import _rjsmin as p_06__rjsmin
    except ImportError:
        print("_rjsmin (C-Port) not available")
jsmins.p_05_rjsmin.jsmin = jsmins.p_05_rjsmin._make_jsmin(
    python_only=True
)
print("Python Release: %s" % ".".join(map(str, _sys.version_info[:3])))
print("")


def slurp(filename):
    """ Load a file """
    fp = open(filename)
    try:
        return fp.read()
    finally:
        fp.close()


def print_(*value, **kwargs):
    """ Print stuff """
    (kwargs.get('file') or _sys.stdout).write(
        ''.join(value) + kwargs.get('end', '\n')
    )


def bench(filenames, count):
    """
    Benchmark the minifiers with given javascript samples

    :Parameters:
      `filenames` : sequence
        List of filenames

      `count` : ``int``
        Number of runs per js file and minifier

    :Exceptions:
      - `RuntimeError` : empty filenames sequence
    """
    if not filenames:
        raise RuntimeError("Missing files to benchmark")
    try:
        xrange
    except NameError:
        xrange = range
    try:
        cmp
    except NameError:
        cmp = lambda a, b: (a > b) - (a < b)

    ports = [item for item in dir(jsmins) if item.startswith('p_')]
    ports.sort()
    space = max(map(len, ports)) - 4
    ports = [(item[5:], getattr(jsmins, item).jsmin) for item in ports]
    counted = [None for _ in xrange(count)]
    flush = _sys.stdout.flush

    inputs = [(filename, slurp(filename)) for filename in filenames]
    for filename, script in inputs:
        print_("Benchmarking %r..." % filename, end=" ")
        flush()
        outputs = [jsmin(script) for _, jsmin in ports]
        print_("(%.1f KiB)" % (len(script) / 1024.0))
        flush()
        times = []
        for idx, (name, jsmin) in enumerate(ports):
            print_("  Timing %s%s... (%5.1f KiB %s)" % (
                name,
                " " * (space - len(name)),
                len(outputs[idx]) / 1024.0,
                idx == 0 and '*' or
                    ['=', '>', '<'][cmp(len(outputs[idx]), len(outputs[0]))],
            ), end=" ")
            flush()
            start = _time.time()
            for _ in counted:
                jsmin(script)
            end = _time.time()
            times.append((end - start) * 1000 / count)
            print_("%8.2f ms" % times[-1], end=" ")
            flush()
            if len(times) <= 1:
                print_()
            else:
                print_("(factor: %s)" % (', '.join([
                    '%.2f' % (timed / times[-1]) for timed in times[:-1]
                ])))
            flush()
        print_()


def main(argv):
    """ Main """
    count, idx = 10, 0
    if argv and argv[0] == '-c':
        count, idx = int(argv[1]), 2
    elif argv and argv[0].startswith('-c'):
        count, idx = int(argv[0][2:]), 1
    bench(argv[idx:], count)


if __name__ == '__main__':
    main(_sys.argv[1:])
