import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from skm_importer.conversion import build_records
from skm_importer.pipeline import generate_import_report
from skm_importer.rpt import write_default_report
from skm_importer.rpt_schema import SECTION_FIELDS


class WorkbookConversionTests(unittest.TestCase):
    def test_maps_cable_to_expected_library_entry(self) -> None:
        workbook = Workbook()
        cable_sheet = workbook.active
        cable_sheet.title = "FIELD CABLEOCP"
        for _ in range(5):
            cable_sheet.append([None] * 32)
        cable_sheet.append([90, "BP", "AHU-4", "STR", "AHU-4", 480, "VCB", "NO", None, 1, 10, 3, "CU", "THHN", "Magnetic", "4-1/C+G"])

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "survey.xlsx"
            workbook.save(path)
            records, warnings = build_records(path)

        cable = dict(zip(SECTION_FIELDS["Cable"], records["Cable"][0]))
        self.assertEqual(warnings, ())
        self.assertEqual(cable["ConnectedComponent1"], "BP AHU-4:1")
        self.assertEqual(cable["ConnectedComponent2"], "STR AHU-4:1")
        self.assertEqual(cable["Manufacturer"], "IEEE 141 - Red Book")
        self.assertEqual(cable["Description"], "NEC Table 310-16")
        self.assertEqual(cable["DuctMaterial"], "Magnetic")
        self.assertEqual(cable["InsulationClass"], "THHN")
        self.assertEqual(cable["Installation"], "Conduit")
        self.assertEqual(cable["VoltageRating"], "600")
        self.assertEqual(cable["CableSize"], "10")
        self.assertEqual(cable["CircularMils"], "10380")
        self.assertEqual(cable["KeyInLibrary"], "1")

    def test_maps_fuse_without_aic_and_keeps_sensor_plug(self) -> None:
        workbook = Workbook()
        cable_sheet = workbook.active
        cable_sheet.title = "FIELD CABLEOCP"
        for _ in range(5):
            cable_sheet.append([None] * 32)
        cable_sheet.append([98, "BP", "MAIN", "PNL", "H4", 480, "VCB", "NO", None, 1, 10, 3, "CU", "THHN", "Magnetic", "4-1/C+G"])
        fuse_row = [None] * 32
        fuse_row[0:3] = [99, "PNL", "H4"]
        fuse_row[19:23] = ["LITTELFUSE", "FLSRID", None, 70]
        cable_sheet.append(fuse_row)

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "survey.xlsx"
            report_path = Path(temporary_directory) / "generated.rpt"
            workbook.save(path)
            records, warnings = build_records(path)
            write_default_report(report_path, records)
            report_lines = report_path.read_text(encoding="utf-8").splitlines()
            device_section = report_lines.index("// --- Protective Device ---")
            report_fuse = dict(
                zip(
                    SECTION_FIELDS["Protective Device"],
                    report_lines[device_section + 2].split("\t"),
                )
            )

        fuse = dict(zip(SECTION_FIELDS["Protective Device"], records["Protective Device"][0]))
        self.assertEqual(warnings, ())
        self.assertEqual(fuse["ProtectionType"], "11041")
        self.assertEqual(fuse["Description"], "Manufacturer: LITTELFUSE; Type: FLSRID; Sensor/Plug: 70")
        self.assertEqual(fuse["Manufacturer"], "")
        self.assertEqual(fuse["Type"], "")
        self.assertEqual(fuse["InterruptingRating"], "")
        self.assertEqual(fuse["Sensor/Trip"], "")
        self.assertEqual(fuse["Plug"], "")
        self.assertEqual(fuse["ProtectiveDeviceLibName"], "")
        self.assertEqual(report_fuse["Description"], fuse["Description"])
        self.assertEqual(report_fuse["InterruptingRating"], "")
        self.assertEqual(report_fuse["Sensor/Trip"], "")
        self.assertEqual(report_fuse["Plug"], "")

    def test_maps_breaker_manufacturer_type_aic_and_sensor_plug(self) -> None:
        workbook = Workbook()
        cable_sheet = workbook.active
        cable_sheet.title = "FIELD CABLEOCP"
        for _ in range(5):
            cable_sheet.append([None] * 32)
        breaker_row = [None] * 32
        breaker_row[0:8] = [97, "BP", "PNL H4", "DISC", "PNL H4", 480, "VCB", "NO"]
        breaker_row[9:16] = [1, 6, 3, "CU", "THHN", "Magnetic", "4-1/C+G"]
        breaker_row[19:23] = ["FEDERAL PIONEER", "NF", 18, 100]
        cable_sheet.append(breaker_row)

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "survey.xlsx"
            report_path = Path(temporary_directory) / "generated.rpt"
            workbook.save(path)
            records, warnings = build_records(path)
            write_default_report(report_path, records)
            report_lines = report_path.read_text(encoding="utf-8").splitlines()
            device_section = report_lines.index("// --- Protective Device ---")
            report_breaker = dict(
                zip(
                    SECTION_FIELDS["Protective Device"],
                    report_lines[device_section + 2].split("\t"),
                )
            )

        breaker = dict(zip(SECTION_FIELDS["Protective Device"], records["Protective Device"][0]))
        self.assertEqual(warnings, ())
        self.assertEqual(breaker["ProtectionType"], "11003")
        self.assertEqual(breaker["Description"], "Manufacturer: FEDERAL PIONEER; Type: NF; AIC: 18; Sensor/Plug: 100")
        self.assertEqual(breaker["Manufacturer"], "")
        self.assertEqual(breaker["Type"], "")
        self.assertEqual(breaker["InterruptingRating"], "")
        self.assertEqual(breaker["Sensor/Trip"], "")
        self.assertEqual(breaker["Plug"], "")
        self.assertEqual(breaker["ProtectiveDeviceLibName"], "")
        self.assertEqual(report_breaker["Description"], breaker["Description"])
        self.assertEqual(report_breaker["Manufacturer"], "")
        self.assertEqual(report_breaker["Type"], "")
        self.assertEqual(report_breaker["InterruptingRating"], "")
        self.assertEqual(report_breaker["Sensor/Trip"], "")
        self.assertEqual(report_breaker["Plug"], "")

    def test_builds_skm_records_without_a_reference_report(self) -> None:
        workbook = Workbook()
        cable_sheet = workbook.active
        cable_sheet.title = "FIELD CABLEOCP"
        cable_sheet.append([None] * 32)
        cable_sheet.append([None] * 32)
        cable_sheet.append([None] * 32)
        cable_sheet.append([None] * 32)
        cable_sheet.append([None] * 32)
        cable_sheet.append([1, "TRANS", "TX1", "PNL", "L8C", 208, "VCB", "NO", None, 3, 2, 20, "CU", "XHHW", "Magnetic", "3-1/C+G"])
        main_device = [None] * 32
        main_device[0:4] = [2, "PNL", "L8C", "CB MAIN"]
        main_device[19:23] = ["GE", "TQD", 10, 225]
        cable_sheet.append(main_device)
        cable_sheet.append([3, "UTILITY", "1", "SWBD", "MAIN", 480, None, None, None, 3, 500, 40, "CU", "THHN", "Magnetic", "4-1/C+G"])

        transformer_sheet = workbook.create_sheet("XFMR")
        for _ in range(5):
            transformer_sheet.append([])
        transformer_sheet.append([1, "TRANS TX1", 480, 208, 75, 5.5, "DRY", "DELTA - WYE GND", 3.15])

        bus_duct_sheet = workbook.create_sheet("BUS DUCT")
        for _ in range(5):
            bus_duct_sheet.append([])
        bus_duct_sheet.append([1, "BUS RISER 1", "Spectra", 2000, 100, "GE", "AL"])

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "survey.xlsx"
            output_path = Path(temporary_directory) / "generated.rpt"
            log_path = output_path.with_suffix(".log")
            workbook.save(path)
            records, warnings = build_records(path)
            workbook_summary, report_summary = generate_import_report(path, output_path)
            log_text = log_path.read_text(encoding="utf-8")
            self.assertTrue(output_path.is_file())
            self.assertTrue(log_path.is_file())

        self.assertEqual(len(warnings), 1)
        self.assertIn("construction type was not mapped for 1 records", warnings[0])
        self.assertIn("FIELD CABLEOCP row 6 inputs", log_text)
        self.assertIn("mapped fields", log_text)
        self.assertIn("Generation completed successfully", log_text)
        self.assertEqual(report_summary.errors, warnings)
        self.assertEqual(len(workbook_summary.sheets), 3)
        transformer = dict(zip(SECTION_FIELDS["2-Winding Transformer"], records["2-Winding Transformer"][0]))
        cable = dict(zip(SECTION_FIELDS["Cable"], records["Cable"][0]))
        protection = dict(zip(SECTION_FIELDS["Protective Device"], records["Protective Device"][0]))
        utility = dict(zip(SECTION_FIELDS["Utility"], records["Utility"][0]))
        bus_records = [dict(zip(SECTION_FIELDS["Bus"], record)) for record in records["Bus"]]
        bus_duct = next(bus for bus in bus_records if bus["ComponentName"] == "BUS RISER 1")
        survey_bus = next(bus for bus in bus_records if bus["ComponentName"] == "PNL L8C")
        self.assertEqual(transformer["ComponentName"], "TRANS TX1")
        self.assertEqual(transformer["ConnectedComponent2"], "TX1:1")
        self.assertEqual(transformer["InService"], "1")
        self.assertEqual(transformer["TransformerType"], "0")
        self.assertEqual(transformer["Phase"], "7")
        self.assertEqual(transformer["Size/Do Not Size"], "0")
        self.assertEqual(transformer["SizingCriteria"], "0")
        self.assertEqual(cable["ComponentName"], "FEED PNL L8C")
        self.assertEqual(cable["ConnectedComponent1"], "TX1:1")
        self.assertEqual(cable["ConnectedComponent2"], "CB MAIN PNL L8C:1")
        self.assertEqual(cable["CableSize"], "2")
        self.assertEqual(cable["Length"], "20")
        self.assertEqual(cable["InService"], "1")
        self.assertEqual(cable["Phase"], "7")
        self.assertEqual(cable["Size/Do Not Size"], "0")
        self.assertEqual(cable["DuctMaterial"], "Magnetic")
        self.assertEqual(cable["KeyInLibrary"], "1")
        self.assertEqual(cable["InsulationType"], "PVC")
        self.assertEqual(cable["InsulationClass"], "XHHW")
        self.assertEqual(protection["ComponentName"], "CB MAIN PNL L8C")
        self.assertEqual(protection["InService"], "1")
        self.assertEqual(protection["ProtectionType"], "11003")
        self.assertEqual(protection["Description"], "Manufacturer: GE; Type: TQD; AIC: 10; Sensor/Plug: 225")
        self.assertEqual(protection["Manufacturer"], "")
        self.assertEqual(protection["Type"], "")
        self.assertEqual(protection["ProtectiveDeviceLibName"], "")
        self.assertEqual(protection["InterruptingRating"], "")
        self.assertEqual(protection["Sensor/Trip"], "")
        self.assertEqual(protection["Plug"], "")
        self.assertEqual(protection["Poles"], "0")
        self.assertEqual(protection["INT/SC RatingBasis"], "0")
        self.assertEqual(protection["ConnectionType"], "2")
        self.assertEqual(protection["AF_ElectrodeConfig"], "0")
        self.assertEqual(protection["AF_EquipType"], "1")
        self.assertEqual(protection["AF_UnLinkedBoxDimensions"], "0")
        self.assertEqual(protection["AF_UnLinkedElectrodeConfig"], "0")
        self.assertEqual(protection["AF_UnLinkedEquipType"], "0")
        self.assertEqual(protection["ConnectedComponent1"], "FEED PNL L8C:2")
        self.assertEqual(protection["ConnectedComponent2"], "PNL L8C:1")
        self.assertEqual(protection["Frame/Rating"], "")
        self.assertEqual(utility["InService"], "1")
        self.assertEqual(utility["Phase"], "7")
        self.assertEqual(utility["SC Contribution Unit"], "2")
        self.assertEqual(utility["SC Contribution Type"], "0")
        self.assertEqual(survey_bus["AF_Inst/ZSI Avail"], "0")
        self.assertEqual(survey_bus["AF_ElectrodeConfig"], "1")
        self.assertEqual(survey_bus["AF_EquipType"], "1")
        self.assertEqual(survey_bus["AF_UnLinkedBoxDimensions"], "0")
        self.assertEqual(survey_bus["AF_UnLinkedElectrodeConfig"], "1")
        self.assertEqual(survey_bus["AF_UnLinkedEquipType"], "1")
        self.assertEqual(bus_duct["ContinuousRating"], "2000")
        self.assertEqual(bus_duct["Manufacturer"], "GE")
        self.assertEqual(bus_duct["Description"], "Spectra")

    def test_reports_unsupported_workbook_format(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires an .xlsx or .xlsm"):
            build_records("survey.xls")


if __name__ == "__main__":
    unittest.main()