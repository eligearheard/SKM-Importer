import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skm_importer.updater import UpdateInfo, check_for_update, download_update, install_update


class UpdateCheckTests(unittest.TestCase):
    def release_response(self, tag: str) -> io.BytesIO:
        release = {
            "tag_name": tag,
            "assets": [
                {
                    "name": "SKM-Importer.exe",
                    "browser_download_url": "https://example.test/SKM-Importer.exe",
                }
            ],
        }
        return io.BytesIO(json.dumps(release).encode())

    def test_returns_asset_for_newer_release(self) -> None:
        with patch("skm_importer.updater.urllib.request.urlopen", return_value=self.release_response("v0.2.0")):
            update = check_for_update("0.1.0")

        self.assertEqual(update, UpdateInfo("0.2.0", "https://example.test/SKM-Importer.exe", None))

    def test_returns_none_for_current_release(self) -> None:
        with patch("skm_importer.updater.urllib.request.urlopen", return_value=self.release_response("v0.1.0")):
            update = check_for_update("0.1.0")

        self.assertIsNone(update)

    def test_download_checks_release_digest(self) -> None:
        payload = b"test executable bytes"
        update = UpdateInfo(
            "0.2.0",
            "https://example.test/SKM-Importer.exe",
            hashlib.sha256(payload).hexdigest(),
        )
        with patch("skm_importer.updater.urllib.request.urlopen", return_value=io.BytesIO(payload)):
            downloaded = download_update(update)

        try:
            self.assertEqual(downloaded.read_bytes(), payload)
        finally:
            downloaded.unlink()
            downloaded.parent.rmdir()

    def test_rejects_bad_download_digest(self) -> None:
        update = UpdateInfo("0.2.0", "https://example.test/SKM-Importer.exe", "0" * 64)
        with patch("skm_importer.updater.urllib.request.urlopen", return_value=io.BytesIO(b"invalid")):
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                download_update(update)

    def test_installer_waits_for_all_app_processes_before_replacing_executable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            helper_dir = Path(temporary_directory)
            executable_path = helper_dir / "SKM-Importer.exe"
            downloaded_path = helper_dir / "download" / "SKM-Importer.exe"
            downloaded_path.parent.mkdir()
            downloaded_path.touch()
            with (
                patch("skm_importer.updater.sys.platform", "win32"),
                patch("skm_importer.updater.sys.frozen", True, create=True),
                patch("skm_importer.updater.sys.executable", str(executable_path)),
                patch("skm_importer.updater.tempfile.gettempdir", return_value=temporary_directory),
                patch("skm_importer.updater.os.getpid", return_value=123),
                patch("skm_importer.updater.subprocess.Popen") as popen,
            ):
                install_update(downloaded_path)

            script_path = helper_dir / "skm-importer-update-123.ps1"
            script = script_path.read_text(encoding="utf-8")
            self.assertIn("Get-CimInstance -ClassName Win32_Process", script)
            self.assertIn("$_.ExecutablePath -ieq $TargetPath", script)
            self.assertLess(script.index("$runningProcesses ="), script.index("Move-Item -LiteralPath $TargetPath"))
            popen.assert_called_once()


if __name__ == "__main__":
    unittest.main()