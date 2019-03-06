#!/bin/bash
set -ex

pkg="${1}"
shift

versions=" ${1} "
shift

target="/io/dist"
owner="$( stat -c%u:%g /io )"

mkdir -p -- "${target}"
chown -R "${owner}" "${target}"

name="$(
    basename "${pkg}" \
    | sed -e 's,^\([a-zA-Z][a-zA-Z0-9]*\([._-][a-zA-Z][a-zA-Z0-9]*\)*\).*,\1,' \
    | grep -x '\([a-zA-Z][a-zA-Z0-9]*\([._-][a-zA-Z][a-zA-Z0-9]*\)*\)'
)"

args=( wheel --no-binary "${name}" --no-deps "${pkg}" -w "${target}" )

found=
for dir in /opt/python/*; do
    pyv="$(
        "${dir}/bin/python" -c 'import sys; sys.stdout.write("".join(map(str, sys.version_info[:2])))'
    )"
    if [ "${versions/${pyv}}" = "${versions}" ]; then
        continue
    fi

    "${dir}/bin/pip" "${args[@]}"
    chown -R "${owner}" "${target}"
    found=1
done

[ -n "${found}" ]

# Bundle external shared libraries into the wheels
for whl in "${target}"/*.whl; do
    if [ "${whl/manylinux}" = "${whl}" ]; then
        auditwheel repair "${whl}" -w "${target}"
        chown -R "${owner}" "${target}"
    fi
done

# Only keep manylinux wheels
for whl in "${target}"/*.whl; do
    if [ "${whl/-manylinux}" = "${whl}" ]; then
        rm -vf -- "${whl}"
    fi
done
