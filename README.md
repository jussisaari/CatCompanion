# CatCompanion

CatCompanion is a small desktop pet that lives on your screen. Built with
Python and PySide6.

## Requirements

- Windows
- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

## Install uv

Assuming Python and pip are already installed, you can install uv with:

```cmd
python -m pip install uv
```

## Run from source

Open a CMD in the project directory (the
directory containing `pyproject.toml`), then sync the project dependencies:

```cmd
uv sync
```

Start CatCompanion:

```cmd
uv run python src\catcompanion\__init__.py
```

Keep the `textures` and `sounds` directories in the project root when running
from source; the application loads its images and audio from these directories.
Close the CatCompanion window to exit.

## Build the Windows executable

Install the development dependencies, including PyInstaller, and build using
the checked-in spec file:

```cmd
uv sync --group dev
uv run --group dev pyinstaller --noconfirm --clean CatCompanion.spec
```

The onedir build is written to `dist\CatCompanion\`. Run
`dist\CatCompanion\CatCompanion.exe`; keep the rest of that directory alongside
the executable.
