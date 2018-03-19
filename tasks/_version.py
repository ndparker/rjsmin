# -*- encoding: ascii -*-
"""
Release code
~~~~~~~~~~~~

"""

import errno as _errno
import os as _os


def update(ctx):
    """ Update version in relevant places """
    version = ctx.run('python setup.py --version', hide=True).stdout.strip()

    _userdoc(ctx, version)
    _download(ctx, version)
    _changes(ctx, version)


def _userdoc(ctx, version):
    """ Update version in userdoc """
    short = '.'.join(version.split('.')[:2])
    conf = _os.path.join(ctx.doc.sphinx.source, 'conf.py')

    with open(conf, 'rb') as fp:
        lines = fp.read().decode('latin-1').splitlines(True)

    seen = set()
    with open(conf, 'wb') as fp:
        for line in lines:
            if line.startswith('version'):
                line = u'version = %r\n' % (short,)
                seen.add('version')
            elif line.startswith('release'):
                line = u'release = %r\n' % (version,)
                seen.add('release')
            fp.write(line.encode('latin-1'))

    assert len(seen) == 2, "version/release not found in userdoc/conf.py"


def _download(ctx, version):  # noqa
    """ Update version in download files """
    # pylint: disable = too-many-branches, too-many-statements

    filename = _os.path.join(ctx.doc.sphinx.source, 'website_download.txt')
    isdev = 'dev' in version

    dllines, dlpath = [], ''
    if isdev:
        oldstable, hasstable = [], False
        try:
            with open(filename, 'rb') as fp:
                lines = fp.read().decode('latin-1').splitlines(True)
        except IOError as e:
            if e.errno != _errno.ENOENT:
                raise
        else:
            for line in lines:
                if line.startswith('.. begin stable'):
                    hasstable, dllines = True, oldstable
                oldstable.append(line)
        if not hasstable:
            dlpath = 'dev/'

    newdev = []
    with open(filename + '.in', 'rb') as fp:
        lines = fp.read().decode('latin-1').splitlines(True)
    if not dllines:
        dllines = lines
    else:
        for line in lines:
            if newdev:
                newdev.append(line)
                if line.startswith('.. end dev'):
                    break
            elif line.startswith('.. begin dev'):
                newdev.append(line)
        else:
            ctx.fail("Incomplete/missing dev marker in %s"
                     % (filename + '.in',))

    instable, indev = [], []
    with open(filename, 'wb') as fp:
        for line in dllines:
            if instable:
                instable.append(line)
                if line.startswith('.. end stable'):
                    if isdev:
                        res = ''.join(instable) if hasstable else ''
                    else:
                        res = (
                            ''.join(instable)
                            .replace('@@VERSION@@', version)
                            .replace('@@PATH@@', '')
                        )
                    fp.write(res.encode('latin-1'))
                    instable = []
            elif indev:
                indev.append(line)
                if line.startswith('.. end dev'):
                    if not isdev:
                        res = ''.join([indev[0], indev[-1]])
                    else:
                        res = (
                            ''.join(newdev or indev)
                            .replace('@@DEVVERSION@@', version)
                            .replace('@@PATH@@', 'dev/')
                        )
                    fp.write(res.encode('latin-1'))
                    indev = []
            elif line.startswith('.. begin stable'):
                instable.append(line)
            elif line.startswith('.. begin dev'):
                indev.append(line)
            elif isdev and hasstable:
                fp.write(line.encode('latin-1'))
            else:
                fp.write(line
                         .replace('@@VERSION@@', version)
                         .replace('@@PATH@@', dlpath)
                         .encode('latin-1'))


def _changes(ctx, version):
    """ Update version in CHANGES """
    fname = ctx.shell.native('docs/CHANGES')
    with open(fname, 'rb') as fp:
        lines = fp.read().decode('latin-1').splitlines(True)

    with open(fname, 'wb') as fp:
        for line in lines:
            if line.rstrip() == 'Changes with version':
                line = "%s %s\n" % (line.rstrip(), version)
            fp.write(line.encode('latin-1'))
