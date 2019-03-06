#!/bin/bash
set -ex

base="$(dirname -- "${0}")"
base="$(dirname -- "$(cd "${base:-.}" && pwd)")"
cd "${base}"

cat bench/.out.* >bench/report.pickle
python -mbench.write \
    -p docs/BENCHMARKS -t docs/_userdoc/benchmark.txt \
    <bench/report.pickle
