#!/usr/bin/env python3
"""OpenFOAM actuator surface: run the example with one command.

    python run.py

The first run creates a private environment in .venv and installs the packages this
project needs (a minute or two). Later runs start straight away. If you already run
it inside an environment that has the packages (for example the conda environment
from environment.yml), that environment is used instead. Works on Linux, macOS and
Windows with Python 3.10 or newer. Extra arguments are passed on to the example.
"""
import hashlib
import importlib.util
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NEEDS = []                  # modules the example imports
INSTALL = []              # what pip installs into .venv
DEMO = ["examples/quick_start.py"]                    # the example, run with Python from the repository root


def venv_python():
    return ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def has(modules):
    return all(importlib.util.find_spec(m) is not None for m in modules)


def prepare_venv():
    py = venv_python()
    if not py.exists():
        print("First run: creating a private environment in .venv ...", flush=True)
        venv.create(ROOT / ".venv", with_pip=True)
    spec = "".join((ROOT / f).read_text() for f in ("requirements.txt", "pyproject.toml") if (ROOT / f).exists())
    stamp = ROOT / ".venv" / ".installed"
    digest = hashlib.sha256((spec + repr(INSTALL)).encode()).hexdigest()
    if not stamp.exists() or stamp.read_text() != digest:
        print("Installing the required packages (only needed once) ...", flush=True)
        subprocess.check_call([str(py), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
        subprocess.check_call([str(py), "-m", "pip", "install", "--quiet", *INSTALL], cwd=ROOT)
        stamp.write_text(digest)
    return py


def main():
    if sys.version_info < (3, 10):
        sys.exit(f"This project needs Python 3.10 or newer (you have {sys.version.split()[0]}).")
    py = Path(sys.executable) if (not NEEDS or has(NEEDS)) else prepare_venv()
    sys.exit(subprocess.call([str(py), *DEMO, *sys.argv[1:]], cwd=ROOT))


if __name__ == "__main__":
    main()
