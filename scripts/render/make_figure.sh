#!/bin/sh
# Make the website figure in outputs/render/ (PNG, WebP and PDF).
# Needs Python with the packages in the README, ParaView's pvpython and LaTeX.
# Set PVPYTHON if pvpython is not on your PATH, e.g.
#   PVPYTHON=/Applications/ParaView-6.1.0.app/Contents/bin/pvpython sh scripts/render/make_figure.sh
set -e
cd "$(dirname "$0")/../.."
PV=${PVPYTHON:-pvpython}
R=scripts/render
O=outputs/render
mkdir -p $O
# Usage: sh scripts/render/make_figure.sh <rotor-only case> <four-wing case>
# Both cases must be run and reconstructed (see the README).
$PV $R/render_wake.py "$1" $O/rotor-only-raw.png
$PV $R/render_wake.py "$2" $O/four-wing-raw.png
python $R/compose_wake.py $O/rotor-only-raw.png $O/four-wing-raw.png $O/regenerative-wakes
