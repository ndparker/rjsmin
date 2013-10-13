# -*- coding: ascii -*-
#
# Copyright 2007 - 2013
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
 Standard targets
==================

Standard targets.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import os as _os
import sys as _sys

from _setup import dist as _dist
from _setup import make as _make
from _setup import shell as _shell
from _setup import term as _term


class Distribution(_make.Target):
    """ Build a distribution """
    NAME = "dist"
    DEPS = ["MANIFEST"]

    _dist, _ebuilds, _changes = None, None, None

    def init(self):
        raise NotImplementedError()

    def run(self):
        exts = self.dist_pkg()
        digests = self.digest_files(exts)
        self.sign_digests(digests)
        self.copy_ebuilds()
        self.copy_changes()

    def dist_pkg(self):
        _term.green("Building package...")
        _dist.run_setup("sdist", "--formats", "tar,zip",
            fakeroot=_shell.frompath('fakeroot')
        )
        exts = ['.zip']
        for name in _shell.files(self._dist, '*.tar', False):
            exts.extend(self.compress(name))
            _shell.rm(name)
        return exts

    def compress(self, filename):
        """ Compress file """
        ext = _os.path.splitext(filename)[1]
        exts = []
        exts.append('.'.join((ext, self.compress_gzip(filename))))
        exts.append('.'.join((ext, self.compress_bzip2(filename))))
        exts.append('.'.join((ext, self.compress_xz(filename))))
        return exts

    def compress_xz(self, filename):
        outfilename = filename + '.xz'
        self.compress_external(filename, outfilename, 'xz', '-c9')
        return 'xz'

    def compress_bzip2(self, filename):
        outfilename = filename + '.bz2'
        try:
            import bz2 as _bz2
        except ImportError:
            self.compress_external(filename, outfilename, 'bzip2', '-c9')
        else:
            outfile = _bz2.BZ2File(outfilename, 'w')
            self.compress_internal(filename, outfile, outfilename)
        return 'bz2'

    def compress_gzip(self, filename):
        outfilename = filename + '.gz'
        try:
            import gzip as _gzip
        except ImportError:
            self.compress_external(filename, outfilename, 'gzip', '-c9')
        else:
            outfile = _gzip.GzipFile(filename, 'wb',
                fileobj=open(outfilename, 'wb')
            )
            self.compress_internal(filename, outfile, outfilename)
        return 'gz'

    def compress_external(self, infile, outfile, *argv):
        argv = list(argv)
        argv[0] = _shell.frompath(argv[0])
        if argv[0] is not None:
            return not _shell.spawn(*argv, **{
                'filepipe': True, 'stdin': infile, 'stdout': outfile,
            })
        return None

    def compress_internal(self, filename, outfile, outfilename):
        infile = open(filename, 'rb')
        try:
            try:
                while 1:
                    chunk = infile.read(8192)
                    if not chunk:
                        break
                    outfile.write(chunk)
                outfile.close()
            except:
                e = _sys.exc_info()
                try:
                    _shell.rm(outfilename)
                finally:
                    try:
                        raise e[0], e[1], e[2]
                    finally:
                        del e
        finally:
            infile.close()

    def digest_files(self, exts):
        """ digest files """
        digests = {}
        digestnames = {}
        for ext in exts:
            for name in _shell.files(self._dist, '*' + ext, False):
                basename = _os.path.basename(name)
                if basename not in digests:
                    digests[basename] = []
                digests[basename].extend(self.digest(name))
                digestname = basename[:-len(ext)]
                if digestname not in digestnames:
                    digestnames[digestname] = []
                digestnames[digestname].append(basename)

        result = []
        for name, basenames in digestnames.items():
            result.append(_os.path.join(self._dist, name + '.digests'))
            fp = open(result[-1], 'wb')
            try:
                fp.write(
                    '\n# The file may contain MD5, SHA1 and SHA256 digests\n'
                )
                fp.write('# Check archive integrity with, e.g. md5sum -c\n')
                fp.write('# Check digest file integrity with PGP\n\n')
                basenames.sort()
                for basename in basenames:
                    for digest in digests[basename]:
                        fp.write("%s *%s\n" % (digest, basename))
            finally:
                fp.close()
        return result

    def digest(self, filename):
        result = []
        for method in (self.md5, self.sha1, self.sha256):
            digest = method(filename)
            if digest is not None:
                result.append(digest)
        return result

    def do_digest(self, hashfunc, name, filename):
        filename = _shell.native(filename)
        _term.green("%(digest)s-digesting %(name)s...",
            digest=name, name=_os.path.basename(filename))
        fp = open(filename, 'rb')
        sig = hashfunc()
        block = fp.read(8192)
        while block:
            sig.update(block)
            block = fp.read(8192)
        fp.close()
        return sig.hexdigest()

        param = {'sig': sig.hexdigest(), 'file': _os.path.basename(filename)}
        fp = open("%s.%s" % (filename, name), "w")
        fp.write("%(sig)s *%(file)s\n" % param)
        fp.close()

        return True

    def md5(self, filename):
        try:
            from hashlib import md5
        except ImportError:
            try:
                from md5 import new as md5
            except ImportError:
                _make.warn("md5 not found -> skip md5 digests", self.NAME)
                return None
        return self.do_digest(md5, "md5", filename)

    def sha1(self, filename):
        try:
            from hashlib import sha1
        except ImportError:
            try:
                from sha import new as sha1
            except ImportError:
                _make.warn("sha1 not found -> skip sha1 digests", self.NAME)
                return None
        return self.do_digest(sha1, "sha1", filename)

    def sha256(self, filename):
        try:
            from hashlib import sha256
        except ImportError:
            try:
                from Crypto.Hash.SHA256 import new as sha256
            except ImportError:
                _make.warn(
                    "sha256 not found -> skip sha256 digests", self.NAME
                )
                return None
        return self.do_digest(sha256, "sha256", filename)

    def copy_ebuilds(self):
        if self._ebuilds is not None:
            for src in _shell.files(self._ebuilds, '*.ebuild'):
                _shell.cp(src, self._dist)

    def copy_changes(self):
        if self._changes is not None:
            _shell.cp(self._changes, self._dist)

    def sign_digests(self, digests):
        for digest in digests:
            self.sign(digest, detach=False)

    def sign(self, filename, detach=True):
        filename = _shell.native(filename)
        try:
            from pyme import core, errors
            from pyme.constants.sig import mode
        except ImportError:
            return self.sign_external(filename, detach=detach)

        _term.green("signing %(name)s...", name=_os.path.basename(filename))
        sigmode = [mode.CLEAR, mode.DETACH][bool(detach)]
        fp = core.Data(file=filename)
        sig = core.Data()
        try:
            c = core.Context()
        except errors.GPGMEError:
            return self.sign_external(filename, detach=detach)
        c.set_armor(1)
        try:
            c.op_sign(fp, sig, sigmode)
        except errors.GPGMEError, e:
            _make.fail(str(e))

        sig.seek(0, 0)
        if detach:
            open("%s.asc" % filename, "w").write(sig.read())
        else:
            open(filename, "w").write(sig.read())

        return True

    def sign_external(self, filename, detach=True):
        """ Sign calling gpg """
        gpg = _shell.frompath('gpg')
        if gpg is None:
            _make.warn('GPG not found -> cannot sign')
            return False
        if detach:
            _shell.spawn(gpg,
                '--armor',
                '--output', filename + '.asc',
                '--detach-sign',
                '--',
                filename,
            )
        else:
            _shell.spawn(gpg,
                '--output', filename + '.signed',
                '--clearsign',
                '--',
                filename,
            )
            _os.rename(filename + '.signed', filename)
        return True

    def clean(self, scm, dist):
        _term.green("Removing dist files...")
        _shell.rm_rf(self._dist)


class Manifest(_make.Target):
    """ Create manifest """
    NAME = "MANIFEST"
    HIDDEN = True
    DEPS = ["doc"]

    def run(self):
        _term.green("Creating %(name)s...", name=self.NAME)
        dest = _shell.native(self.NAME)
        dest = open(dest, 'w')
        for name in self.manifest_names():
            dest.write("%s\n" % name)
        dest.close()

    def manifest_names(self):
        import setup
        for item in setup.manifest():
            yield item

    def clean(self, scm, dist):
        """ Clean manifest """
        if scm:
            _term.green("Removing MANIFEST")
            _shell.rm(self.NAME)
