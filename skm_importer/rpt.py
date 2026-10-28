import re
from pathlib import Path
from typing import Mapping, Sequence

from .models import ReportSectionSummary, ReportSummary
from .rpt_schema import default_template


SECTION_PATTERN = re.compile(r"^\s*//\s*---\s*(.+?)\s*---\s*$")
FIELD_PATTERN = re.compile(r"<([^<>]+)>")


def inspect_report(path: str | Path) -> ReportSummary:
    report_path = Path(path)
    if report_path.suffix.lower() != ".rpt":
        raise ValueError("Choose an SKM .rpt report.")
    if not report_path.is_file():
        raise FileNotFoundError(f"SKM report not found: {report_path}")
    text = report_path.read_text(encoding="utf-8-sig", errors="replace")
    sections, errors = parse_report(text)
    return ReportSummary(str(report_path), sections, errors)


def parse_report(text: str) -> tuple[tuple[ReportSectionSummary, ...], tuple[str, ...]]:
    section_name: str | None = None
    fields: tuple[str, ...] = ()
    component_type_index: int | None = None
    component_types: set[str] = set()
    record_count = 0
    malformed_rows: list[int] = []
    section_start_line = 0
    sections: list[ReportSectionSummary] = []
    errors: list[str] = []

    def finish_section() -> None:
        if section_name is None:
            return
        component_type = ""
        sections.append(
            ReportSectionSummary(
                name=section_name,
                component_type=", ".join(sorted(component_types)),
                fields=fields,
                record_count=record_count,
                malformed_rows=tuple(malformed_rows),
            )
        )
        if not fields:
            errors.append(f"{section_name}, line {section_start_line}: component field header was not found.")

    for line_number, line in enumerate(text.splitlines(), start=1):
        section_match = SECTION_PATTERN.match(line)
        if section_match:
            finish_section()
            section_name = section_match.group(1).strip()
            fields = ()
            component_type_index = None
            component_types = set()
            record_count = 0
            malformed_rows = []
            section_start_line = line_number
            continue

        if section_name is None:
            continue

        if line.lstrip().startswith("//"):
            parsed_fields = tuple(FIELD_PATTERN.findall(line))
            if parsed_fields and "ComponentName" in parsed_fields:
                fields = parsed_fields
                try:
                    component_type_index = fields.index("ComponentType")
                except ValueError:
                    component_type_index = None
            continue

        if not line.strip() or not fields:
            continue

        values = line.split("\t")
        record_count += 1
        if component_type_index is not None and component_type_index < len(values):
            component_types.add(values[component_type_index].strip())
        if len(values) != len(fields):
            malformed_rows.append(line_number)
            errors.append(
                f"{section_name}, line {line_number}: expected {len(fields)} fields, found {len(values)}."
            )

    finish_section()
    if not sections:
        errors.append("No SKM component sections were found in the RPT file.")
    return tuple(sections), tuple(errors)


def render_report(
    template_text: str,
    records_by_section: Mapping[str, Sequence[Sequence[object]]],
) -> str:
    lines = template_text.splitlines()
    section_starts = [
        index for index, line in enumerate(lines) if SECTION_PATTERN.match(line)
    ]
    available_sections = {
        SECTION_PATTERN.match(lines[index]).group(1).strip()
        for index in section_starts
    }
    unknown_sections = set(records_by_section) - available_sections
    if unknown_sections:
        names = ", ".join(sorted(unknown_sections))
        raise ValueError(f"Sections are not present in the RPT template: {names}.")

    for section_number in range(len(section_starts) - 1, -1, -1):
        section_start = section_starts[section_number]
        section_end = (
            section_starts[section_number + 1]
            if section_number + 1 < len(section_starts)
            else len(lines)
        )
        section_match = SECTION_PATTERN.match(lines[section_start])
        section_name = section_match.group(1).strip()
        if section_name not in records_by_section:
            continue

        header_index = next(
            (
                index
                for index in range(section_start + 1, section_end)
                if "ComponentName" in FIELD_PATTERN.findall(lines[index])
            ),
            None,
        )
        if header_index is None:
            raise ValueError(f"The {section_name} section has no component field header.")

        fields = FIELD_PATTERN.findall(lines[header_index])
        rendered_records: list[str] = []
        for record_number, record in enumerate(records_by_section[section_name], start=1):
            if len(record) != len(fields):
                raise ValueError(
                    f"{section_name} record {record_number} has {len(record)} values; "
                    f"the template requires {len(fields)}."
                )
            values = ["" if value is None else str(value) for value in record]
            if any("\t" in value or "\r" in value or "\n" in value for value in values):
                raise ValueError(f"{section_name} record {record_number} contains a tab or newline.")
            rendered_records.append("\t".join(values))

        first_record = header_index + 1
        while first_record < section_end and (
            not lines[first_record].strip() or lines[first_record].lstrip().startswith("//")
        ):
            first_record += 1

        record_end = first_record
        while record_end < section_end and lines[record_end].strip() and not lines[record_end].lstrip().startswith("//"):
            record_end += 1

        if first_record < record_end:
            lines[first_record:record_end] = rendered_records
        else:
            lines[header_index + 1 : header_index + 1] = rendered_records

    newline = "\r\n" if "\r\n" in template_text else "\n"
    rendered = newline.join(lines)
    if template_text.endswith(("\n", "\r")):
        rendered += newline
    return rendered


def write_report(
    template_path: str | Path,
    output_path: str | Path,
    records_by_section: Mapping[str, Sequence[Sequence[object]]],
) -> None:
    template = Path(template_path)
    if not template.is_file():
        raise FileNotFoundError(f"SKM report template not found: {template}")
    text = template.read_text(encoding="utf-8-sig", errors="replace")
    rendered = render_report(text, records_by_section)
    Path(output_path).write_text(rendered, encoding="utf-8", newline="")


def write_default_report(
    output_path: str | Path,
    records_by_section: Mapping[str, Sequence[Sequence[object]]],
) -> None:
    output = Path(output_path)
    if output.suffix.lower() != ".rpt":
        raise ValueError("The SKM output path must use the .rpt extension.")
    rendered = render_report(default_template(), records_by_section)
    output.write_text(rendered, encoding="utf-8", newline="")