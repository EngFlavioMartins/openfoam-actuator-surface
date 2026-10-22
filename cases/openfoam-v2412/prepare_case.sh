#!/bin/bash
# Build an OpenFOAM v2412 (openfoam.com) copy of the Solver/ case.
#
# Usage: prepare_case.sh <ActuatorsSetup file> <topoSetDict file> <destination>
#
# The original Solver/ case targets the OpenFOAM Foundation releases (v9/v10).
# This copy changes only what v2412 needs:
#   - constant/momentumTransport  -> constant/turbulenceProperties
#   - constant/fvOptions          -> v2412 vectorCodedSource syntax; the actuator
#     cells are read from the Rotor and Blade cellZones written by topoSet, and the
#     force vectors are copied from the ActuatorsSetup file.
# Mesh, initial fields, schemes, solver settings and the source distribution are unchanged.
set -euo pipefail

setup=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
topo=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
dest=$3
repo=$(cd "$(dirname "$0")/../.." && pwd)

if [ -e "$dest" ]; then echo "destination exists: $dest" >&2; exit 1; fi
mkdir -p "$dest"
cp -r "$repo/Solver/0.backup" "$dest/0"
cp -r "$repo/Solver/system" "$dest/system"
mkdir -p "$dest/constant"
cp -r "$repo/Solver/constant/polyMesh.backup" "$dest/constant/polyMesh"
cp "$repo/Solver/constant/transportProperties" "$dest/constant/"
cp "$topo" "$dest/system/topoSetDict"
cp "$setup" "$dest/ActuatorsSetup"
rm -f "$dest/system/meshDict"

rotor=$(sed -n 's/.*RotorForce *= *vector(\([^)]*\)).*/\1/p' "$setup")
blade=$(sed -n 's/.*BladeForce *= *vector(\([^)]*\)).*/\1/p' "$setup")

cat > "$dest/constant/turbulenceProperties" <<'DICT'
FoamFile { version 2.0; format ascii; class dictionary; location "constant"; object turbulenceProperties; }

simulationType RAS;

RAS
{
    RASModel        kOmegaSST;
    turbulence      on;
    printCoeffs     on;
}
DICT

cat > "$dest/constant/fvOptions" <<DICT
FoamFile { version 2.0; format ascii; class dictionary; location "constant"; object fvOptions; }

// Port of Solver/constant/fvOptions (Flavio Martins, 2023) to OpenFOAM v2412.
sourceForce
{
    type            vectorCodedSource;
    selectionMode   all;
    fields          (U);
    name            sourceForce;

    codeInclude
    #{
        #include "cellZone.H"
    #};

    codeCorrect   #{ #};
    codeConstrain #{ #};

    codeAddSup
    #{
        const vector RotorForce = vector(${rotor});   // N
        const vector BladeForce = vector(${blade});   // N

        const scalarField& cellsV = mesh().V();
        const labelList& BladeCells = mesh().cellZones()[mesh().cellZones().findZoneID("Blade")];
        const labelList& RotorCells = mesh().cellZones()[mesh().cellZones().findZoneID("Rotor")];

        scalar BladeVolume = 0.0;
        forAll(BladeCells, i) { BladeVolume += cellsV[BladeCells[i]]; }
        const scalar BladeVolume_ProcVolFrac = BladeVolume/max(returnReduce(BladeVolume, sumOp<scalar>()), VSMALL);

        scalar RotorVolume = 0.0;
        forAll(RotorCells, i) { RotorVolume += cellsV[RotorCells[i]]; }
        const scalar RotorVolume_ProcVolFrac = RotorVolume/max(returnReduce(RotorVolume, sumOp<scalar>()), VSMALL);

        vectorField& Usource = eqn.source();

        forAll(BladeCells, i)
        {
            Usource[BladeCells[i]] -= (cellsV[BladeCells[i]]/BladeVolume)*BladeForce*BladeVolume_ProcVolFrac;
        }
        forAll(RotorCells, i)
        {
            Usource[RotorCells[i]] -= (cellsV[RotorCells[i]]/RotorVolume)*RotorForce*RotorVolume_ProcVolFrac;
        }

        const vector totalUSource = returnReduce(sum(Usource), sumOp<vector>());
        Info<< "Actuator surface: rotor " << RotorForce << " N, blades " << BladeForce
            << " N, momentum source " << totalUSource << " N" << endl;
    #};
}
DICT
echo "Prepared $dest (RotorForce ($rotor), BladeForce ($blade))"
