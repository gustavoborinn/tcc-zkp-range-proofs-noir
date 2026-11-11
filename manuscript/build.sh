#!/bin/sh
set -eu
cd "$(dirname "$0")"
compiler="${TCC_TECTONIC:-/home/brn/.local/share/tcc-latex/tectonic}"
mkdir -p build
"$compiler" --keep-logs --keep-intermediates --outdir build main.tex
