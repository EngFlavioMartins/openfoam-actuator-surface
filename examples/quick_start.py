"""Quick start for OpenFOAM actuator surface: write the four-wing actuator-surface case and run it if OpenFOAM is available.

Run from the repository root with:  python run.py
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "runs" / "four-wing"


def main():
    if shutil.which("bash") is None:
        sys.exit("This case is prepared with bash scripts; on Windows, use WSL.")
    if not CASE.exists():
        subprocess.check_call(["bash", "cases/openfoam-v2412/prepare_case.sh", "Resources/Setup-with-blades",
                               "Resources/topoSetDict-FourBlades", str(CASE)], cwd=ROOT)
    print(f"Case written to {CASE.relative_to(ROOT)}")
    if shutil.which("simpleFoam") is None:
        print("OpenFOAM v2412 (openfoam.com) was not found on this computer, so the case was only prepared.")
        print("Install OpenFOAM (https://www.openfoam.com/download), load its environment, then run:")
        print("    bash cases/openfoam-v2412/run_case.sh runs/four-wing")
        return
    print("OpenFOAM found: running the case (this takes about 15 minutes on 5 cores) ...")
    subprocess.check_call(["bash", "cases/openfoam-v2412/run_case.sh", str(CASE), str(min(5, os.cpu_count() or 1))], cwd=ROOT)
    print("Done. Results are in", CASE.relative_to(ROOT))


if __name__ == "__main__":
    main()
