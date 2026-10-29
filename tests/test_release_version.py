import tempfile
import unittest
from pathlib import Path

from scripts.build_windows import find_runtime_dlls
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


class RuntimeBundlingTests(unittest.TestCase):
    def test_finds_vc_runtime_dlls_in_python_build_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            for name in ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"):
                (directory / name).touch()

            dlls = find_runtime_dlls((directory,))

        self.assertEqual({path.name for path in dlls}, {"vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"})

    def test_requires_core_vc_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(RuntimeError, "vcruntime140.dll"):
                find_runtime_dlls((Path(temporary_directory),))


if __name__ == "__main__":
    unittest.main()