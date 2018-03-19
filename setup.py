#!/usr/bin/env python
# -*- coding: ascii -*-
u"""
:Copyright:

 Copyright 2011 - 2019
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

===========================================
 rJSmin - A Javascript Minifier For Python
===========================================

rJSmin - A Javascript Minifier For Python.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import os as _os
import posixpath as _posixpath
import sys as _sys

# pylint: disable = no-name-in-module, import-error
from distutils import ccompiler as _ccompiler
from distutils import core as _core
from distutils import log as _log
from distutils.command import build_ext as _build_ext
import setuptools as _setuptools

# pylint: disable = invalid-name


def _doc(filename):
    """ Read docs file """
    args = {} if str is bytes else dict(encoding='utf-8')
    try:
        with open(_os.path.join('docs', filename), **args) as fp:
            return fp.read()
    except IOError:
        return None


def _lines(multiline):
    """ Split multiline string into single line % empty and comments """
    return [line for line in (
        line.strip() for line in multiline.splitlines(False)
    ) if line and not line.startswith('#')]


package = dict(
    name='rjsmin',
    top='.',
    pathname='.',
    provides=_doc('PROVIDES'),
    desc=_doc('SUMMARY').strip(),
    longdesc=_doc('DESCRIPTION'),
    author=__author__,
    email='nd@perlig.de',
    license="Apache License, Version 2.0",
    keywords=_lines(_doc('KEYWORDS')),
    url='http://opensource.perlig.de/rjsmin/',
    classifiers=_lines(_doc('CLASSIFIERS') or ''),

    install_requires=_lines("""
    """),
)


class build_ext(_build_ext.build_ext):  # pylint: disable = no-init
    """ Improved extension building code """

    def build_extension(self, ext):
        """
        Build C extension - with extended functionality

        The following features are added here:

        - The macros ``EXT_PACKAGE`` and ``EXT_MODULE`` will be filled (or
          unset) depending on the extensions name, but only if they are not
          already defined.

        - "." is added to the include directories (for cext.h)

        :Parameters:
          `ext` : `Extension`
            The extension to build

        :Return: whatever ``distutils.command.build_ext.build_ext`` returns
        :Rtype: any
        """
        # handle name macros
        macros = dict(ext.define_macros or ())
        tup = ext.name.split('.')
        if len(tup) == 1:
            pkg, mod = None, tup[0]
        else:
            pkg, mod = '.'.join(tup[:-1]), tup[-1]
        if pkg is not None and 'EXT_PACKAGE' not in macros:
            ext.define_macros.append(('EXT_PACKAGE', pkg))
        if 'EXT_MODULE' not in macros:
            ext.define_macros.append(('EXT_MODULE', mod))
        if pkg is None:
            macros = dict(ext.undef_macros or ())
            if 'EXT_PACKAGE' not in macros:
                ext.undef_macros.append('EXT_PACKAGE')

        return _build_ext.build_ext.build_extension(self, ext)


class Extension(_core.Extension):
    """ improved functionality """

    def __init__(self, *args, **kwargs):
        """ Initialization """
        self.depends = []
        if 'depends' in kwargs:
            self.depends = kwargs['depends']
        _core.Extension.__init__(self, *args, **kwargs)

        # add include path
        included = '.'
        if included not in self.include_dirs:
            self.include_dirs.append(included)

        # add cext.h to the dependencies
        cext_h = _posixpath.normpath(_posixpath.join(included, 'cext.h'))
        for item in self.depends:
            if _posixpath.normpath(item) == cext_h:
                break
        else:
            self.depends.append(cext_h)


EXTENSIONS = [Extension('_rjsmin', ["rjsmin.c"])]


def setup():
    """ Main """
    # pylint: disable = too-many-branches

    with open('rjsmin.py') as fp:
        for line in fp:  # pylint: disable = redefined-outer-name
            if line.startswith('__version__'):
                version = line.split('=', 1)[1].strip()
                if version.startswith(("'", '"')):
                    version = version[1:-1].strip()
                break
        else:
            raise RuntimeError("Version not found")

    if 'java' in _sys.platform.lower():
        EXTENSIONS[:] = []

    if EXTENSIONS:
        gcov = False
        if _os.environ.get('CFLAGS') is None:
            compiler = _ccompiler.get_default_compiler()
            try:
                with open("debug.%s.cflags" % compiler) as fp:
                    cflags = ' '.join([
                        line for line in (line.strip() for line in fp)
                        if line and not line.startswith('#')
                    ]) or None
            except IOError:
                pass
            else:
                if cflags is not None:
                    # pylint: disable = unsupported-membership-test
                    if 'coverage' in cflags:
                        gcov = True
                    _log.info("Setting CFLAGS to %r", cflags)
                    _os.environ['CFLAGS'] = cflags

        if gcov:
            for ext in EXTENSIONS:
                ext.libraries.append('gcov')

    packages = [package['top']] + [
        '%s.%s' % (package['top'], item)
        for item in
        _setuptools.find_packages(package['pathname'])
    ]

    _core.setup(
        cmdclass={'build_ext': build_ext},
        name=package['name'],
        author=package['author'],
        author_email=package['email'],
        license=package['license'],
        classifiers=package['classifiers'],
        description=package['desc'],
        long_description=package['longdesc'],
        url=package['url'],
        ext_modules=EXTENSIONS,
        install_requires=package['install_requires'],
        # packages=packages,
        py_modules=['rjsmin'],
        version=version,
        zip_safe=False,
    )


if __name__ == '__main__':
    setup()
