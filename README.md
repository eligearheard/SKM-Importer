# SKM Importer

Desktop application for inspecting Excel workbooks and SKM Power*Tools `.rpt` exports before generating an import report.

## Easiest: Download the app

Once a Windows release is published, download `SKM-Importer.exe` from [the latest release](https://github.com/eligearheard/SKM-Importer/releases/latest) and double-click it. Python and the IDE are not required.

Windows may display a SmartScreen warning because the app is not code-signed.

## Build a Windows download

For maintainers, the easiest way to publish a download is from GitHub: open **Actions → Windows release → Run workflow**, enter a version such as `v0.1.0`, and start the workflow. GitHub builds the Windows app and publishes the release; no local Python setup is needed.

To build locally instead, run `build_windows.bat` on Windows with Python 3.11 or newer. It creates a standalone `dist\SKM-Importer.exe`. Pushing a version tag also publishes a release automatically:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

## Run from source

Run `setup.bat` once, then `run.bat`. This creates a local virtual environment and installs the dependencies.

The app currently inspects `.xls`, `.xlsx`, and `.xlsm` workbooks and an SKM `.rpt` reference export. It reports workbook sheets, formulas, Excel formula errors, SKM sections, field counts, and malformed records with visible progress. It does not generate a project `.rpt` yet; workbook-to-SKM field mappings must be verified before producing engineering data.

## Run tests

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
```
