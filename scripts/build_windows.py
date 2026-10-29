from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


RUNTIME_PATTERNS = ("vcruntime140*.dll", "msvcp140*.dll")


def find_runtime_dlls(search_directories: Iterable[Path]) -> tuple[Path, ...]:
    found: dict[str, Path] = {}
    for directory in search_directories:
        if not directory.is_dir():
            continue
        for pattern in RUNTIME_PATTERNS:
            for path in directory.glob(pattern):
                found.setdefault(path.name.casefold(), path)

    if "vcruntime140.dll" not in found:
        raise RuntimeError("Could not find vcruntime140.dll; install the Visual C++ runtime used by this Python build.")
    return tuple(found[name] for name in sorted(found))


def runtime_search_directories() -> tuple[Path, ...]:
    python_root = Path(sys.base_prefix)
    python_directory = Path(sys.executable).resolve().parent
    windows_directory = Path(os.environ.get("WINDIR", r"C:\Windows"))
    return (
        python_root,
        python_root / "DLLs",
        python_root / "Library" / "bin",
        python_directory,
        python_directory / "DLLs",
        windows_directory / "System32",
    )


def build() -> None:
    runtime_dlls = find_runtime_dlls(runtime_search_directories())
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "SKM-Importer",
        "--collect-all",
        "openpyxl",
        "--collect-all",
        "xlrd",
    ]
    for runtime_dll in runtime_dlls:
        command.extend(("--add-binary", f"{runtime_dll};."))
    command.append("main.py")
    print("Bundling Visual C++ runtime DLLs:")
    for runtime_dll in runtime_dlls:
        print(f"  {runtime_dll}")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    build()