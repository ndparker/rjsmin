# -*- encoding: ascii -*-
"""
Dist building code
~~~~~~~~~~~~~~~~~~

"""

import os as _os


def compress(ctx, filename, cmd, ext):
    """ Compress tar file """
    prog = ctx.shell.frompath(cmd)
    if prog is None:
        return None

    ctx.run('%s -c9 <%s >%s'
            % (ctx.q(prog), ctx.q(filename), ctx.q(filename + ext)),
            echo=True)
    return filename + ext


def digest(ctx, files, digestname):
    """ Make digest file """
    import hashlib as _hashlib

    result = {}
    for filename in files:
        basename = _os.path.basename(filename)
        result[basename] = []
        for method in ('md5', 'sha1', 'sha256'):
            sign = getattr(_hashlib, method)()
            with open(filename, 'rb') as fp:
                for block in iter(lambda fp=fp: fp.read(8192), b''):
                    sign.update(block)
            result[basename].append(sign.hexdigest())

    with open(digestname, 'wb') as fp:
        fp.write(b'\n# The file contains MD5, SHA1 and SHA256 digests\n')
        fp.write(b'# Check archive integrity with, e.g. md5sum -c\n')
        fp.write(b'# Check digest file integrity with PGP\n\n')

        for basename, digests in sorted(result.items()):
            for sign in digests:
                fp.write(("%s *%s\n" % (sign, basename)).encode('utf-8'))

    _sign_inline(ctx, digestname)


def _sign_inline(ctx, filename):
    """ Sign file (inline) """
    gpg = ctx.shell.frompath('gpg')
    ctx.run(ctx.c('''
        %s --output %s --clearsign -- %s
    ''', gpg, filename + '.signed', filename), echo=True)
    _os.rename(filename + '.signed', filename)


def copy_changes(ctx):
    """ Copy changelog """
    version = ctx.run('python setup.py --version', hide=True).stdout.strip()
    from_ = 'docs/CHANGES'
    to_ = 'dist/CHANGES-%s' % (version,)
    ctx.shell.cp(from_, to_)
