import hashlib
import io
import json
import tempfile
import unittest
from urllib.error import HTTPError
from pathlib import Path
from unittest.mock import patch

from skm_importer.updater import LATEST_RELEASE_URL, UpdateInfo, check_for_update, download_update


class UpdateCheckTests(unittest.TestCase):
    def release_response(self, tag: str, download_url: str | None = None) -> io.BytesIO:
        release = {
            "tag_name": tag,
            "assets": [
                {
                    "name": "SKM-Importer.exe",
                    "browser_download_url": download_url or (
                        f"https://github.com/eligearheard/SKM-Importer/releases/download/{tag}/SKM-Importer.exe"
                    ),
                }
            ],
        }
        return io.BytesIO(json.dumps(release).encode())

    def test_returns_asset_for_newer_release(self) -> None:
        with patch("skm_importer.updater.urllib.request.urlopen", return_value=self.release_response("v0.2.0")):
            update = check_for_update("0.1.0")

        self.assertEqual(
            update,
            UpdateInfo(
                "0.2.0",
                "https://github.com/eligearheard/SKM-Importer/releases/download/v0.2.0/SKM-Importer.exe",
                None,
            ),
        )

    def test_reports_when_no_public_release_exists(self) -> None:
        error = HTTPError(LATEST_RELEASE_URL, 404, "Not Found", None, None)
        with patch("skm_importer.updater.urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(RuntimeError, "No publicly accessible GitHub release"):
                check_for_update("0.1.0")

    def test_rejects_asset_url_outside_github(self) -> None:
        with patch(
            "skm_importer.updater.urllib.request.urlopen",
            return_value=self.release_response("v0.2.0", "https://example.test/SKM-Importer.exe"),
        ):
            with self.assertRaisesRegex(RuntimeError, "unexpected download URL"):
                check_for_update("0.1.0")

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


if __name__ == "__main__":
    unittest.main()