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
from source, the application loads its images and audio from these directories.
Close the CatCompanion window to exit.

## Build a standalone .exe

CatCompanion can be packaged into a standalone Windows application using
[PyInstaller](https://pyinstaller.org/) and the included `CatCompanion.spec`
file, which bundles the `textures` and `sounds` directories, sets the app
icon, and runs the app windowed (no console).

Open a CMD in the project directory, then install the dev dependencies
(which include PyInstaller):

```cmd
uv sync --group dev
```

Build the executable:

```cmd
uv run pyinstaller --clean --noconfirm CatCompanion.spec
```

This produces a `dist\CatCompanion\` folder containing `CatCompanion.exe`
and an `_internal\` folder with its dependencies (Python runtime, Qt/PySide6
binaries, etc.). Run `CatCompanion.exe` from inside that folder, and
distribute/copy the whole `dist\CatCompanion\` folder together — the
`.exe` will not run without its `_internal\` folder alongside it.

PyInstaller also creates a `build\` folder as a scratch workspace while
compiling, it's safe to delete and is not needed to run the app. The
`CatCompanion.exe` inside `build\CatCompanion\` is not runnable on its
own (it's an intermediate artifact). Always run the one inside `dist\`.


