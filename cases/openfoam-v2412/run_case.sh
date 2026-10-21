#!/bin/bash
# Run a case prepared by prepare_case.sh: topoSet, decompose, simpleFoam, reconstruct.
# Usage: run_case.sh <case directory> [number of processes, default 5]
set -euo pipefail
cd "$1"
np=${2:-5}
foamDictionary -entry numberOfSubdomains -set "$np" system/decomposeParDict > /dev/null
foamDictionary -entry hierarchicalCoeffs/n -set "($np 1 1)" system/decomposeParDict > /dev/null
topoSet > log.topoSet 2>&1
decomposePar -force > log.decomposePar 2>&1
mpirun -np "$np" simpleFoam -parallel > log.simpleFoam 2>&1
reconstructPar -latestTime > log.reconstructPar 2>&1
echo "finished $1"
