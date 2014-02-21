#!/usr/bin/env python
# -*- coding: ascii -*-
#
# Copyright 2006 - 2013
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
===============
 Build targets
===============

Build targets.
"""
__author__ = "Andr\xe9 Malo"
__author__ = getattr(__author__, 'decode', lambda x: __author__)('latin-1')
__docformat__ = "restructuredtext en"

import errno as _errno
import os as _os
import re as _re
import sys as _sys

from _setup import dist
from _setup import shell
from _setup import make
from _setup import term
from _setup.make import targets, default_targets


class Target(make.Target):
    def init(self):
        self.dirs = {
            'lib': '.',
            'docs': 'docs',
            'apidoc': 'docs/apidoc',
            'userdoc': 'docs/userdoc',
            'userdoc_source': 'docs/_userdoc',
            'userdoc_build': 'docs/_userdoc/_build',
            'website': 'dist/website',
            '_website': '_website', # source dir
            'dist': 'dist',
            'build': 'build',
            'bench': 'bench',
            'ebuild': '_pkg/ebuilds',
        }
        libpath = shell.native(self.dirs['lib'])
        if libpath != _sys.path[0]:
            while libpath in _sys.path:
                _sys.path.remove(libpath)
            _sys.path.insert(0, libpath)

        self.ebuild_files = {
            'rjsmin.ebuild.in':
                'rjsmin-%(VERSION)s.ebuild',
        }


Manifest = targets.Manifest

class Distribution(targets.Distribution):
    def init(self):
        self._dist = 'dist'
        self._ebuilds = '_pkg/ebuilds'
        self._changes = 'docs/CHANGES'


class MakefileTarget(default_targets.MakefileTarget):
    def extend(self, names):
        names.append('jsmin')
        return '\n\n'.join([
            'jsmin: bench/jsmin',
            'bench/jsmin: bench/jsmin.c\n\tgcc -o bench/jsmin bench/jsmin.c',
        ])


class Benchmark(Target):
    """ Benchmark """
    NAME = "bench"
    DEPS = ["compile-quiet"]
    python = None

    def run(self):
        files = list(shell.files(self.dirs['bench'], '*.js'))
        if self.python is None:
            python = _sys.executable
        else:
            python = shell.frompath(self.python)
        return not shell.spawn(*[
            python,
            '-mbench.main',
            '-c10',
        ] + files)

    def clean(self, scm, dist):
        term.green("Removing bytecode files...")
        for filename in shell.dirs('.', '__pycache__'):
            shell.rm_rf(filename)
        for filename in shell.files('.', '*.py[co]'):
            shell.rm(filename)
        for filename in shell.files('.', '*$py.class'):
            shell.rm(filename)
        shell.rm(shell.native('bench/jsmin'))


class Check(Target):
    """ Check the python code """
    NAME = "check"
    DEPS = ["compile-quiet"]

    def run(self):
        from _setup.dev import analysis
        term.green('Linting rjsmin sources...')
        res = analysis.pylint('_pkg/pylint.conf', 'rjsmin')
        if res == 2:
            make.warn('pylint not found', self.NAME)


class Compile(Target):
    """ Compile the python code """
    NAME = "compile"
    #DEPS = None

    def run(self):
        import setup

        _old_argv = _sys.argv
        try:
            _sys.argv = ['setup.py', '-q', 'build']
            if not self.HIDDEN:
                _sys.argv.remove('-q')
            setup.setup()
            if 'java' not in _sys.platform.lower():
                _sys.argv = [
                    'setup.py', '-q', 'install_lib', '--install-dir',
                    shell.native(self.dirs['lib']),
                    '--optimize', '2',
                ]
                if not self.HIDDEN:
                    _sys.argv.remove('-q')
                setup.setup()
        finally:
            _sys.argv = _old_argv

        self.compile('rjsmin.py')
        term.write("%(ERASE)s")

        term.green("All files successfully compiled.")

    def compile(self, name):
        path = shell.native(name)
        term.write("%(ERASE)s%(BOLD)s>>> Compiling %(name)s...%(NORMAL)s",
            name=name)
        from distutils import util
        try:
            from distutils import log
        except ImportError:
            util.byte_compile([path], verbose=0, force=True)
        else:
            log.set_verbosity(0)
            util.byte_compile([path], force=True)

    def clean(self, scm, dist):
        term.green("Removing python byte code...")
        for name in shell.dirs('.', '__pycache__'):
            shell.rm_rf(name)
        for name in shell.files('.', '*.py[co]'):
            shell.rm(name)

        term.green("Removing c extensions...")
        for name in shell.files('.', '*.so'):
            shell.rm(name)
        for name in shell.files('.', '*.pyd'):
            shell.rm(name)

        shell.rm_rf(self.dirs['build'])


class CompileQuiet(Compile):
    NAME = "compile-quiet"
    HIDDEN = True

    def clean(self, scm, dist):
        pass


class Doc(Target):
    """ Build the docs (api + user) """
    NAME = "doc"
    DEPS = ['apidoc', 'userdoc']


class ApiDoc(Target):
    """ Build the API docs """
    NAME = "apidoc"

    def run(self):
        from _setup.dev import apidoc
        apidoc.epydoc(
            prepend=[
                shell.native(self.dirs['lib']),
            ],
        )

    def clean(self, scm, dist):
        if scm:
            term.green("Removing apidocs...")
            shell.rm_rf(self.dirs['apidoc'])


class UserDoc(Target):
    """ Build the user docs """
    NAME = "userdoc"
    #DEPS = None

    def run(self):
        from _setup.dev import userdoc
        userdoc.sphinx(
            build=shell.native(self.dirs['userdoc_build']),
            source=shell.native(self.dirs['userdoc_source']),
            target=shell.native(self.dirs['userdoc']),
        )

    def clean(self, scm, dist):
        if scm:
            term.green("Removing userdocs...")
            shell.rm_rf(self.dirs['userdoc'])
        shell.rm_rf(self.dirs['userdoc_build'])


class Website(Target):
    """ Build the website """
    NAME = "website"
    DEPS = ["apidoc"]

    def run(self):
        from _setup.util import SafeConfigParser as parser
        parser = parser()
        parser.read('package.cfg')
        strversion = parser.get('package', 'version.number')
        shortversion = tuple(map(int, strversion.split('.')[:2]))

        shell.rm_rf(self.dirs['_website'])
        shell.cp_r(
            self.dirs['userdoc_source'],
            _os.path.join(self.dirs['_website'], 'src')
        )
        shell.rm_rf(_os.path.join(self.dirs['_website'], 'build'))
        shell.rm_rf(self.dirs['website'])
        _os.makedirs(self.dirs['website'])
        filename = _os.path.join(
            self.dirs['_website'], 'src', 'website_download.txt'
        )
        fp = open(filename)
        try:
            download = fp.read()
        finally:
            fp.close()
        filename = _os.path.join(self.dirs['_website'], 'src', 'index.txt')
        fp = open(filename)
        try:
            indexlines = fp.readlines()
        finally:
            fp.close()

        fp = open(filename, 'w')
        try:
            for line in indexlines:
                if line.startswith('.. placeholder: Download'):
                    line = download
                fp.write(line)
        finally:
            fp.close()

        shell.cp_r(
            self.dirs['apidoc'],
            _os.path.join(self.dirs['website'], 'doc-%d.%d' % shortversion)
        )
        shell.cp_r(
            self.dirs['apidoc'],
            _os.path.join(
                self.dirs['_website'], 'src', 'doc-%d.%d' % shortversion
            )
        )
        fp = open(_os.path.join(
            self.dirs['_website'], 'src', 'conf.py'
        ), 'a')
        try:
            fp.write("\nepydoc = dict(rjsmin=%r)\n" % (
                _os.path.join(
                    shell.native(self.dirs['_website']),
                    "src",
                    "doc-%d.%d" % shortversion,
                ),
            ))
            fp.write("\nexclude_trees.append(%r)\n" %
                "doc-%d.%d" % shortversion
            )
        finally:
            fp.close()
        from _setup.dev import userdoc
        userdoc.sphinx(
            build=shell.native(_os.path.join(self.dirs['_website'], 'build')),
            source=shell.native(_os.path.join(self.dirs['_website'], 'src')),
            target=shell.native(self.dirs['website']),
        )
        shell.rm(_os.path.join(self.dirs['website'], '.buildinfo'))

    def clean(self, scm, dist):
        if scm:
            term.green("Removing website...")
            shell.rm_rf(self.dirs['website'])
        shell.rm_rf(self.dirs['_website'])


class PreCheck(Target):
    """ Run clean, doc, check """
    NAME = "precheck"
    DEPS = ["clean", "doc", "check"]


class SVNRelease(Target):
    """ Release current version """
    #NAME = "release"
    DEPS = None

    def run(self):
        self._check_committed()
        self._update_versions()
        self._tag_release()
        self.runner('dist', seen={})

    def _tag_release(self):
        """ Tag release """
        from _setup.util import SafeConfigParser as parser
        parser = parser()
        parser.read('package.cfg')
        strversion = parser.get('package', 'version.number')
        version = strversion
        trunk_url = self._repo_url()
        if not trunk_url.endswith('/trunk'):
            rex = _re.compile(r'/branches/\d+(?:\.\d+)*\.[xX]$').search
            match = rex(trunk_url)
            if not match:
                make.fail("Not in trunk or release branch!")
            found = match.start(0)
        else:
            found = -len('/trunk')
        release_url = trunk_url[:found] + '/releases/' + version

        svn = shell.frompath('svn')
        shell.spawn(
            svn, 'copy', '-m', 'Release version ' + version, '--',
            trunk_url, release_url,
            echo=True,
        )

    def _update_versions(self):
        """ Update versions """
        self.runner('version', seen={})
        svn = shell.frompath('svn')
        shell.spawn(svn, 'commit', '-m', 'Pre-release: version update',
            echo=True
        )

    def _repo_url(self):
        """ Determine URL """
        from xml.dom import minidom
        svn = shell.frompath('svn')
        info = minidom.parseString(
            shell.spawn(svn, 'info', '--xml', stdout=True)
        )
        try:
            url = info.getElementsByTagName('url')[0]
            text = []
            for node in url.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    text.append(node.data)
        finally:
            info.unlink()
        return ''.join(text).encode('utf-8')

    def _check_committed(self):
        """ Check if everything is committed """
        if not self._repo_url().endswith('/trunk'):
            rex = _re.compile(r'/branches/\d+(?:\.\d+)*\.[xX]$').search
            match = rex(self._repo_url())
            if not match:
                make.fail("Not in trunk or release branch!")
        svn = shell.frompath('svn')
        lines = shell.spawn(svn, 'stat', '--ignore-externals',
            stdout=True, env=dict(_os.environ, LC_ALL='C'),
        ).splitlines()
        for line in lines:
            if line.startswith('X'):
                continue
            make.fail("Uncommitted changes!")


class GitRelease(Target):
    """ Release current version """
    #NAME = "release"
    DEPS = None

    def run(self):
        self._check_committed()
        self._update_versions()
        self._tag_release()
        self.runner('dist', seen={})

    def _tag_release(self):
        """ Tag release """
        from _setup.util import SafeConfigParser as parser
        parser = parser()
        parser.read('package.cfg')
        strversion = parser.get('package', 'version.number')
        version = strversion
        git = shell.frompath('git')
        shell.spawn(
            git, 'tag', '-a', '-m', 'Release version ' + version, '--',
            version,
            echo=True,
        )

    def _update_versions(self):
        """ Update versions """
        self.runner('version', seen={})
        git = shell.frompath('git')
        shell.spawn(git, 'commit', '-a', '-m', 'Pre-release: version update',
            echo=True
        )

    def _check_committed(self):
        """ Check if everything is committed """
        git = shell.frompath('git')
        lines = shell.spawn(git, 'branch', '--color=never',
            stdout=True, env=dict(_os.environ, LC_ALL='C')
        ).splitlines()
        for line in lines:
            if line.startswith('*'):
                branch = line.split(None, 1)[1]
                break
        else:
            make.fail("Could not determine current branch.")
        if branch != 'master':
            rex = _re.compile(r'^\d+(?:\.\d+)*\.[xX]$').match
            match = rex(branch)
            if not match:
                make.fail("Not in master or release branch.")

        lines = shell.spawn(git, 'status', '--porcelain',
            stdout=True, env=dict(_os.environ, LC_ALL='C'),
        )
        if lines:
            make.fail("Uncommitted changes!")


class Release(GitRelease):
    NAME = "release"
    #DEPS = None


class Version(Target):
    """ Insert the program version into all relevant files """
    NAME = "version"
    #DEPS = None

    def run(self):
        from _setup.util import SafeConfigParser as parser
        parser = parser()
        parser.read('package.cfg')
        strversion = parser.get('package', 'version.number')

        self._version_init(strversion)
        self._version_userdoc(strversion)
        self._version_download(strversion)
        self._version_changes(strversion)

        parm = {'VERSION': strversion}
        for src, dest in self.ebuild_files.items():
            src = "%s/%s" % (self.dirs['ebuild'], src)
            dest = "%s/%s" % (self.dirs['ebuild'], dest % parm)
            term.green("Creating %(name)s...", name=dest)
            shell.cp(src, dest)

    def _version_init(self, strversion):
        """ Modify version in __init__ """
        filename = _os.path.join(self.dirs['lib'], 'rjsmin.py')
        fp = open(filename)
        try:
            initlines = fp.readlines()
        finally:
            fp.close()
        fp = open(filename, 'w')
        replaced = False
        try:
            for line in initlines:
                if line.startswith('__version__'):
                    line = '__version__ = %r\n' % (strversion,)
                    replaced = True
                fp.write(line)
        finally:
            fp.close()
        assert replaced, "__version__ not found in rjsmin.py"

    def _version_changes(self, strversion):
        """ Modify version in changes """
        filename = _os.path.join(shell.native(self.dirs['docs']), 'CHANGES')
        fp = open(filename)
        try:
            initlines = fp.readlines()
        finally:
            fp.close()
        fp = open(filename, 'w')
        try:
            for line in initlines:
                if line.rstrip() == "Changes with version":
                    line = "%s %s\n" % (line.rstrip(), strversion)
                fp.write(line)
        finally:
            fp.close()

    def _version_userdoc(self, strversion):
        """ Modify version in userdoc """
        filename = _os.path.join(self.dirs['userdoc_source'], 'conf.py')
        shortversion = '.'.join(strversion.split('.')[:2])
        longversion = strversion
        fp = open(filename)
        try:
            initlines = fp.readlines()
        finally:
            fp.close()
        replaced = 0
        fp = open(filename, 'w')
        try:
            for line in initlines:
                if line.startswith('version'):
                    line = 'version = %r\n' % shortversion
                    replaced |= 1
                elif line.startswith('release'):
                    line = 'release = %r\n' % longversion
                    replaced |= 2
                fp.write(line)
        finally:
            fp.close()
        assert replaced & 3 != 0, "version/release not found in conf.py"

    def _version_download(self, strversion):
        """ Modify version in website download docs """
        filename = _os.path.join(
            self.dirs['userdoc_source'], 'website_download.txt'
        )
        VERSION, PATH = strversion, ''
        fp = open(filename + '.in')
        try:
            dllines = fp.readlines()
        finally:
            fp.close()
        instable = []
        fp = open(filename, 'w')
        try:
            for line in dllines:
                if instable:
                    instable.append(line)
                    if line.startswith('.. end stable'):
                        res = (''.join(instable)
                            .replace('@@VERSION@@', strversion)
                            .replace('@@PATH@@', '')
                        )
                        fp.write(res)
                        instable = []
                elif line.startswith('.. begin stable'):
                    instable.append(line)
                else:
                    fp.write(line
                        .replace('@@VERSION@@', VERSION)
                        .replace('@@PATH@@', PATH)
                    )
        finally:
            fp.close()

    def clean(self, scm, dist):
        """ Clean versioned files """
        if scm:
            term.green("Removing generated ebuild files")
            for name in shell.files(self.dirs['ebuild'], '*.ebuild'):
                shell.rm(name)


make.main(name=__name__)
