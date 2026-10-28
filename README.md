# SKM Importer

Desktop application for converting field-survey Excel workbooks into SKM Power*Tools `.rpt` import reports.

## Easiest: Download the app

Once a Windows release is published, download `SKM-Importer.exe` from [the latest release](https://github.com/eligearheard/SKM-Importer/releases/latest) and double-click it. Python and the IDE are not required.

Windows may display a SmartScreen warning because the app is not code-signed.

The app checks for updates when it opens and every 5 minutes by default. Change the **Auto-check every** value and select **Save** to use a different interval (1 to 1,440 minutes); the setting persists across launches. You can also use **Check for updates** at any time. When an update is available, choose **Yes** to download and install it; the app closes briefly and reopens with the new version. Users with an already-downloaded older executable must download this update-enabled release once; later releases can be installed from within the app.

## Build a Windows download

For maintainers, the easiest way to publish a download is from GitHub: open **Actions → Windows release → Run workflow**, enter a version such as `v0.1.0`, and start the workflow. GitHub stamps that version into the Windows app, builds it, and publishes the release; no local Python setup is needed.

To build locally instead, run `build_windows.bat` on Windows with Python 3.11 or newer. It creates a standalone `dist\SKM-Importer.exe`. Pushing a version tag also publishes a release automatically:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

## Run from source

Run `setup.bat` once, then `run.bat`. This creates a local virtual environment and installs the dependencies.

The app reads `.xlsx` and `.xlsm` field-survey workbooks and generates an SKM `.rpt` using its built-in section and field schema; no reference report is needed. It currently maps feeder/cable, bus, bus duct, utility, and two-winding transformer data. Values not present in the workbook are left blank, and skipped or incomplete records are reported as validation warnings. Review the generated report and warnings before importing it into SKM.

## Run tests

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
```
