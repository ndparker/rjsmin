#!/usr/bin/env python
# -*- coding: ascii -*-
r"""
=========================
 Write benchmark results
=========================

Write benchmark results.

:Copyright:

 Copyright 2014
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

Usage::

    python -mbench.write -p plain-file <pickled

    -p plain-file  Plain file to write to (like docs/BENCHAMRKS).

"""
if __doc__:
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"
__license__ = "Apache License, Version 2.0"
__version__ = "1.0.0"

import sys as _sys


def write_plain(filename, results):
    """
    Output plain benchmark results

    :Parameters:
      `filename` : ``str``
        Filename to write to

      `results` : ``list``
        Results
    """
    try:
        unicode
    except NameError:
        def uni(v):
            if hasattr(v, 'decode'):
                return v.decode('latin-1')
            return str(v)
    else:
        def uni(v):
            if isinstance(v, unicode):
                return v.encode('utf-8')
            return str(v)

    lines = []
    results = sorted(results, reverse=True)
    for idx, (version, import_notes, result) in enumerate(results):
        if idx:
            lines.append('')
            lines.append('')

        lines.append('$ python%s -OO bench/main.py bench/*.js' % (
            '.'.join(version.split('.')[:2])
        ))
        lines.append('~' * 72)
        for note in import_notes:
            lines.append(uni(note))
        lines.append('Python Release: %s' % (version,))

        for single in result:
            lines.append('')
            lines.append('Benchmarking %r... (%.1f KiB)' % (
                uni(single['filename']), single['size'] / 1024.0
            ))
            for msg in single['messages']:
                lines.append(msg)
            times = []
            space = max([len(uni(port)) for port, _ in single['times']])
            for idx, (port, time) in enumerate(single['times']):
                port = uni(port)
                if time is None:
                    lines.append("  FAILED %s" % (port,))
                else:
                    times.append(time)
                    lines.append(
                        "  Timing %s%s ... (%5.1f KiB %s) %8.2f ms" % (
                            port,
                            " " * (space - len(port)),
                            single['sizes'][idx] / 1024.0,
                            idx == 0 and '*' or ['=', '>', '<'][
                                cmp(single['sizes'][idx], single['sizes'][0])
                            ],
                            time
                        )
                    )
                    if len(times) > 1:
                        lines[-1] += " (factor: %s)" % (', '.join([
                            '%.2f' % (timed / time) for timed in times[:-1]
                        ]))

    lines.append('')
    lines.append('')
    lines.append('# vim: nowrap')
    fp = open(filename, 'w')
    try:
        fp.write('\n'.join(lines) + '\n')
    finally:
        fp.close()


def main(argv=None):
    """ Main """
    import getopt as _getopt
    import os as _os
    import pickle as _pickle

    if argv is None:
        argv = _sys.argv[1:]
    try:
        opts, args = _getopt.getopt(argv, "hp:", ["help"])
    except getopt.GetoptError:
        e = _sys.exc_info()[0](_sys.exc_info()[1])
        print >> _sys.stderr, "%s\nTry %s -mbench.write --help" % (
            e,
            _os.path.basename(_sys.executable),
        )
        _sys.exit(2)

    plain = None
    for key, value in opts:
        if key in ("-h", "--help"):
            print >> _sys.stderr, (
                "%s -mbench.write [-p plain-file] <pickled" % (
                    _os.path.basename(_sys.executable),
                )
            )
            _sys.exit(0)
        elif key == '-p':
            plain = str(value)

    struct = []
    try:
        while True:
            version, import_notes, result = _pickle.load(_sys.stdin)
            if hasattr(version, 'decode'):
                version = version.decode('latin-1')
            struct.append((version, import_notes, result))
    except EOFError:
        pass

    if plain:
        write_plain(plain, struct)


if __name__ == '__main__':
    main()
