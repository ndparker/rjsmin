# -*- encoding: ascii -*-
"""
invoke tasks
~~~~~~~~~~~~

"""


def namespace():
    """ Create invoke task namespace """

    class adict(object):
        """ attribute dict """
        # pylint: disable = invalid-name, missing-docstring

        def __init__(self, *args, **kwargs):
            self.__x__ = dict(*args, **kwargs)

        def __getitem__(self, name):
            return self.__x__[name]

        def __getattr__(self, name):
            if name == '__setstate__':
                raise AttributeError(name)
            try:
                return self.__x__[name]
            except KeyError:
                raise AttributeError(name)

        def items(self):
            return self.__x__.items()

    import os as _os
    import sys as _sys

    from . import _shell

    def fail(msg):
        """ Exit with message """
        _sys.stderr.write('Error: %s\n' % (msg,))
        raise _invoke.Exit(1)

    env = adict(
        package='rjsmin',
        test=adict(ignore=[]),
        doc=adict(
            userdoc="docs/userdoc",
            website=adict(
                source="docs/website",
                target="dist/website",
            ),

            sphinx=adict(
                build='docs/_userdoc/_build',
                source='docs/_userdoc',
            ),
        ),
        wheels=dict(
            build="binary",
            specs={
                "aarch64": {
                    "36": "2014",
                    "37": "2014",
                    "38": "2014",
                    "39": "2014",
                    "310": "2014",
                    "311": "2014",
                },
                "x86_64": {
                    "27": "1",
                    "36": "1",
                    "37": "1",
                    "38": "1",
                    "39": "1",
                    "310": "2010",
                    "311": "2014",
                },
                "i686": {
                    "27": "1",
                    "36": "1",
                    "37": "1",
                    "38": "1",
                    "39": "1",
                    "310": "2010",
                    "311": "2014",
                },
            },
        ),
        pypi=adict(
            # repository='https://test.pypi.org/legacy/',
            repository='https://upload.pypi.org/legacy/',
            username='__token__',
        ),

        shell=adict((key, value) for key, value in vars(_shell).items()
                    if not key.startswith('_')),
        c=_shell.command,
        q=lambda x: _shell.command('%s', x),
        fail=fail,
    )

    _sys.path.insert(0, _os.path.dirname(
        _os.path.dirname(_os.path.abspath(__file__))
    ))

    class Vars(object):
        """ Submodules container """
        from . import (  # noqa
            benchmark,
            build,
            check,
            clean,
            compile,
            deps,
            doc,
            test,
            upload,
        )

    import invoke as _invoke

    result = _invoke.Collection(*[value for key, value in vars(Vars).items()
                                  if not key.startswith('__')])
    result.configure(env)
    return result

namespace = namespace()
