# OpenFOAM actuator surface

<p align="center">
  <a href="https://doi.org/10.5194/wes-10-41-2025"><img src="https://img.shields.io/badge/paper-10.5194%2Fwes--10--41--2025-1F6FEB" alt="paper: 10.5194/wes-10-41-2025"></a>
  <a href="https://doi.org/10.5281/zenodo.11615669"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.11615669-0D47A1" alt="DOI: 10.5281/zenodo.11615669"></a>
  <a href="https://www.openfoam.com/"><img src="https://img.shields.io/badge/OpenFOAM-v2412-1C6EB4" alt="OpenFOAM: v2412"></a>
  <a href="https://github.com/EngFlavioMartins/openfoam-actuator-surface/blob/HEAD/LICENSE.txt"><img src="https://img.shields.io/badge/license-Apache%202.0-2E7D32" alt="license: Apache 2.0"></a>
  <a href="https://engflaviomartins.github.io/#regenerative-wakes"><img src="https://img.shields.io/badge/website-research%20page-15212B" alt="website: research page"></a>
</p>

**Rotors and wings as momentum sources in OpenFOAM.**

<p align="center"><img src="docs/assets/render.webp" width="560" alt="Wake of an actuator-surface rotor without wings (top) and with four brushed-metal wing strips (bottom): the wake rises and recovers faster with the wings"></p>

A rotor and lift-producing wing strips are modelled as momentum sources on selected cells, so wakes can be studied without resolving the blades. The original case (`Solver/`) targets the OpenFOAM Foundation releases; `cases/openfoam-v2412/` runs it on OpenFOAM v2412 (openfoam.com).

## Get started

```bash
git clone https://github.com/EngFlavioMartins/openfoam-actuator-surface.git
cd openfoam-actuator-surface
bash cases/openfoam-v2412/prepare_case.sh Resources/Setup-with-blades Resources/topoSetDict-FourBlades runs/four-wing
bash cases/openfoam-v2412/run_case.sh runs/four-wing
```

Run these in an OpenFOAM v2412 environment. Use `Resources/Setup-no-blades` for the rotor alone. Forces are set in `Resources/Setup-*`, the actuator cells in `Resources/topoSetDict-*`. Each run converges in under 300 iterations.

## Make the figure above

```bash
sh scripts/render/make_figure.sh runs/rotor-only runs/four-wing
```

You need [ParaView](https://www.paraview.org/download/) (for `pvpython`), a LaTeX installation, and `pip install pyvista pillow`.

## Cite

This code accompanies the paper below. If you use it, please cite (code record: [Zenodo, 10.5281/zenodo.11615669](https://doi.org/10.5281/zenodo.11615669)):

```bibtex
@article{martins2025multirotor,
  author  = {Martins, Flavio A. C. and van Zuijlen, A. and Ferreira, C. S.},
  title   = {Proof of Concept for Multirotor Systems with Vortex-Generating Modes for Regenerative Wind Energy: A Study Based on Numerical Simulations and Experimental Data},
  journal = {Wind Energy Science},
  volume  = {10},
  pages   = {41--58},
  year    = {2025},
  doi     = {10.5194/wes-10-41-2025}
}
```

GitHub's **Cite this repository** button (from [CITATION.cff](CITATION.cff)) gives the same reference in other formats.

## Licence

Apache 2.0; see [LICENSE.txt](LICENSE.txt).
