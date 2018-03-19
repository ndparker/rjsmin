#!/bin/bash
set -e

export PYTHONPATH=$PWD
cleanup() {
    rm -f -- "$out"
}
out="$(mktemp)"
trap cleanup EXIT

for v in 3.7 3.6 3.5 3.4 2.7; do
(
    set -e

    p=python$v
    $p make.py makefile || continue
    CFLAGS=-O3 make clean compile
    $p -OO bench/main.py -p >( cat - >>"$out" ) bench/*.js
)
done
python make.py makefile

[ "$1" = "-w" ] && \
    python -mbench.write \
    -p docs/BENCHMARKS \
    -t docs/_userdoc/benchmark.txt \
    <"$out" \
    || true
