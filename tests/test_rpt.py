import unittest

from skm_importer.rpt import parse_report, render_report


class ReportParsingTests(unittest.TestCase):
    def test_reads_section_fields_and_records(self) -> None:
        text = (
            "// --- Bus ---\n"
            "//<ComponentName>\t<ComponentType>\t<SystemNominalVoltage>\n"
            "MAIN\t10\t480\n"
            "\n"
            "// --- Cable ---\n"
            "//<ComponentName>\t<ComponentType>\t<ConnectedComponent1>\n"
            "FEED MAIN\t20\tMAIN:1\n"
        )

        sections, errors = parse_report(text)

        self.assertEqual(errors, ())
        self.assertEqual([section.name for section in sections], ["Bus", "Cable"])
        self.assertEqual(sections[0].fields, ("ComponentName", "ComponentType", "SystemNominalVoltage"))
        self.assertEqual(sections[0].component_type, "10")
        self.assertEqual(sections[1].component_type, "20")
        self.assertEqual(sections[0].record_count, 1)
        self.assertEqual(sections[1].record_count, 1)

    def test_reports_malformed_record_field_count(self) -> None:
        text = "// --- Bus ---\n//<ComponentName>\t<ComponentType>\nMAIN\t10\textra\n"

        sections, errors = parse_report(text)

        self.assertEqual(sections[0].malformed_rows, (3,))
        self.assertEqual(len(errors), 1)
        self.assertIn("expected 2 fields, found 3", errors[0])

    def test_reports_missing_sections(self) -> None:
        sections, errors = parse_report("// Export start\nNo data\n")

        self.assertEqual(sections, ())
        self.assertTrue(any("No SKM component sections" in error for error in errors))

    def test_render_replaces_records_using_template_field_order(self) -> None:
        template = (
            "// --- Bus ---\r\n"
            "//<ComponentName>\t<ComponentType>\t<SystemNominalVoltage>\r\n"
            "OLD\t10\t480\r\n"
            "\r\n"
            "// --- Cable ---\r\n"
            "//<ComponentName>\t<ComponentType>\t<ConnectedComponent1>\r\n"
            "OLD FEED\t20\tOLD:1\r\n"
        )

        rendered = render_report(
            template,
            {"Bus": [("MAIN", 10, 480), ("PANEL", 10, 208)]},
        )

        self.assertIn("MAIN\t10\t480\r\nPANEL\t10\t208", rendered)
        self.assertIn("OLD FEED\t20\tOLD:1", rendered)
        self.assertNotIn("OLD\t10\t480", rendered)

    def test_render_rejects_wrong_record_width(self) -> None:
        template = "// --- Bus ---\n//<ComponentName>\t<ComponentType>\n"

        with self.assertRaisesRegex(ValueError, "template requires 2"):
            render_report(template, {"Bus": [("MAIN",)]})

    def test_render_rejects_unknown_section(self) -> None:
        template = "// --- Bus ---\n//<ComponentName>\t<ComponentType>\n"

        with self.assertRaisesRegex(ValueError, "not present in the RPT template"):
            render_report(template, {"Not a section": []})


if __name__ == "__main__":
    unittest.main()