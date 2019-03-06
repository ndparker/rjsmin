#!/bin/bash
set -ex

base="$(dirname -- "${0}")"
base="$(dirname -- "$(cd "${base:-.}" && pwd)")"
cd "${base}"

pyv="$(python -c 'import sys; print("".join(map(str, sys.version_info[:2])))')"

out="${base}/bench/.out.${pyv}"
: >"${out}"


CFLAGS=-O3 pip install -vv -e .
python -OO bench/main.py -p >( cat - >>"$out" ) bench/*.js
