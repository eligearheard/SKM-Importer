# SKM Importer

Desktop application for inspecting Excel workbooks and SKM Power*Tools `.rpt` exports before generating an import report.

## Run on Windows

1. Install Python 3.11 or newer.
2. Run `setup.bat` once to create a local virtual environment and install dependencies.
3. Run `run.bat` to open the desktop application.

The app currently inspects `.xls`, `.xlsx`, and `.xlsm` workbooks and an SKM `.rpt` reference export. It reports workbook sheets, formulas, Excel formula errors, SKM sections, field counts, and malformed records with visible progress. It does not generate an `.rpt` yet; the workbook-to-SKM field mappings must be verified before producing engineering data.

## Run tests

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
```
