#!/bin/bash
set -ex

base="$(dirname -- "${0}")"
base="$(dirname -- "$(cd "${base:-.}" && pwd)")"
cd "${base}"

rm -f -- "${base}"/bench/.out.*
rm -f -- "${base}"/*.so
