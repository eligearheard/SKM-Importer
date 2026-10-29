from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse


LATEST_RELEASE_URL = "https://api.github.com/repos/eligearheard/SKM-Importer/releases/latest"
APP_ASSET_NAME = "SKM-Importer.exe"


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    download_url: str
    sha256: str | None


def _version_key(version: str) -> tuple[int, ...]:
    match = re.fullmatch(r"v?(\d+(?:\.\d+)*)(?:[-+][0-9A-Za-z.-]+)?", version)
    if not match:
        raise ValueError(f"Invalid application version: {version}")
    parts = tuple(int(part) for part in match.group(1).split("."))
    if len(parts) < 3:
        raise ValueError(f"Invalid application version: {version}")
    while len(parts) > 3 and parts[-1] == 0:
        parts = parts[:-1]
    return parts


def check_for_update(current_version: str) -> UpdateInfo | None:
    request = urllib.request.Request(
        LATEST_RELEASE_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "SKM-Importer"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            release = json.load(response)
    except HTTPError as error:
        if error.code == 404:
            raise RuntimeError(
                "No publicly accessible GitHub release is available for SKM Importer. "
                "Publish a release or make the repository's releases publicly accessible."
            ) from error
        raise

    tag = release.get("tag_name", "")
    latest_key = _version_key(tag)
    if latest_key <= _version_key(current_version):
        return None

    asset = next(
        (item for item in release.get("assets", []) if item.get("name") == APP_ASSET_NAME),
        None,
    )
    if asset is None or not asset.get("browser_download_url"):
        raise RuntimeError("The latest release does not include the SKM-Importer.exe update.")
    download_url = asset["browser_download_url"]
    parsed_url = urlparse(download_url)
    if parsed_url.scheme != "https" or parsed_url.hostname != "github.com":
        raise RuntimeError("The latest release includes an unexpected download URL.")

    digest = asset.get("digest")
    sha256 = digest.removeprefix("sha256:") if isinstance(digest, str) and digest.startswith("sha256:") else None
    return UpdateInfo(tag.removeprefix("v"), download_url, sha256)


def download_update(update: UpdateInfo) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="skm-importer-update-"))
    download_path = directory / APP_ASSET_NAME
    request = urllib.request.Request(update.download_url, headers={"User-Agent": "SKM-Importer"})
    digest = hashlib.sha256()

    try:
        with urllib.request.urlopen(request, timeout=60) as response, download_path.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
                digest.update(chunk)
        if update.sha256 and digest.hexdigest().lower() != update.sha256.lower():
            raise RuntimeError("The downloaded update failed its SHA-256 integrity check.")
    except Exception:
        download_path.unlink(missing_ok=True)
        directory.rmdir()
        raise
    return download_path


def install_update(download_path: Path) -> None:
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        raise RuntimeError("Automatic installation is available in the packaged Windows app only.")

    target_path = Path(sys.executable).resolve()
    helper_path = Path(tempfile.gettempdir()) / f"skm-importer-update-{os.getpid()}.ps1"
    helper_path.write_text(
        """param([int]$ProcessId, [string]$TargetPath, [string]$DownloadPath)
$ErrorActionPreference = 'Stop'
Wait-Process -Id $ProcessId -ErrorAction SilentlyContinue
$BackupPath = "$TargetPath.previous"
try {
    Remove-Item -LiteralPath $BackupPath -Force -ErrorAction SilentlyContinue
    Move-Item -LiteralPath $TargetPath -Destination $BackupPath -Force
    Move-Item -LiteralPath $DownloadPath -Destination $TargetPath -Force
    Start-Process -FilePath $TargetPath
    Remove-Item -LiteralPath (Split-Path -Parent $DownloadPath) -Recurse -Force -ErrorAction SilentlyContinue
} catch {
    if (Test-Path -LiteralPath $BackupPath) {
        Move-Item -LiteralPath $BackupPath -Destination $TargetPath -Force
        Start-Process -FilePath $TargetPath
    }
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("SKM Importer could not complete the update: $($_.Exception.Message)", "Update failed") | Out-Null
}
""",
        encoding="utf-8",
    )
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(helper_path),
            "-ProcessId",
            str(os.getpid()),
            "-TargetPath",
            str(target_path),
            "-DownloadPath",
            str(download_path.resolve()),
        ],
        creationflags=creation_flags,
        close_fds=True,
    )