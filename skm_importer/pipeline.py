from pathlib import Path
from typing import Callable

from .models import ReportSummary, WorkbookSummary
from .rpt import inspect_report
from .workbook import inspect_workbook


ProgressCallback = Callable[[int, str], None]


def inspect_inputs(
    workbook_path: str | Path,
    report_path: str | Path,
    progress: ProgressCallback | None = None,
) -> tuple[WorkbookSummary, ReportSummary]:
    def workbook_progress(percent: int, message: str) -> None:
        if progress:
            progress(int(percent * 0.72), message)

    workbook = inspect_workbook(workbook_path, workbook_progress)
    if progress:
        progress(78, "Read workbook values and formula results")

    report = inspect_report(report_path)
    if progress:
        progress(100, "Parsed SKM sections and checked field counts")
    return workbook, report