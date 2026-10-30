from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse


LATEST_RELEASE_URL = "https://api.github.com/repos/eligearheard/SKM-Importer/releases/latest"
APP_ASSET_NAME = "SKM-Importer.exe"


def _log_update(message: str) -> None:
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    log_path = local_app_data / "SKM Importer" / "update.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if log_path.exists() and log_path.stat().st_size > 1_000_000:
            previous_log = log_path.with_name("update.previous.log")
            previous_log.unlink(missing_ok=True)
            log_path.replace(previous_log)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{datetime.now().astimezone().isoformat()} {message}\n")
    except OSError:
        pass


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
    _log_update(f"Checking for updates; current version={current_version}")
    request = urllib.request.Request(
        LATEST_RELEASE_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "SKM-Importer"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            release = json.load(response)
    except HTTPError as error:
        _log_update(f"Release check failed with HTTP {error.code}: {error.reason}")
        if error.code == 404:
            raise RuntimeError(
                "No publicly accessible GitHub release is available for SKM Importer. "
                "Publish a release or make the repository's releases publicly accessible."
            ) from error
        raise

    tag = release.get("tag_name", "")
    _log_update(f"Latest release tag={tag!r}")
    latest_key = _version_key(tag)
    if latest_key <= _version_key(current_version):
        _log_update("No update available according to version comparison")
        return None

    asset = next(
        (item for item in release.get("assets", []) if item.get("name") == APP_ASSET_NAME),
        None,
    )
    if asset is None or not asset.get("browser_download_url"):
        _log_update(f"Latest release {tag!r} has no {APP_ASSET_NAME} asset")
        raise RuntimeError("The latest release does not include the SKM-Importer.exe update.")
    download_url = asset["browser_download_url"]
    parsed_url = urlparse(download_url)
    if parsed_url.scheme != "https" or parsed_url.hostname != "github.com":
        _log_update(f"Rejected unexpected update asset URL: {download_url!r}")
        raise RuntimeError("The latest release includes an unexpected download URL.")

    digest = asset.get("digest")
    sha256 = digest.removeprefix("sha256:") if isinstance(digest, str) and digest.startswith("sha256:") else None
    update = UpdateInfo(tag.removeprefix("v"), download_url, sha256)
    _log_update(f"Update selected: version={update.version}; url={update.download_url}; sha256={update.sha256}")
    return update


def download_update(update: UpdateInfo) -> Path:
    _log_update(f"Starting download for version={update.version}; url={update.download_url}")
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
        _log_update(
            f"Download complete: path={download_path}; bytes={download_path.stat().st_size}; "
            f"sha256={digest.hexdigest()}"
        )
    except Exception as error:
        _log_update(f"Download failed: {type(error).__name__}: {error}")
        download_path.unlink(missing_ok=True)
        directory.rmdir()
        raise
    return download_path


def install_update(download_path: Path, version: str | None = None) -> None:
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        raise RuntimeError("Automatic installation is available in the packaged Windows app only.")

    target_path = Path(sys.executable).resolve()
    helper_path = Path(tempfile.gettempdir()) / f"skm-importer-update-{os.getpid()}.ps1"
    ready_path = Path(tempfile.gettempdir()) / f"skm-importer-update-ready-{os.getpid()}.txt"
    log_path = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SKM Importer" / "update.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    downloaded_digest = hashlib.sha256(download_path.read_bytes()).hexdigest()
    _log_update(
        f"Starting install: version={version}; running_executable={target_path}; "
        f"download={download_path}; bytes={download_path.stat().st_size}; sha256={downloaded_digest}"
    )

    # 1. Clean PyInstaller environment leaks before calling PowerShell
    clean_env = os.environ.copy()
    for key in list(clean_env.keys()):
        if "_MEI" in key.upper() or key.startswith("PYI_"):
            clean_env.pop(key, None)
    mei_pass = getattr(sys, "_MEIPASS", None)
    if mei_pass:
        paths = clean_env.get("PATH", "").split(os.pathsep)
        clean_env["PATH"] = os.pathsep.join(p for p in paths if p != mei_pass)

    # 2. PowerShell helper with sanitized execution and brief wait to allow file unlock
    helper_path.write_text(
        """param([int]$ProcessId, [string]$TargetPath, [string]$DownloadPath, [string]$LogPath, [string]$Version, [string]$ReadyPath)
$ErrorActionPreference = 'Stop'
function Write-UpdateLog([string]$Message) {
    Add-Content -LiteralPath $LogPath -Value "$(Get-Date -Format o) $Message" -Encoding UTF8
}
Write-UpdateLog "Installer helper started; version=$Version; pid=$ProcessId; target=$TargetPath; download=$DownloadPath"
$DownloadedHash = (Get-FileHash -LiteralPath $DownloadPath -Algorithm SHA256).Hash
Write-UpdateLog "Downloaded executable SHA256=$DownloadedHash"
Wait-Process -Id $ProcessId -ErrorAction SilentlyContinue
Write-UpdateLog "Original application process exited"

# Allow OS to finish cleaning up open handles
Start-Sleep -Milliseconds 500

$BackupPath = "$TargetPath.previous"
$UpdatedProcess = $null
try {
    Remove-Item -LiteralPath $ReadyPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $BackupPath -Force -ErrorAction SilentlyContinue
    Move-Item -LiteralPath $TargetPath -Destination $BackupPath -Force
    Write-UpdateLog "Moved existing executable to backup=$BackupPath"
    Move-Item -LiteralPath $DownloadPath -Destination $TargetPath -Force
    Write-UpdateLog "Placed downloaded executable at target=$TargetPath"
    
    # Strip any PyInstaller environment variables in PowerShell session
    Get-ChildItem Env: | Where-Object { $_.Name -like "*MEI*" -or $_.Name -like "PYI*" } | ForEach-Object {
        Remove-Item "Env:\$($_.Name)" -ErrorAction SilentlyContinue
    }

    $PreviousReadyPath = $env:SKM_IMPORTER_UPDATE_READY_FILE
    $env:SKM_IMPORTER_UPDATE_READY_FILE = $ReadyPath
    $UpdatedProcess = Start-Process -FilePath $TargetPath -PassThru
    if ($null -eq $PreviousReadyPath) {
        Remove-Item Env:\SKM_IMPORTER_UPDATE_READY_FILE -ErrorAction SilentlyContinue
    } else {
        $env:SKM_IMPORTER_UPDATE_READY_FILE = $PreviousReadyPath
    }
    Write-UpdateLog "Started updated executable; pid=$($UpdatedProcess.Id)"
    $StartupDeadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Path -LiteralPath $ReadyPath) -and (Get-Date) -lt $StartupDeadline) {
        $UpdatedProcess.Refresh()
        if ($UpdatedProcess.HasExited) {
            throw "Updated executable exited before startup readiness; exit code $($UpdatedProcess.ExitCode)."
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not (Test-Path -LiteralPath $ReadyPath)) {
        throw "Updated executable did not signal startup readiness within 30 seconds."
    }
    Write-UpdateLog "Updated executable signaled startup readiness"
    Remove-Item -LiteralPath $BackupPath -Force
    Remove-Item -LiteralPath $ReadyPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Split-Path -Parent $DownloadPath) -Recurse -Force -ErrorAction SilentlyContinue
    Write-UpdateLog "Update helper completed"
} catch {
    Write-UpdateLog "Update failed: $($_.Exception.ToString())"
    if ($null -ne $UpdatedProcess) {
        $UpdatedProcess.Refresh()
        if (-not $UpdatedProcess.HasExited) {
            Stop-Process -Id $UpdatedProcess.Id -Force -ErrorAction SilentlyContinue
            Wait-Process -Id $UpdatedProcess.Id -ErrorAction SilentlyContinue
            Write-UpdateLog "Stopped updated executable after failed startup"
        }
    }
    if (Test-Path -LiteralPath $BackupPath) {
        Remove-Item -LiteralPath $TargetPath -Force -ErrorAction SilentlyContinue
        Move-Item -LiteralPath $BackupPath -Destination $TargetPath -Force
        Write-UpdateLog "Restored backup executable"
        $RestoredProcess = Start-Process -FilePath $TargetPath -PassThru
        Write-UpdateLog "Restarted restored executable; pid=$($RestoredProcess.Id)"
    }
    Remove-Item -LiteralPath $ReadyPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Split-Path -Parent $DownloadPath) -Recurse -Force -ErrorAction SilentlyContinue
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
            "-LogPath",
            str(log_path),
            "-Version",
            version or "unknown",
            "-ReadyPath",
            str(ready_path),
        ],
        env=clean_env,
        creationflags=creation_flags,
        close_fds=True,
    )