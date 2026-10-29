from __future__ import annotations

import sys
from pathlib import Path


def normalize_release_version(value: str) -> str:
    tag = value.strip()
    if tag.startswith("v"):
        tag = tag[1:]

    separator_positions = [position for separator in "-+" if (position := tag.find(separator)) >= 0]
    split_at = min(separator_positions) if separator_positions else len(tag)
    core, suffix = tag[:split_at], tag[split_at:]
    components = core.split(".")
    if len(components) < 3 or any(not part.isascii() or not part.isdigit() for part in components):
        raise ValueError("Release version must contain at least three numeric dot-separated components.")
    if suffix and any(not (character.isascii() and (character.isalnum() or character in ".-+")) for character in suffix[1:]):
        raise ValueError("Release version contains an invalid suffix.")
    if suffix and len(suffix) == 1:
        raise ValueError("Release version suffix cannot be empty.")
    return tag


def stamp_version(value: str, version_file: str | Path = "skm_importer/version.py") -> str:
    version = normalize_release_version(value)
    Path(version_file).write_text(f'__version__ = "{version}"\n', encoding="ascii")
    return f"v{version}"


if __name__ == "__main__":
    try:
        print(stamp_version(sys.argv[1]))
    except (IndexError, OSError, ValueError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)