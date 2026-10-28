import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from skm_importer.workbook import inspect_workbook


class WorkbookInspectionTests(unittest.TestCase):
    def test_summarizes_sheets_values_and_formulas(self) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "FIELD CABLEOCP"
        sheet["A1"] = "Header"
        sheet["A2"] = "Cable 1"
        sheet["B2"] = "Load 1"
        sheet["C2"] = "=1+1"

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "input.xlsx"
            workbook.save(path)
            summary = inspect_workbook(path)

        self.assertEqual(len(summary.sheets), 1)
        self.assertEqual(summary.sheets[0].name, "FIELD CABLEOCP")
        self.assertEqual(summary.sheets[0].populated_rows, 2)
        self.assertEqual(summary.sheets[0].formula_count, 1)

    def test_rejects_unsupported_workbook_extension(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported workbook format"):
            inspect_workbook("input.csv")


if __name__ == "__main__":
    unittest.main()