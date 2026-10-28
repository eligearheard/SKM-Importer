from dataclasses import dataclass


@dataclass(frozen=True)
class WorkbookSheetSummary:
    name: str
    rows: int
    columns: int
    populated_rows: int
    formula_count: int
    errors: tuple[str, ...]


@dataclass(frozen=True)
class WorkbookSummary:
    path: str
    sheets: tuple[WorkbookSheetSummary, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ReportSectionSummary:
    name: str
    component_type: str
    fields: tuple[str, ...]
    record_count: int
    malformed_rows: tuple[int, ...]


@dataclass(frozen=True)
class ReportSummary:
    path: str
    sections: tuple[ReportSectionSummary, ...]
    errors: tuple[str, ...]