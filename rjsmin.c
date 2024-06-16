/*
 * Copyright 2011 - 2024
 * Andr\xe9 Malo or his licensors, as applicable
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "cext.h"
EXT_INIT_FUNC;

#define RJSMIN_DULL_BIT           (1 <<  0)
#define RJSMIN_PRE_REGEX_BIT      (1 <<  1)
#define RJSMIN_REGEX_DULL_BIT     (1 <<  2)
#define RJSMIN_REGEX_CC_DULL_BIT  (1 <<  3)
#define RJSMIN_ID_LIT_BIT         (1 <<  4)
#define RJSMIN_ID_LIT_O_BIT       (1 <<  5)
#define RJSMIN_ID_LIT_C_BIT       (1 <<  6)
#define RJSMIN_STRING_DULL_BIT    (1 <<  7)
#define RJSMIN_SPACE_BIT          (1 <<  8)
#define RJSMIN_POST_REGEX_OFF_BIT (1 <<  9)
#define RJSMIN_A_Z_BIT            (1 << 10)

typedef unsigned char rchar;
#ifdef U
#undef U
#endif
#define U(c) ((rchar)(c))

#define RJSMIN_IS_DULL(c) ((U(c) > 127) || \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_DULL_BIT))

#define RJSMIN_IS_REGEX_DULL(c) ((U(c) > 127) || \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_REGEX_DULL_BIT))

#define RJSMIN_IS_REGEX_CC_DULL(c) ((U(c) > 127) || \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_REGEX_CC_DULL_BIT))

#define RJSMIN_IS_STRING_DULL(c) ((U(c) > 127) || \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_STRING_DULL_BIT))

#define RJSMIN_IS_ID_LITERAL(c) ((U(c) > 127) || \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_ID_LIT_BIT))

#define RJSMIN_IS_ID_LITERAL_OPEN(c) ((U(c) > 127) || \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_ID_LIT_O_BIT))

#define RJSMIN_IS_ID_LITERAL_CLOSE(c) ((U(c) > 127) || \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_ID_LIT_C_BIT))

#define RJSMIN_IS_POST_REGEX_OFF(c) ((U(c) > 127) || \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_POST_REGEX_OFF_BIT))

#define RJSMIN_IS_SPACE(c) ((U(c) <= 127) && \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_SPACE_BIT))

#define RJSMIN_IS_PRE_REGEX_1(c) ((U(c) <= 127) && \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_PRE_REGEX_BIT))

#define RJSMIN_IS_A_Z(c) ((U(c) <= 127) && \
    (rjsmin_charmask[U(c) & 0x7F] & RJSMIN_A_Z_BIT))


static const unsigned short rjsmin_charmask[128] = {
     396,  396,  396,  396,  396,  396,  396,  396,
     396,  396,    2,  396,  396,    2,  396,  396,
     396,  396,  396,  396,  396,  396,  396,  396,
     396,  396,  396,  396,  396,  396,  396,  396,
     396,  687,  588,  653,  765,  653,  143,  588,
     687,  205,  655,  239,  143,  239,  141,  648,
     765,  765,  765,  765,  765,  765,  765,  765,
     765,  765,  143,  143,  653,  143,  653,  143,
     653,  765,  765,  765,  765,  765,  765,  765,
     765,  765,  765,  765,  765,  765,  765,  765,
     765,  765,  765,  765,  765,  765,  765,  765,
     765,  765,  765,  683,  513,  197,  653,  765,
     588, 1789, 1789, 1789, 1789, 1789, 1789, 1789,
    1789, 1789, 1789, 1789, 1789, 1789, 1789, 1789,
    1789, 1789, 1789, 1789, 1789, 1789, 1789, 1789,
    1789, 1789, 1789,  687,  143,  207,  653,  765
};


static Py_ssize_t
rjsmin(const rchar *source, rchar *target, Py_ssize_t length,
       int keep_bang_comments)
{
    const rchar
        *sentinel = source + length, /* never hit this pointer (source buf) */
        *reset,          /* reset pointer (source buf) */
        *pcreset = NULL, /* pre-comment reset pointer (source buf) */
        *pctoken = NULL, /* pre-comment token pointer (target buf)
                          * Pointing to before the last kept comment, if any */
        *rsreset = NULL, /* regex-with-method reset pointer (source buf) */
        *xtarget;        /* pre-regex-2 target pointer */

    rchar *tstart = target, /* Target start pointer for reference */
        *rtreset = NULL;    /* regex-with-method reset pointer (target buf) */

    int rsdot,              /* seen dot after regex-with-method pattern? */
        post_regex = 0;
    rchar c, quote,
        spaced = U(' ');    /* the last seen kind of space (nl taking prio),
                             * init with ' ' */

    /* main loop */
    while (source < sentinel) {
        c = *source++;

        if (RJSMIN_IS_DULL(c)) {
            if (post_regex) post_regex = 0;
            if (pctoken) pctoken = NULL;
            if (spaced == U('\n')) spaced = U(' ');
            if (rsreset) {
                /* both a-z and . are covered by "dull" */
                if (!rsdot) {
                    if (c != U('.')) {
                        /* reset regex-with-method to the starting slash */
                        source = rsreset;
                        target = rtreset;
                        rsreset = NULL;
                        continue; /* main loop */
                    }
                    /* Found a dot after possible regex, looking for a-z now */
                    rsdot = 1;
                }
                else if (!RJSMIN_IS_A_Z(c)) {
                    /* reset regex-with-method to the starting slash */
                    source = rsreset;
                    target = rtreset;
                    rsreset = NULL;
                    continue; /* main loop */
                }
                else {
                    /* Successfull finish the regex-with-method match */
                    rsreset = NULL;
                }
            }

            *target++ = c;
            continue; /* main loop */
        }

        switch (c) {

        /* String */
        case U('\''): case U('"'): case U('`'):
            if (post_regex) post_regex = 0;
            if (pctoken) pctoken = NULL;
            if (spaced == U('\n')) spaced = U(' ');
            if (rsreset) {
                /* reset regex-with-method to the starting slash */
                source = rsreset;
                target = rtreset;
                rsreset = NULL;
                continue; /* main loop */
            }

            reset = source;
            *target++ = quote = c;

            /* string loop */
            while (source < sentinel) {
                c = *source++;
                *target++ = c;
                if (RJSMIN_IS_STRING_DULL(c))
                    continue; /* string loop */

                switch (c) {
                case U('\''): case U('"'): case U('`'):
                    if (c == quote)
                        goto cont; /* main loop */
                    continue; /* string loop */
                case U('\\'):
                    if (source < sentinel) {
                        c = *source++;
                        *target++ = c;
                        if (c == U('\r') && source < sentinel
                            && *source == U('\n'))
                            *target++ = *source++;
                    }
                    continue; /* string loop */
                case U('\r'): case U('\n'):
                    if (quote != U('`'))
                        break; /* string reset */
                    continue; /* string loop */
                }
                break; /* string reset */
            }
            /* string reset */
            target -= source - reset;
            source = reset;
            continue; /* main loop */

        /* Comment or Regex or something else entirely */
        case U('/'):
            if (!(source < sentinel)) {
                if (post_regex) post_regex = 0;
                if (pctoken) pctoken = NULL;
                if (spaced == U('\n')) spaced = U(' ');
                if (rsreset) {
                    /* reset regex-with-method to the starting slash */
                    source = rsreset;
                    target = rtreset;
                    rsreset = NULL;
                    continue; /* main loop */
                }

                *target++ = c;
            }
            else {
                switch (*source) {
            /* Comment */
                case U('*'): case U('/'):
                    goto skip_or_copy_ws;

            /* Regex or slash */
                default:
                    if (rsreset) {
                        /* reset regex-with-method to the starting slash */
                        if (post_regex) post_regex = 0;
                        if (pctoken) pctoken = NULL;
                        if (spaced == U('\n')) spaced = U(' ');
                        source = rsreset;
                        target = rtreset;
                        rsreset = NULL;
                        continue; /* main loop */
                    }

                    xtarget = NULL;
                    if (   target == tstart
                        || RJSMIN_IS_PRE_REGEX_1(*((pctoken ? pctoken : target)
                                                   - 1))
                        || (
                            (xtarget = pctoken ? pctoken : target)
                            && (xtarget - tstart >= 6)
                            && *(xtarget - 1) == U('n')
                            && *(xtarget - 2) == U('r')
                            && *(xtarget - 3) == U('u')
                            && *(xtarget - 4) == U('t')
                            && *(xtarget - 5) == U('e')
                            && *(xtarget - 6) == U('r')
                            && (
                                   xtarget - tstart == 6
                                || !RJSMIN_IS_ID_LITERAL(*(xtarget - 7))
                            )
                        )) {
                        /* nothing to do here, continuing down below
                         * We could unset rsreset here, but we know it already
                         * is. */
                        ;
                    }
                    else if (*((pctoken ? pctoken : target) - 1) == U(')')) {
                        xtarget = NULL;
                        rsreset = source;
                        rtreset = target + 1;
                        rsdot = 0;
                    }
                    else {
                        /* Just a slash */
                        if (post_regex) post_regex = 0;
                        if (pctoken) pctoken = NULL;
                        if (spaced == U('\n')) spaced = U(' ');

                        *target++ = c;
                        continue; /* main loop */
                    }

                    if (post_regex) post_regex = 0;
                    if (pctoken) pctoken = NULL;

                    reset = source;
                    if (spaced == U('\n')) {
                        spaced = U(' ');
                        if (xtarget)
                            *target++ = U('\n');
                    }

                    *target++ = U('/');

                    /* regex loop */
                    while (source < sentinel) {
                        c = *source++;
                        *target++ = c;

                        if (RJSMIN_IS_REGEX_DULL(c))
                            continue; /* regex loop */

                        switch (c) {
                        case U('/'):
                            while (source < sentinel
                                   && RJSMIN_IS_A_Z(*source))
                                *target++ = *source++;
                            post_regex = !rsreset;
                            /* This check is supposed to make it faster.
                             * It doesn't. It slows it down. I wonder why...
                             */
                            /*
                             * if (!post_regex
                             *     && source < sentinel - 1
                             *     && *source == U('.')
                             *     && RJSMIN_IS_A_Z(*(source + 1)))
                             *     rsreset = NULL;
                             */

                            goto cont; /* main loop */

                        case U('\\'):
                            if (source < sentinel) {
                                c = *source++;
                                *target++ = c;
                                if (c == U('\r') || c == U('\n'))
                                    break; /* regex reset */
                            }
                            continue; /* regex loop */

                        case U('['):
                            /* regex CC loop */
                            while (source < sentinel) {
                                c = *source++;
                                *target++ = c;

                                if (RJSMIN_IS_REGEX_CC_DULL(c))
                                    continue; /* regex CC loop */

                                switch (c) {
                                case U('\\'):
                                    if (source < sentinel) {
                                        c = *source++;
                                        *target++ = c;
                                        if (c == U('\r') || c == U('\n'))
                                            break; /* regex reset */
                                    }
                                    continue; /* regex CC loop */

                                case U(']'):
                                    goto cont_regex; /* regex loop */
                                }
                            }
                            break; /* regex reset */

                        }
                        break; /* regex reset */

                    cont_regex:
                        continue; /* regex loop */
                    }

                    /* regex reset */
                    target -= source - reset;
                    source = reset;
                    rsreset = NULL;
                    continue; /* main loop */
                }
            }
            continue;  /* main loop */ /* LCOV_EXCL_LINE */

        /* Whitespace */
        default:
        skip_or_copy_ws:
            /* remember if we've seen a newline, start with: no */
            quote = U(' ');
            --source;

            /* space loop */
            while (source < sentinel) {
                c = *source++;
                if (RJSMIN_IS_SPACE(c))
                    continue; /* space loop */

                switch (c) {
                case U('\r'): case U('\n'):
                    quote = U('\n');
                    continue; /* space loop */

                /* Can only be a comment at this point
                 * (or ending prematurely) */
                case U('/'):
                    if (source < sentinel) {
                        switch (*source) {

                        /* multiline comment */
                        case U('*'):
                            reset = source++;
                            /* copy bang comment, if requested */
                            if (   keep_bang_comments && source < sentinel
                                && *source == U('!')) {
                                if (!pctoken) {
                                    /* Backtracking if ending prematurely */
                                    pctoken = target;
                                    pcreset = reset;
                                }

                                *target++ = U('/');
                                *target++ = U('*');
                                *target++ = *source++;

                                /* comment loop */
                                while (source < sentinel) {
                                    c = *source++;
                                    *target++ = c;
                                    if (c == U('*') && source < sentinel
                                        && *source == U('/')) {
                                        *target++ = *source++;
                                        reset = NULL;
                                        break; /* continue space loop */
                                    }
                                }
                                if (!reset)
                                    continue; /* space loop */

                                /* comment reset */
                                target -= source - reset;
                                source = reset;
                                if (pcreset == reset) {
                                    pctoken = NULL;
                                    pcreset = NULL;
                                }
                            }

                            /* strip regular comment */
                            else {
                                while (source < sentinel) {
                                    c = *source++;
                                    if (c == U('*') && source < sentinel
                                        && *source == U('/')) {
                                        ++source;
                                        reset = NULL;
                                        break; /* continue space loop */
                                    }
                                }
                                if (!reset)
                                    continue; /* space loop */

                                /* comment reset: fallback to slash */
                                source = reset;
                                *target++ = U('/');
                            }
                            goto cont; /* main loop */

                        /* single line comment */
                        case U('/'):
                            ++source;

                            /* single line comment loop */
                            while (source < sentinel) {
                                c = *source++;
                                switch (c) {
                                case U('\n'):
                                    break; /* continue space loop */

                                case U('\r'):
                                    if (source < sentinel
                                        && *source == U('\n'))
                                        ++source;
                                    break; /* continue space loop */

                                default:
                                    continue; /* single line comment loop */
                                }
                                break; /* continue space loop */
                            }
                            quote = U('\n');
                            continue; /* space loop */
                        }
                    }
                }

                /* No more spacy character found */
                --source;
                break; /* end space loop */
            }

            /* Copy a space if needed */
            if ((tstart < (pctoken ? pctoken : target) && source < sentinel)
                && ((quote == U('\n')
                     && ((RJSMIN_IS_ID_LITERAL_CLOSE(*((pctoken ?
                                                        pctoken : target) - 1))
                          && RJSMIN_IS_ID_LITERAL_OPEN(*source))
                         || (post_regex
                             && RJSMIN_IS_POST_REGEX_OFF(*source)
                             && !(post_regex = 0))))
                    ||
                    (quote == U(' ') && !pctoken
                     && ((RJSMIN_IS_ID_LITERAL(*(target - 1))
                          && RJSMIN_IS_ID_LITERAL(*source))
                         || (source < sentinel
                             && ((*(target - 1) == U('+')
                                  && *source == U('+'))
                                 || (*(target - 1) == U('-')
                                     && *source == U('-')))))))) {
                *target++ = quote;
            }

            pcreset = NULL;
            spaced = quote;
        }

    cont:
        continue; /* main loop */
    }
    return (Py_ssize_t)(target - tstart);
}


PyDoc_STRVAR(rjsmin_jsmin__doc__,
"jsmin(script, keep_bang_comments=False)\n\
\n\
Minify javascript based on `jsmin.c by Douglas Crockford`_\\.\n\
\n\
Instead of parsing the stream char by char, it uses a regular\n\
expression approach which minifies the whole script with one big\n\
substitution regex.\n\
\n\
.. _jsmin.c by Douglas Crockford:\n\
   http://www.crockford.com/javascript/jsmin.c\n\
\n\
:Note: This is a hand crafted C implementation built on the regex\n\
       semantics.\n\
\n\
Parameters:\n\
  script (str):\n\
    Script to minify\n\
\n\
  keep_bang_comments (bool):\n\
    Keep comments starting with an exclamation mark? (``/*!...*/``)\n\
\n\
Returns:\n\
  str: Minified script");

static PyObject *
rjsmin_jsmin(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *script, *keep_bang_comments_ = NULL, *result;
    static char *kwlist[] = {"script", "keep_bang_comments", NULL};
    Py_ssize_t slength, length;
    int keep_bang_comments;
#ifdef EXT2
    int uni;
#endif
#ifdef EXT3
    int bytes;
    rchar *bytescript;
#endif

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist,
                                     &script, &keep_bang_comments_))
        LCOV_EXCL_LINE_RETURN(NULL);

    if (!keep_bang_comments_)
        keep_bang_comments = 0;
    else {
        keep_bang_comments = PyObject_IsTrue(keep_bang_comments_);
        if (keep_bang_comments == -1)
            return NULL;
    }

#ifdef EXT2
    if (PyUnicode_Check(script)) {
        if (!(script = PyUnicode_AsUTF8String(script)))
            LCOV_EXCL_LINE_RETURN(NULL);
        uni = 1;
    }
    else if (!PyString_Check(script)) {
        PyErr_SetString(PyExc_TypeError, "Unexpected type");
        return NULL;
    }
    else {
        if (!(script = PyObject_Str(script)))
            LCOV_EXCL_LINE_RETURN(NULL);
        uni = 0;
    }
    slength = PyString_GET_SIZE(script);

    if (!(result = PyString_FromStringAndSize(NULL, slength))) {
        LCOV_EXCL_START

        Py_DECREF(script);
        return NULL;

        LCOV_EXCL_STOP
    }
    Py_BEGIN_ALLOW_THREADS
    length = rjsmin((rchar *)PyString_AS_STRING(script),
                    (rchar *)PyString_AS_STRING(result),
                    slength, keep_bang_comments);
    Py_END_ALLOW_THREADS

    Py_DECREF(script);
    if (length < 0) {
        LCOV_EXCL_START

        Py_DECREF(result);
        return NULL;

        LCOV_EXCL_STOP
    }
    if (length != slength && _PyString_Resize(&result, length) == -1)
        LCOV_EXCL_LINE_RETURN(NULL);

    if (uni) {
        script = PyUnicode_DecodeUTF8(PyString_AS_STRING(result),
                                      PyString_GET_SIZE(result), "strict");
        Py_DECREF(result);
        return script;
    }

    return result;

#else  /* EXT3 */

    if (PyUnicode_Check(script)) {
        bytes = 0;
        script = PyUnicode_AsUTF8String(script);
        bytescript = (rchar *)PyBytes_AS_STRING(script);
        slength = PyBytes_GET_SIZE(script);
    }
    else if (PyBytes_Check(script)) {
        bytes = 1;
        Py_INCREF(script);
        bytescript = (rchar *)PyBytes_AS_STRING(script);
        slength = PyBytes_GET_SIZE(script);
    }
    else if (PyByteArray_Check(script)) {
        bytes = 2;
        Py_INCREF(script);
        bytescript = (rchar *)PyByteArray_AS_STRING(script);
        slength = PyByteArray_GET_SIZE(script);
    }
    else {
        PyErr_SetString(PyExc_TypeError, "Unexpected type");
        return NULL;
    }

    if (!(result = PyBytes_FromStringAndSize(NULL, slength))) {
        LCOV_EXCL_START

        Py_DECREF(script);
        return NULL;

        LCOV_EXCL_STOP
    }
    Py_BEGIN_ALLOW_THREADS
    length = rjsmin(bytescript, (rchar *)PyBytes_AS_STRING(result),
                    slength, keep_bang_comments);
    Py_END_ALLOW_THREADS

    Py_DECREF(script);
    if (length < 0) {
        LCOV_EXCL_START

        Py_DECREF(result);
        return NULL;

        LCOV_EXCL_STOP
    }

    if (!bytes) {
        script = PyUnicode_DecodeUTF8(PyBytes_AS_STRING(result), length,
                                      "strict");
        Py_DECREF(result);
        return script;
    }
    if (bytes == 1) {
        if (length != slength) {
            _PyBytes_Resize(&result, length);
        }
        return result;
    }
    /* bytes == 2: bytearray */
    script = PyByteArray_FromStringAndSize(PyBytes_AS_STRING(result), length);
    Py_DECREF(result);
    return script;
#endif
}

/* ------------------------ BEGIN MODULE DEFINITION ------------------------ */

EXT_METHODS = {
    {"jsmin",
        EXT_CFUNC(rjsmin_jsmin), METH_VARARGS | METH_KEYWORDS,
        rjsmin_jsmin__doc__},

    {NULL}  /* Sentinel */
};

PyDoc_STRVAR(EXT_DOCS_VAR,
"C implementation of rjsmin\n\
==========================\n\
\n\
C implementation of rjsmin.");


EXT_DEFINE(EXT_MODULE_NAME, EXT_METHODS_VAR, EXT_DOCS_VAR);

EXT_INIT_FUNC {
    PyObject *m;

    /* Create the module and populate stuff */
    if (!(m = EXT_CREATE(&EXT_DEFINE_VAR)))
        EXT_INIT_ERROR(LCOV_EXCL_LINE(NULL));

    EXT_ADD_UNICODE(m, "__author__", "Andr\xe9 Malo", "latin-1");
    EXT_ADD_STRING(m, "__version__", STRINGIFY(EXT_VERSION));

    EXT_INIT_RETURN(m);
}

/* ------------------------- END MODULE DEFINITION ------------------------- */
