import logging
from pathlib import Path
from typing import Callable
from uuid import uuid4

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
    output = Path(output_path)
    log_path = output.with_suffix(".log")
    output.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"skm_importer.generator.{uuid4().hex}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)

    logger.info("SKM Importer generation started")
    logger.info("Input workbook: %s", workbook_path)
    logger.info("Output report: %s", output)
    logger.info("Detailed generation log: %s", log_path)

    def workbook_progress(percent: int, message: str) -> None:
        logger.info("Workbook inspection %d%%: %s", percent, message)
        if progress:
            progress(int(percent * 0.6), message)

    try:
        logger.info("Starting workbook inspection")
        workbook = inspect_workbook(workbook_path, workbook_progress)
        logger.info(
            "Workbook inspection finished: %d sheet(s), %d workbook issue(s)",
            len(workbook.sheets),
            len(workbook.errors),
        )
        for sheet in workbook.sheets:
            logger.info(
                "Sheet summary: name=%r rows=%d columns=%d populated_rows=%d formulas=%d issues=%d",
                sheet.name,
                sheet.rows,
                sheet.columns,
                sheet.populated_rows,
                sheet.formula_count,
                len(sheet.errors),
            )

        if progress:
            progress(65, "Mapped survey values to SKM components")
        logger.info("Starting workbook-to-SKM record conversion")
        records, warnings = build_records(workbook_path, logger=logger)
        logger.info("Record conversion returned section counts: %s", {name: len(rows) for name, rows in records.items()})
        logger.info("Writing generated SKM report")
        write_default_report(output, records)
        logger.info("Report written successfully: %s (%d bytes)", output, output.stat().st_size)

        logger.info("Re-reading generated report for structural validation")
        report = inspect_report(output)
        logger.info("Report validation found %d issue(s)", len(report.errors))
        for issue in report.errors:
            logger.warning("Report validation: %s", issue)
        for warning in warnings:
            logger.warning("Conversion warning: %s", warning)
        report = ReportSummary(report.path, report.sections, (*report.errors, *warnings))
        logger.info("Generation completed successfully")
        if progress:
            progress(100, "Generated and validated SKM import report")
        return workbook, report
    except Exception:
        logger.exception("Generation failed")
        raise
    finally:
        handler.flush()
        handler.close()
        logger.removeHandler(handler)