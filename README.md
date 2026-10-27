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

## The standalone .exe

The standalone .exe file to run the application can be found in: `dist\CatCompanion.exe`

## Building a standalone .exe (Optional)

If you want to build your own new standalone .exe file (for example if you've made your own modifications to the code). You can do this by using
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

This produces a single file, `dist\CatCompanion.exe`, with everything
(Python runtime, Qt/PySide6 binaries, `textures`, `sounds`, etc.) bundled
inside it. Just run `dist\CatCompanion.exe` directly.



