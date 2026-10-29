import tempfile
import unittest
from pathlib import Path

from scripts.stamp_version import normalize_release_version, stamp_version


class ReleaseVersionTests(unittest.TestCase):
    def test_normalizes_any_count_of_numeric_components(self) -> None:
        self.assertEqual(normalize_release_version("v0.1.2.3.4.5"), "0.1.2.3.4.5")

    def test_preserves_prerelease_and_build_suffixes(self) -> None:
        self.assertEqual(normalize_release_version("v1.2.3.4-rc.1+build.2"), "1.2.3.4-rc.1+build.2")

    def test_rejects_versions_with_fewer_than_three_components(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least three"):
            normalize_release_version("v1.2")

    def test_rejects_nonnumeric_components(self) -> None:
        with self.assertRaisesRegex(ValueError, "numeric"):
            normalize_release_version("v1.2.beta.4")

    def test_stamps_version_file_and_returns_tag(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            version_file = Path(temporary_directory) / "version.py"
            tag = stamp_version("v0.1.2.3", version_file)

            self.assertEqual(tag, "v0.1.2.3")
            self.assertEqual(version_file.read_text(encoding="ascii"), '__version__ = "0.1.2.3"\n')


if __name__ == "__main__":
    unittest.main()