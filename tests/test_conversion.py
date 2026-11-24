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

    def test_maps_fuse_display_fields_without_library_link(self) -> None:
        workbook = Workbook()
        cable_sheet = workbook.active
        cable_sheet.title = "FIELD CABLEOCP"
        for _ in range(5):
            cable_sheet.append([None] * 32)
        cable_sheet.append([98, "BP", "MAIN", "PNL", "H4", 480, "VCB", "NO", None, 1, 10, 3, "CU", "THHN", "Magnetic", "4-1/C+G"])
        fuse_row = [None] * 32
        fuse_row[0:3] = [99, "PNL", "H4"]
        fuse_row[19:23] = ["GOULD SHAWMUT", "A4BY", None, 2000]
        fuse_row[23:31] = [0.8, 10, 5, 0.3, 10, 0.1, 8, 0.05]
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
        self.assertEqual(len(warnings), 1)
        self.assertIn("SKM settings remain blank", warnings[0])
        self.assertEqual(fuse["ProtectionType"], "11041")
        self.assertEqual(fuse["Description"], "")
        self.assertEqual(fuse["Manufacturer"], "GOULD SHAWMUT")
        self.assertEqual(fuse["Type"], "A4BY")
        self.assertEqual(fuse["Frame/Model"], "A4BY")
        self.assertEqual(fuse["InterruptingRating"], "")
        self.assertEqual(fuse["Sensor/Trip"], "2000.0")
        self.assertEqual(fuse["Plug"], "2000.0")
        self.assertEqual(fuse["ProtectiveDeviceLibName"], "")
        self.assertEqual(fuse["TCC No."], "")
        self.assertEqual(fuse["Settings"], "")
        self.assertEqual(report_fuse["Description"], "")
        self.assertEqual(report_fuse["Manufacturer"], "GOULD SHAWMUT")
        self.assertEqual(report_fuse["Type"], "A4BY")
        self.assertEqual(report_fuse["Frame/Model"], "A4BY")
        self.assertEqual(report_fuse["InterruptingRating"], "")
        self.assertEqual(report_fuse["Sensor/Trip"], "2000.0")
        self.assertEqual(report_fuse["Plug"], "2000.0")
        self.assertEqual(report_fuse["ProtectiveDeviceLibName"], "")
        self.assertEqual(report_fuse["TCC No."], "")
        self.assertEqual(report_fuse["Settings"], "")

    def test_maps_breaker_display_fields_without_library_link(self) -> None:
        workbook = Workbook()
        cable_sheet = workbook.active
        cable_sheet.title = "FIELD CABLEOCP"
        for _ in range(5):
            cable_sheet.append([None] * 32)
        breaker_row = [None] * 32
        breaker_row[0:8] = [97, "BP", "PNL H4", "DISC", "PNL H4", 480, "VCB", "NO"]
        breaker_row[9:16] = [1, 6, 3, "CU", "THHN", "Magnetic", "4-1/C+G"]
        breaker_row[19:23] = ["FEDERAL PIONEER", "NF", 18, 100]
        breaker_row[23:31] = [0.8, 10, 5, 0.3, 10, 0.1, 8, 0.05]
        cable_sheet.append(breaker_row)

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "survey.xlsx"
            report_path = Path(temporary_directory) / "generated.rpt"
            workbook.save(path)
            records, warnings = build_records(path)
            write_default_report(report_path, records)
            report_lines = report_path.read_text(encoding="utf-8").splitlines()
            device_section = report_lines.index("// --- Protective Device ---")
            report_headers = [
                header.lstrip("/").strip("<>")
                for header in report_lines[device_section + 1].split("\t")
            ]
            report_values = report_lines[device_section + 2].split("\t")
            report_breaker = dict(
                zip(
                    SECTION_FIELDS["Protective Device"],
                    report_values,
                )
            )

        breaker = dict(zip(SECTION_FIELDS["Protective Device"], records["Protective Device"][0]))
        reference_positions = {
            "Manufacturer": 14,
            "Type": 15,
            "Description": 16,
            "TCC No.": 17,
            "Frame/Model": 19,
            "Frame/Rating": 20,
            "FrameVoltage": 21,
            "InterruptingRating": 22,
            "Sensor/Trip": 23,
            "Plug": 24,
            "ProtectiveDeviceLibName": 30,
            "Settings": 37,
        }
        self.assertEqual(len(report_headers), 51)
        self.assertEqual(len(report_values), 51)
        for field, position in reference_positions.items():
            self.assertEqual(report_headers[position - 1], field)
        self.assertEqual(len(warnings), 1)
        self.assertIn("SKM settings remain blank", warnings[0])
        self.assertEqual(breaker["ProtectionType"], "11003")
        self.assertEqual(breaker["Description"], "")
        self.assertEqual(breaker["Manufacturer"], "FEDERAL PIONEER")
        self.assertEqual(breaker["Type"], "NF")
        self.assertEqual(breaker["Frame/Model"], "NF")
        self.assertEqual(breaker["FrameVoltage"], "480.0")
        self.assertEqual(breaker["InterruptingRating"], "18.0")
        self.assertEqual(breaker["Sensor/Trip"], "100.0")
        self.assertEqual(breaker["Plug"], "100.0")
        self.assertEqual(breaker["ProtectiveDeviceLibName"], "")
        self.assertEqual(breaker["TCC No."], "")
        self.assertEqual(breaker["Settings"], "")
        self.assertEqual(report_breaker["Description"], "")
        self.assertEqual(report_breaker["Manufacturer"], "FEDERAL PIONEER")
        self.assertEqual(report_breaker["Type"], "NF")
        self.assertEqual(report_breaker["Frame/Model"], "NF")
        self.assertEqual(report_breaker["FrameVoltage"], "480.0")
        self.assertEqual(report_breaker["InterruptingRating"], "18.0")
        self.assertEqual(report_breaker["Sensor/Trip"], "100.0")
        self.assertEqual(report_breaker["Plug"], "100.0")
        self.assertEqual(report_breaker["ProtectiveDeviceLibName"], "")
        self.assertEqual(report_breaker["TCC No."], "")
        self.assertEqual(report_breaker["Settings"], "")

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
        self.assertEqual(protection["SystemNominalVoltage"], "208.0")
        self.assertEqual(protection["Description"], "")
        self.assertEqual(protection["Manufacturer"], "GE")
        self.assertEqual(protection["Type"], "TQD")
        self.assertEqual(protection["Frame/Model"], "TQD")
        self.assertEqual(protection["FrameVoltage"], "208.0")
        self.assertEqual(protection["ProtectiveDeviceLibName"], "")
        self.assertEqual(protection["InterruptingRating"], "10.0")
        self.assertEqual(protection["Sensor/Trip"], "225.0")
        self.assertEqual(protection["Plug"], "225.0")
        self.assertEqual(protection["Settings"], "")
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

    def test_splits_bus_riser_for_each_bus_plug_and_keeps_duplicate_plugs(self) -> None:
        workbook = Workbook()
        cable_sheet = workbook.active
        cable_sheet.title = "FIELD CABLEOCP"
        for _ in range(5):
            cable_sheet.append([None] * 32)
        cable_sheet.append([1, "SWBD", "MSB", "BUS RISER", "1", 480, None, None, None, 3, "BUS (2000A)", 99, "AL"])
        cable_sheet.append([2, "BUS RISER", "1", "BP", "H1", 480, None, None, None, 3, "BUS (2000A)", 0.1, "AL"])
        cable_sheet.append([3, "BP", "H1", "PNL", "H1", 480, None, None, None, 3, "10", 20, "CU", "THHN", "Magnetic", "4-1/C+G"])
        cable_sheet.append([4, "BUS RISER", "1", "BP", "H1", 480, None, None, None, 3, "BUS (2000A)", 0.1, "AL"])
        cable_sheet.append([5, "BP", "H1", "PNL", "H1", 480, None, None, None, 3, "10", 20, "CU", "THHN", "Magnetic", "4-1/C+G"])
        cable_sheet.append([6, "BUS RISER", "1", "BP", "H2", 480, None, None, None, 3, "BUS (2000A)", 0.1, "AL"])
        cable_sheet.append([7, "BP", "H2", "PNL", "H2", 480, None, None, None, 3, "10", 20, "CU", "THHN", "Magnetic", "4-1/C+G"])

        bus_duct_sheet = workbook.create_sheet("BUS DUCT")
        for _ in range(5):
            bus_duct_sheet.append([])
        bus_duct_sheet.append([1, "BUS RISER 1", "Spectra", 2000, 10, "GE", "AL"])

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "survey.xlsx"
            workbook.save(path)
            records, warnings = build_records(path)

        cables = {
            cable["ComponentName"]: cable
            for cable in (
                dict(zip(SECTION_FIELDS["Cable"], record))
                for record in records["Cable"]
            )
        }
        buses = {
            bus["ComponentName"]
            for bus in (
                dict(zip(SECTION_FIELDS["Bus"], record))
                for record in records["Bus"]
            )
        }

        self.assertEqual(cables["FEED BUS RISER 1"]["ConnectedComponent1"], "SWBD MSB:1")
        self.assertEqual(cables["FEED BUS RISER 1"]["ConnectedComponent2"], "BUS RISER 1:1")
        self.assertEqual(cables["FEED BUS RISER 1"]["Length"], "9.8")
        self.assertEqual(cables["FEED BUS RISER 1 - 1"]["Length"], "0.1")
        self.assertEqual(cables["FEED BUS RISER 1 - 2"]["Length"], "0.1")
        self.assertEqual(cables["FEED BUS RISER 1 - 1"]["ConnectedComponent1"], "BUS RISER 1:1")
        self.assertEqual(cables["FEED BUS RISER 1 - 1"]["ConnectedComponent2"], "BUS RISER 1 - 1:1")
        self.assertEqual(cables["FEED BUS RISER 1 - 2"]["ConnectedComponent1"], "BUS RISER 1 - 1:1")
        self.assertEqual(cables["FEED BUS RISER 1 - 2"]["ConnectedComponent2"], "BUS RISER 1 - 2:1")
        for cable_name in ("FEED BUS RISER 1", "FEED BUS RISER 1 - 1", "FEED BP H1"):
            self.assertEqual(cables[cable_name]["CableSize"], "2000 Amps")
            self.assertEqual(cables[cable_name]["NeutralSize"], "N/A")
            self.assertEqual(cables[cable_name]["QtyPerPhase"], "1")
            self.assertEqual(cables[cable_name]["Manufacturer"], "BUS")
            self.assertEqual(cables[cable_name]["ConductorType"], "Aluminum")
            self.assertEqual(cables[cable_name]["#/Conductors"], "0")
            self.assertEqual(cables[cable_name]["DuctMaterial"], "Busway")
            self.assertEqual(cables[cable_name]["InsulationType"], "Epoxy")
            self.assertEqual(cables[cable_name]["InsulationClass"], "Class B")
            self.assertEqual(cables[cable_name]["Conductor Desc"], "225-5000A")
            self.assertEqual(cables[cable_name]["Installation"], "Sandwich")
            self.assertEqual(cables[cable_name]["AmpacityDescription"], "NONE")
            self.assertEqual(cables[cable_name]["CircularMils"], "2000000")
            self.assertEqual(cables[cable_name]["Ampacity"], "2000.0")
            self.assertEqual(cables[cable_name]["Ampacity Sec"], "2000.0")
            self.assertEqual(cables[cable_name]["KeyInLibrary"], "1")
        self.assertEqual(cables["FEED BP H1"]["ConnectedComponent1"], "BUS RISER 1:1")
        self.assertEqual(cables["FEED BP H1 - 2"]["ConnectedComponent1"], "BUS RISER 1 - 1:1")
        self.assertEqual(cables["FEED BP H2"]["ConnectedComponent1"], "BUS RISER 1 - 2:1")
        self.assertEqual(cables["FEED PNL H1 - 2"]["ConnectedComponent1"], "BP H1 - 2:1")
        self.assertIn("BP H1 - 2", buses)
        self.assertIn("BUS RISER 1 - 2", buses)
        self.assertNotIn("BUS RISER 1 - 3", buses)
        self.assertTrue(any("duplicate bus plug ID H1" in warning for warning in warnings))
        self.assertFalse(any("FEED BP H1 has an unsupported cable size" in warning for warning in warnings))

    def test_reports_unsupported_workbook_format(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires an .xlsx or .xlsm"):
            build_records("survey.xls")


if __name__ == "__main__":
    unittest.main()