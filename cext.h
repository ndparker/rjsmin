/*
 * Copyright 2006 - 2022
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

/*
 * central naming stuff
 */

#ifndef CEXT_H
#define CEXT_H

#define LCOV_EXCL_LINE(x) (x)
#define LCOV_EXCL_LINE_GOTO(x) goto x
#define LCOV_EXCL_LINE_RETURN(x) return (x)
#define LCOV_EXCL_START
#define LCOV_EXCL_STOP

#ifndef EXT_MODULE
#error EXT_MODULE must be defined outside of this file (-DEXT_MODULE=...)
#endif

/*
 * include core header files
 */
#define PY_SSIZE_T_CLEAN

#include "Python.h"
#include "structmember.h"

/*
 * define our helper macros depending on the stuff above
 */
#define STRINGIFY(n) STRINGIFY_HELPER(n)
#define STRINGIFY_HELPER(n) #n
#define CONCATENATE(first, second) CONCATENATE_HELPER(first, second)
#define CONCATENATE_HELPER(first, second) first##second

#define EXT_MODULE_NAME  STRINGIFY(EXT_MODULE)
#ifdef EXT_PACKAGE
#define EXT_PACKAGE_NAME STRINGIFY(EXT_PACKAGE)
#define EXT_MODULE_PATH  EXT_PACKAGE_NAME "." EXT_MODULE_NAME
#else
#define EXT_PACKAGE_NAME ""
#define EXT_MODULE_PATH  EXT_MODULE_NAME
#endif

#define EXT_DOCS_VAR      CONCATENATE(var, CONCATENATE(EXT_MODULE, __doc__))
#define EXT_METHODS_VAR   CONCATENATE(var, CONCATENATE(EXT_MODULE, _methods))
#define EXT_METHODS       static PyMethodDef EXT_METHODS_VAR[]

#define EXT_DEFINE_VAR    CONCATENATE(var, CONCATENATE(EXT_MODULE, _module))

/* GCC 8 doesn't like the generic (PyCFunction) cast */
#define EXT_CFUNC(func) ((PyCFunction)(void (*) (void))(func))

/*
 * Link helpers
 */
#if defined(__GNUC__) && __GNUC__ >= 4 && !defined(__MINGW32__)
    #define EXT_LOCAL __attribute__((visibility("hidden")))
#else
    #define EXT_LOCAL
#endif


/*
 * Py-version specific support
 */

/* Py3K */
#if PY_MAJOR_VERSION >= 3

#if PY_VERSION_HEX >= 0x03040000
#define TEXT_SIGNATURE
#endif

#define EXT3

#ifndef Py_TPFLAGS_HAVE_CLASS
#define Py_TPFLAGS_HAVE_CLASS (0)
#endif

#ifndef Py_TPFLAGS_HAVE_WEAKREFS
#define Py_TPFLAGS_HAVE_WEAKREFS (0)
#endif

#ifndef Py_TPFLAGS_HAVE_ITER
#define Py_TPFLAGS_HAVE_ITER (0)
#endif

#ifndef Py_TPFLAGS_HAVE_RICHCOMPARE
#define Py_TPFLAGS_HAVE_RICHCOMPARE (0)
#endif

#ifndef Py_TPFLAGS_HAVE_SEQUENCE_IN
#define Py_TPFLAGS_HAVE_SEQUENCE_IN (0)
#endif

#ifndef PyMODINIT_FUNC
#define EXT_INIT_FUNC PyObject *CONCATENATE(PyInit_, EXT_MODULE)(void)
#else
#define EXT_INIT_FUNC PyMODINIT_FUNC CONCATENATE(PyInit_, EXT_MODULE)(void)
#endif

#define EXT_DEFINE(name, methods, doc) \
static struct PyModuleDef EXT_DEFINE_VAR = { \
    PyModuleDef_HEAD_INIT, \
    name,                  \
    doc,                   \
    -1,                    \
    methods,               \
    NULL,                  \
    NULL,                  \
    NULL,                  \
    NULL                   \
}

#define EXT_CREATE(def) (PyModule_Create(def))
#define EXT_INIT_ERROR(module) do {Py_XDECREF(module); return NULL;} while(0)
#define EXT_INIT_RETURN(module) return module

#define EXT_DOC_UNICODE(m)

#else /* end py3k */

#define EXT2

/*
 * Py3 Object defintions
 */
#ifndef PyVarObject_HEAD_INIT
    #define PyVarObject_HEAD_INIT(type, size) \
        PyObject_HEAD_INIT(type) size,
#endif

#ifndef PyMODINIT_FUNC
#define EXT_INIT_FUNC void CONCATENATE(init, EXT_MODULE)(void)
#else
#define EXT_INIT_FUNC PyMODINIT_FUNC CONCATENATE(init, EXT_MODULE)(void)
#endif

#define EXT_DEFINE__STRUCT \
    CONCATENATE(struct, CONCATENATE(EXT_MODULE, _module))

struct EXT_DEFINE__STRUCT {
    char *m_name;
    char *m_doc;
    PyMethodDef *m_methods;
};
#define EXT_DEFINE(name, methods, doc)              \
static struct EXT_DEFINE__STRUCT EXT_DEFINE_VAR = { \
    name,                                           \
    doc,                                            \
    methods                                         \
}

#define EXT_CREATE(def) ((def)->m_doc                               \
    ? Py_InitModule3((def)->m_name, (def)->m_methods, (def)->m_doc) \
    : Py_InitModule((def)->m_name, (def)->m_methods)                \
)
#define EXT_INIT_ERROR(module) return
#define EXT_INIT_RETURN(module) return

#define EXT_DOC_UNICODE(m) do {                                         \
    PyObject *doc__, *uni__;                                            \
    int res__;                                                          \
                                                                        \
    if ((doc__ = PyObject_GetAttrString(m, "__doc__"))) {               \
        uni__ = PyUnicode_FromEncodedObject(doc__, "utf-8", "strict");  \
        Py_DECREF(doc__);                                               \
        if (!uni__)                                                     \
            EXT_INIT_ERROR(m);                                          \
        res__ = PyObject_SetAttrString(m, "__doc__", uni__);            \
        Py_DECREF(uni__);                                               \
        if (res__ == -1)                                                \
            EXT_INIT_ERROR(m);                                          \
    }                                                                   \
    else if (!(PyErr_Occurred()                                         \
               && PyErr_ExceptionMatches(PyExc_AttributeError)))        \
        EXT_INIT_ERROR(m);                                              \
} while(0)

#endif /* end py2K */


/*
 * Fake py 3.3 Unicode APIs
 */
#ifndef PyUnicode_GET_LENGTH

#ifdef EXT_PEP393
#undef EXT_PEP393
#endif

#define EXT_UNI_CP Py_UNICODE
enum PyUnicode_Kind {
/* String contains only wstr byte characters.  This is only possible
   when the string was created with a legacy API and _PyUnicode_Ready()
   has not been called yet.  */
    PyUnicode_WCHAR_KIND = 0,
/* Return values of the PyUnicode_KIND() macro: */
    PyUnicode_1BYTE_KIND = 1,
    PyUnicode_2BYTE_KIND = 2,
    PyUnicode_4BYTE_KIND = 4
};

#define EXT_UNI_KIND_DECL(var)
#define EXT_UNI_KIND_SET(var, value)

#if Py_UNICODE_SIZE == 2
#define PyUnicode_KIND(x) (2)
#elif Py_UNICODE_SIZE == 4
#define PyUnicode_KIND(x) (4)
#else
#error "Cannot recognize sizeof(Py_UNICODE)"
#endif

#define PyUnicode_GET_LENGTH(x) (PyUnicode_GET_SIZE(x))
#define PyUnicode_DATA(x) ((void *)PyUnicode_AS_UNICODE(x))
#define PyUnicode_READ(kind, data, index) \
    ((Py_UNICODE) (((const Py_UNICODE *)(data))[(index)]))
#define PyUnicode_WRITE(kind, data, index, value) \
    do { \
        ((Py_UNICODE *)(data))[(index)] = (Py_UNICODE)(value); \
    } while(0)

#define PyUnicode_FromKindAndData(kind, data, length) \
    (PyUnicode_FromUnicode((Py_UNICODE *)data, length))
#define EXT_UNI_MAX_DECL(var)
#define EXT_UNI_MAX_SET(var, value)
#define EXT_UNI_MAX_LEVEL(var, add)
#define PyUnicode_New(size, maxchar) PyUnicode_FromUnicode(NULL, size)

#else

#ifndef EXT_PEP393
#define EXT_PEP393
#endif

#define EXT_UNI_CP Py_UCS4

#define EXT_UNI_KIND_DECL(var) enum PyUnicode_Kind var;
#define EXT_UNI_KIND_SET(var, value) var = (value);

#define EXT_UNI_MAX_DECL(var) Py_UCS4 var;
#define EXT_UNI_MAX_SET(var, value) (var) = (value);
#define EXT_UNI_MAX_LEVEL(var, add) do { \
    if ((add) > (var)) (var) = (add);  \
} while(0)

#endif

#define U(c) ((EXT_UNI_CP)(c))


/*
 * Module init tools
 */
#define EXT_INIT_TYPE(module, type) do { \
    if (PyType_Ready(type) < 0)          \
        EXT_INIT_ERROR(module);          \
} while (0)

#define EXT_ADD_TYPE(module, name, type) do {                     \
    Py_INCREF(type);                                              \
    if (PyModule_AddObject(module, name, (PyObject *)(type)) < 0) \
        EXT_INIT_ERROR(module);                                   \
} while (0)

#define EXT_ADD_UNICODE(module, name, string, encoding) do { \
    if (PyModule_AddObject(                                  \
            module,                                          \
            name,                                            \
            PyUnicode_Decode(                                \
                string,                                      \
                sizeof(string) - 1,                          \
                encoding,                                    \
                "strict"                                     \
            )) < 0)                                          \
        EXT_INIT_ERROR(module);                              \
} while (0)

#define EXT_ADD_STRING(module, name, string) do {             \
    if (PyModule_AddStringConstant(module, name, string) < 0) \
        EXT_INIT_ERROR(module);                               \
} while (0)

#define EXT_ADD_INT(module, name, number) do {             \
    if (PyModule_AddIntConstant(module, name, number) < 0) \
        EXT_INIT_ERROR(module);                            \
} while (0)


/* PEP 353 support, implemented as of python 2.5 */
#if PY_VERSION_HEX < 0x02050000
typedef int Py_ssize_t;
#define PyInt_FromSsize_t(arg) PyInt_FromLong((long)arg)
#define PyInt_AsSsize_t(arg) (int)PyInt_AsLong(arg)
#define PY_SSIZE_T_MAX ((Py_ssize_t)INT_MAX)
#endif

/*
 * some helper macros (Python 2.4)
 */
#ifndef Py_VISIT
#define Py_VISIT(op) do {            \
    if (op) {                        \
        int vret = visit((op), arg); \
        if (vret) return vret;       \
    }                                \
} while (0)
#endif

#ifdef Py_CLEAR
#undef Py_CLEAR
#endif
#define Py_CLEAR(op) do {                   \
    if (op) {                               \
        PyObject *tmp__ = (PyObject *)(op); \
        (op) = NULL;                        \
        Py_DECREF(tmp__);                   \
    }                                       \
} while (0)

#ifndef Py_RETURN_NONE
#define Py_RETURN_NONE return Py_INCREF(Py_None), Py_None
#endif

#ifndef Py_RETURN_FALSE
#define Py_RETURN_FALSE return Py_INCREF(Py_False), Py_False
#endif

#ifndef Py_RETURN_TRUE
#define Py_RETURN_TRUE return Py_INCREF(Py_True), Py_True
#endif

/* Macros for inline documentation. (Python 2.3) */
#ifndef PyDoc_VAR
#define PyDoc_VAR(name) static char name[]
#endif

#ifndef PyDoc_STRVAR
#define PyDoc_STRVAR(name,str) PyDoc_VAR(name) = PyDoc_STR(str)
#endif

#ifndef PyDoc_STR
#ifdef WITH_DOC_STRINGS
#define PyDoc_STR(str) str
#else
#define PyDoc_STR(str) ""
#endif
#endif

/* Basestring check (basestring introduced in Python 2.3) */
#if PY_VERSION_HEX < 0x02030000
#define BaseString_Check(type) (                  \
       PyObject_TypeCheck((type), &PyString_Type)  \
    || PyObject_TypeCheck((type), &PyUnicode_Type) \
)
#else
#define BaseString_Check(type) PyObject_TypeCheck((type), &PyBaseString_Type)
#endif

#define GENERIC_ALLOC(type) \
    ((void *)((PyTypeObject *)type)->tp_alloc(type, (Py_ssize_t)0))

/* PyPy doesn't define it */
#ifndef PyType_IS_GC
#define PyType_IS_GC(t) PyType_HasFeature((t), Py_TPFLAGS_HAVE_GC)
#endif

#ifndef Py_TYPE
#define Py_TYPE(ob) (((PyObject*)(ob))->ob_type)
#endif

#define DEFINE_GENERIC_DEALLOC(prefix)          \
static void prefix##_dealloc(void *self)        \
{                                               \
    if (PyType_IS_GC(Py_TYPE(self)))            \
        PyObject_GC_UnTrack(self);              \
    (void)prefix##_clear(self);                 \
    (Py_TYPE(self))->tp_free((PyObject *)self); \
}

#endif /* CEXT_H */
