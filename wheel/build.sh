#!/bin/bash
set -ex

libc="${1}"
shift

pkg="${1}"
shift

versions=" ${1} "
shift

final="/io/dist"
target="/io/dist/${libc}"
owner="$( stat -c%u:%g /io )"

mkdir -p -- "${final}"
chown -R "${owner}" "${final}"

mkdir -p -- "${target}"
chown -R "${owner}" "${target}"

# Extract name-only from package spec
name="$(
    basename "${pkg}" \
    | sed -e 's,^\([a-zA-Z][a-zA-Z0-9]*\([._-][a-zA-Z][a-zA-Z0-9]*\)*\).*,\1,' \
    | grep -x '\([a-zA-Z][a-zA-Z0-9]*\([._-][a-zA-Z][a-zA-Z0-9]*\)*\)'
)"

# fail if it doesn't build
export SETUP_CEXT_REQUIRED=1

# pip args
args=( wheel --no-binary "${name}" --no-deps "${pkg}" -w "${target}" )

found=
for dir in /opt/python/*; do
    if [ "${dir/pypy}" != "${dir}" ]; then
        continue
    fi

    pyv="$(
        "${dir}/bin/python" -c 'import sys; sys.stdout.write("".join(map(str, sys.version_info[:2])))'
    )"
    if [ "${versions/${pyv}}" = "${versions}" ]; then
        continue
    fi

    "${dir}/bin/pip" "${args[@]}"
    chown -R -- "${owner}" "${target}"
    found=1
done

[ -n "${found}" ]

# Bundle external shared libraries into the wheels
for whl in "${target}"/*.whl; do
    base="$(basename -- "${whl}")"
    if [ "${base/${libc}}" = "${base}" ]; then
        auditwheel repair "${whl}" -w "${target}"
        chown -R -- "${owner}" "${target}"
    fi
done

# Only keep properly tagged wheels
for whl in "${target}"/*.whl; do
    base="$(basename -- "${whl}")"
    if [ "${base/-${libc}}" != "${base}" -a "${base/pypy}" = "${base}" ]; then
        mv -v -- "${whl}" "${final}"
    fi
done
rm -rf -- "${target}"
chown -R -- "${owner}" "${final}"

# The end.
