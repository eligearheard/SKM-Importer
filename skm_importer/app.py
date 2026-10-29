import queue
import os
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from typing import Callable
from tkinter import filedialog, messagebox, ttk

from .pipeline import generate_import_report
from .preferences import load_update_interval, save_update_interval
from .updater import UpdateInfo, check_for_update, download_update, install_update
from .version import __version__


class ImporterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SKM Importer")
        self.root.geometry("940x700")
        self.root.minsize(800, 600)
        self.root.configure(bg="#f1f3f2")

        self.workbook_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.update_interval_minutes = load_update_interval()
        self.update_interval = tk.StringVar(value=str(self.update_interval_minutes))
        self._update_checking = False
        self._update_downloading = False
        self._update_timer_id: str | None = None
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._build_ui()
        self.root.after(100, self._drain_events)
        self._schedule_update_check(delay_ms=600)

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#f1f3f2")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f1f3f2", foreground="#202b2a", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 21), foreground="#162725")
        style.configure("Muted.TLabel", foreground="#667572", font=("Segoe UI", 9))
        style.configure("PanelTitle.TLabel", background="#ffffff", font=("Segoe UI Semibold", 11))
        style.configure("TButton", font=("Segoe UI Semibold", 10), padding=(12, 8))
        style.configure("Accent.TButton", background="#c95b2a", foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#ad4820"), ("disabled", "#b8c0bd")])
        style.configure("Horizontal.TProgressbar", background="#c95b2a", troughcolor="#dfe5e2", thickness=8)
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 9), background="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9))

        page = ttk.Frame(self.root, padding=(28, 22))
        page.pack(fill="both", expand=True)
        ttk.Label(page, text="SKM Importer", style="Title.TLabel").pack(anchor="w")
        ttk.Label(page, text=f"Workbook to SKM report · Version {__version__}", style="Muted.TLabel").pack(anchor="w", pady=(2, 18))

        inputs = ttk.Frame(page, style="Panel.TFrame", padding=18)
        inputs.pack(fill="x")
        self._file_row(inputs, 0, "Spreadsheet", self.workbook_path, self._choose_workbook)
        self._file_row(inputs, 1, "Output SKM report", self.output_path, self._choose_output)

        actions = ttk.Frame(page)
        actions.pack(fill="x", pady=(14, 12))
        self.analyze_button = ttk.Button(actions, text="Generate SKM report", style="Accent.TButton", command=self._start_generation)
        self.analyze_button.pack(side="left")
        self.update_button = ttk.Button(actions, text="Check for updates", command=self._start_update_check)
        self.update_button.pack(side="right")
        interval_controls = ttk.Frame(actions)
        interval_controls.pack(side="right", padx=(0, 10))
        ttk.Label(interval_controls, text="Auto-check every", style="Muted.TLabel").pack(side="left")
        ttk.Spinbox(
            interval_controls,
            from_=1,
            to=1440,
            width=5,
            textvariable=self.update_interval,
        ).pack(side="left", padx=5)
        ttk.Label(interval_controls, text="min", style="Muted.TLabel").pack(side="left")
        ttk.Button(interval_controls, text="Save", command=self._apply_update_interval).pack(side="left", padx=(6, 0))
        ttk.Label(actions, textvariable=self.status, style="Muted.TLabel").pack(side="left", padx=(14, 0))

        progress_panel = ttk.Frame(page, style="Panel.TFrame", padding=(18, 14))
        progress_panel.pack(fill="x")
        ttk.Label(progress_panel, text="PROGRESS", style="PanelTitle.TLabel").pack(anchor="w")
        self.progress = ttk.Progressbar(progress_panel, maximum=100, mode="determinate")
        self.progress.pack(fill="x", pady=(10, 4))

        results_panel = ttk.Frame(page, style="Panel.TFrame", padding=18)
        results_panel.pack(fill="both", expand=True, pady=(12, 0))
        ttk.Label(results_panel, text="INSPECTION RESULTS", style="PanelTitle.TLabel").pack(anchor="w", pady=(0, 10))
        columns = ("kind", "name", "rows", "details")
        self.results = ttk.Treeview(results_panel, columns=columns, show="headings", height=11)
        self.results.heading("kind", text="TYPE")
        self.results.heading("name", text="SHEET / SECTION")
        self.results.heading("rows", text="ROWS")
        self.results.heading("details", text="FORMULAS / FIELDS / ISSUES")
        self.results.column("kind", width=100, stretch=False)
        self.results.column("name", width=230)
        self.results.column("rows", width=80, anchor="e", stretch=False)
        self.results.column("details", width=390)
        results_scroll = ttk.Scrollbar(results_panel, orient="vertical", command=self.results.yview)
        self.results.configure(yscrollcommand=results_scroll.set)
        self.results.pack(side="left", fill="both", expand=True)
        results_scroll.pack(side="right", fill="y")
        self.results.tag_configure("warning", foreground="#a33c23")

        footer = ttk.Label(
            page,
            text="Only values present in the workbook are exported. Missing or unsupported data appears as a validation warning.",
            style="Muted.TLabel",
            wraplength=860,
        )
        footer.pack(anchor="w", pady=(10, 0))

    def _apply_update_interval(self) -> None:
        try:
            interval = int(self.update_interval.get())
            save_update_interval(interval)
        except ValueError as error:
            messagebox.showwarning("Invalid update interval", str(error) or "Enter a whole number of minutes.")
            self.update_interval.set(str(self.update_interval_minutes))
            return
        except OSError as error:
            messagebox.showerror("Could not save setting", str(error))
            return

        self.update_interval_minutes = interval
        self.update_interval.set(str(interval))
        self._schedule_update_check()
        self.status.set(f"Update check interval set to {interval} minutes")

    def _schedule_update_check(self, delay_ms: int | None = None) -> None:
        if self._update_timer_id is not None:
            self.root.after_cancel(self._update_timer_id)
        delay = delay_ms if delay_ms is not None else self.update_interval_minutes * 60 * 1000
        self._update_timer_id = self.root.after(delay, self._run_scheduled_update_check)

    def _run_scheduled_update_check(self) -> None:
        self._update_timer_id = None
        self._start_update_check(silent=True)
        self._schedule_update_check()

    def _file_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command: Callable[[], None],
    ) -> None:
        ttk.Label(parent, text=label, style="PanelTitle.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 14), pady=7)
        field = ttk.Entry(parent, textvariable=variable)
        field.grid(row=row, column=1, sticky="ew", pady=7)
        ttk.Button(parent, text="Browse...", command=command).grid(row=row, column=2, padx=(10, 0), pady=7)
        parent.columnconfigure(1, weight=1)

    def _choose_workbook(self) -> None:
        path = filedialog.askopenfilename(
            title="Select spreadsheet",
            filetypes=[("Excel workbooks", "*.xlsx *.xlsm"), ("All files", "*.*")],
        )
        if path:
            self.workbook_path.set(path)

    def _choose_output(self) -> None:
        workbook_path = self.workbook_path.get().strip()
        initial_name = f"{Path(workbook_path).stem}-SKM-Import.rpt" if workbook_path else "SKM-Import.rpt"
        path = filedialog.asksaveasfilename(
            title="Save SKM import report",
            defaultextension=".rpt",
            initialfile=initial_name,
            filetypes=[("SKM RPT files (*.rpt)", "*.rpt"), ("All files", "*.*")],
        )
        if path:
            self.output_path.set(path)

    def _start_generation(self) -> None:
        workbook_path = self.workbook_path.get().strip()
        output_path = self.output_path.get().strip()
        if not workbook_path or not output_path:
            messagebox.showwarning("Select files", "Choose a spreadsheet and an output SKM report path first.")
            return

        self._clear_results()
        self.progress.configure(value=0)
        self.status.set("Inspecting...")
        self.analyze_button.configure(state="disabled")
        worker = threading.Thread(
            target=self._generate_worker,
            args=(workbook_path, output_path),
            daemon=True,
        )
        worker.start()

    def _generate_worker(self, workbook_path: str, output_path: str) -> None:
        try:
            workbook, report = generate_import_report(
                workbook_path,
                output_path,
                progress=lambda percent, message: self.events.put(("progress", (percent, message))),
            )
            self.events.put(("result", (workbook, report)))
        except Exception as error:
            self.events.put(("error", str(error)))

    def _start_update_check(self, silent: bool = False) -> None:
        if self._update_checking or self._update_downloading:
            return
        self._update_checking = True
        self.update_button.configure(state="disabled")
        if not silent:
            self.status.set("Checking for updates...")
        threading.Thread(target=self._update_worker, args=(silent,), daemon=True).start()

    def _update_worker(self, silent: bool) -> None:
        try:
            update = check_for_update(__version__)
            self.events.put(("update_check", (update, silent)))
        except Exception as error:
            self.events.put(("update_error", (str(error), silent)))

    def _offer_update(self, update: UpdateInfo) -> None:
        if not getattr(sys, "frozen", False):
            if messagebox.askyesno(
                "Update available",
                f"SKM Importer {update.version} is available. Open its download in your browser?",
            ):
                webbrowser.open(update.download_url)
            return
        if not messagebox.askyesno(
            "Update available",
            f"SKM Importer {update.version} is available. Install it now? The app will close and reopen after updating.",
        ):
            self.status.set("Update skipped")
            return
        self.update_button.configure(state="disabled")
        self._update_downloading = True
        self.status.set("Downloading update...")
        threading.Thread(target=self._download_update_worker, args=(update,), daemon=True).start()

    def _download_update_worker(self, update: UpdateInfo) -> None:
        try:
            downloaded = download_update(update)
            self.events.put(("update_downloaded", (downloaded, update.version)))
        except Exception as error:
            self.events.put(("update_error", (str(error), False)))

    def _drain_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "progress":
                    percent, message = payload
                    self.progress.configure(value=percent)
                    self.status.set(message)
                elif event == "result":
                    self._show_result(*payload)
                    self.status.set("Report generation complete")
                    self.analyze_button.configure(state="normal")
                elif event == "error":
                    self.status.set("Inspection failed")
                    self.analyze_button.configure(state="normal")
                    messagebox.showerror("Could not inspect files", payload)
                elif event == "update_check":
                    update, silent = payload
                    self._update_checking = False
                    self.update_button.configure(state="normal")
                    if update:
                        self._offer_update(update)
                    elif not silent:
                        self.status.set("You're up to date")
                        messagebox.showinfo("No updates available", "You're running the latest version of SKM Importer.")
                elif event == "update_downloaded":
                    downloaded_path, version = payload
                    try:
                        install_update(downloaded_path, version)
                    except Exception as error:
                        self.status.set("Update could not be installed")
                        messagebox.showerror("Could not install update", str(error))
                    else:
                        self.root.destroy()
                elif event == "update_error":
                    error, silent = payload
                    self._update_downloading = False
                    self.update_button.configure(state="normal")
                    self.status.set("Update check failed" if not silent else "Ready")
                    if not silent:
                        messagebox.showerror("Update unavailable", error)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)

    def _show_result(self, workbook: object, report: object) -> None:
        for sheet in workbook.sheets:
            details = f"{sheet.formula_count} formulas; {len(sheet.errors)} formula errors"
            tags = ("warning",) if sheet.errors else ()
            self.results.insert("", "end", values=("Workbook", sheet.name, sheet.populated_rows, details), tags=tags)
        for section in report.sections:
            details = f"{len(section.fields)} fields; {section.component_type or 'type code not detected'}"
            tags = ("warning",) if section.malformed_rows else ()
            self.results.insert("", "end", values=("SKM section", section.name, section.record_count, details), tags=tags)
        for error in (*workbook.errors, *report.errors):
            self.results.insert("", "end", values=("Issue", "Validation", "", error), tags=("warning",))
        log_path = Path(report.path).with_suffix(".log")
        self.results.insert("", "end", values=("Log", "Generator log", "", str(log_path)))

    def _clear_results(self) -> None:
        for item in self.results.get_children():
            self.results.delete(item)


def main() -> None:
    root = tk.Tk()
    ImporterApp(root)
    ready_path = os.environ.pop("SKM_IMPORTER_UPDATE_READY_FILE", "")
    if ready_path:
        Path(ready_path).write_text("ready\n", encoding="ascii")
    root.mainloop()