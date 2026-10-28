from pathlib import Path
from typing import Callable

from .conversion import build_records
from .models import ReportSummary, WorkbookSummary
from .rpt import inspect_report, write_default_report
from .workbook import inspect_workbook


ProgressCallback = Callable[[int, str], None]


def generate_import_report(
    workbook_path: str | Path,
    output_path: str | Path,
    progress: ProgressCallback | None = None,
) -> tuple[WorkbookSummary, ReportSummary]:
    def workbook_progress(percent: int, message: str) -> None:
        if progress:
            progress(int(percent * 0.6), message)

    workbook = inspect_workbook(workbook_path, workbook_progress)
    if progress:
        progress(65, "Mapped survey values to SKM components")
    records, warnings = build_records(workbook_path)
    write_default_report(output_path, records)
    report = inspect_report(output_path)
    report = ReportSummary(report.path, report.sections, (*report.errors, *warnings))
    if progress:
        progress(100, "Generated and validated SKM import report")
    return workbook, report