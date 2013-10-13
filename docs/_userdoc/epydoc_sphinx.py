# -*- coding: ascii -*-
#
# Copyright 2010, 2011
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

import os
import posixpath

from docutils import nodes

from sphinx.util import caption_ref_re


def relpath(path, start=os.path.curdir):
    """Return a relative version of a path - stolen from python2.6 """

    if not path:
        raise ValueError("no path specified")

    start_list = os.path.abspath(start).split(sep)
    path_list = os.path.abspath(path).split(sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([start_list, path_list]))

    rel_list = [os.path.pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return os.path.curdir
    return os.path.join(*rel_list)

try:
    relpath = os.path.relpath
except AttributeError:
    pass


def make_roles(app):
    """ Make roles """
    epydoc = app.config.epydoc
    if epydoc is not None:
        for name, basedir in epydoc.iteritems():
            app.add_role(name, make_epydoc_role(app, basedir))


def make_epydoc_role(app, epydoc):
    """ Make a single role """
    try:
        fp = open(os.path.join(epydoc, 'api-objects.txt'))
        try:
            apis = dict([
                line.strip().split(None, 1) for line in fp if line.strip()
            ])
        finally:
            fp.close()
    except IOError:
        app.warn("Epydoc description at %s not found" % (epydoc,))
        apis = {}

    def epydoc_role(role, rawtext, text, lineno, inliner, options={},
                    content=[]):
        """ Actual role callback """
        match = caption_ref_re.match(text)
        if match:
            extra, (text, ref) = True, match.group(1, 2)
            text = text.strip()
            if text.startswith('|') and text.endswith('|'):
                text = text[1:-1]
                extra = False
        else:
            extra, text, ref = False, None, text
        if ref.endswith('()'):
            ref = ref[:-2].strip()
            parens = text is None
        else:
            parens = False

        if '/' in ref:
            chunks = ref.split('/', 1)
            if not chunks[0]: # Main page
                uri = 'index.html'
            else:
                uri = apis.get(''.join(chunks))
            if text is None:
                text = chunks[1]
        else:
            uri = apis.get(ref)
        if not text:
            text = ref
        if parens:
            text += '()'

        if uri is None:
            node = nodes.literal(rawtext, text)
        else:
            baseuri = relpath(
                epydoc,
                os.path.dirname(inliner.document.current_source)
            ).split(os.path.sep)
            for idx, elem in enumerate(baseuri):
                if elem == os.path.curdir:
                    baseuri[idx] = '.'
                elif elem == os.path.pardir:
                    baseuri[idx] = '..'
            baseuri = '/'.join(baseuri)
            uri = posixpath.join(baseuri, uri)
            if not extra:
                text =u'\u2192\xa0' + text
            node = nodes.reference(rawtext, text, refuri=uri, **options)
            if not extra:
                node = nodes.literal(rawtext, '', node)
        return [node], []

    return epydoc_role


def setup(app):
    app.add_config_value('epydoc', None, 'html')
    app.connect('builder-inited', make_roles)
