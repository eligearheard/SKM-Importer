import os
import tempfile
import unittest
from unittest.mock import patch

from skm_importer.preferences import load_update_interval, save_update_interval


class UpdateIntervalPreferenceTests(unittest.TestCase):
    def test_defaults_to_five_minutes_and_persists_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.dict(os.environ, {"APPDATA": temporary_directory}):
                self.assertEqual(load_update_interval(), 5)
                save_update_interval(12)
                self.assertEqual(load_update_interval(), 12)

    def test_rejects_interval_outside_supported_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 1 and 1440"):
            save_update_interval(1441)


if __name__ == "__main__":
    unittest.main()