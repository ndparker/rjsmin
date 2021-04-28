#!/bin/bash
# Usage: Run this script as below with different python versions
# ./wheel/multiarch_build.sh <package_name> 35 36 37 38
set -ex

pkg="${1}"
shift

versions="${@}"

images="manylinux2010_x86_64 manylinux1_i686 manylinux2014_aarch64"

docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

for image in ${images};do
    for version in $versions;do
        docker run --rm -v "$(pwd)":/io quay.io/pypa/${image} /io/wheel/build.sh ${pkg} ${version}
    done
done
