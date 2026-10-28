import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .pipeline import inspect_inputs


class ImporterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SKM Importer")
        self.root.geometry("940x700")
        self.root.minsize(800, 600)
        self.root.configure(bg="#f1f3f2")

        self.workbook_path = tk.StringVar()
        self.report_path = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._build_ui()
        self.root.after(100, self._drain_events)

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#f1f3f2")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f1f3f2", foreground="#202b2a", font=("Segoe UI", 10))
        from typing import Callable
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
        ttk.Label(page, text="Workbook and SKM report inspection", style="Muted.TLabel").pack(anchor="w", pady=(2, 18))

        inputs = ttk.Frame(page, style="Panel.TFrame", padding=18)
        inputs.pack(fill="x")
        self._file_row(inputs, 0, "Spreadsheet", self.workbook_path, self._choose_workbook)
        self._file_row(inputs, 1, "SKM reference report", self.report_path, self._choose_report)

        actions = ttk.Frame(page)
        actions.pack(fill="x", pady=(14, 12))
        self.analyze_button = ttk.Button(actions, text="Inspect files", style="Accent.TButton", command=self._start_inspection)
        self.analyze_button.pack(side="left")
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
            text="No report is generated during inspection. Export mappings are the next step after source fields are verified.",
            style="Muted.TLabel",
            wraplength=860,
        )
        footer.pack(anchor="w", pady=(10, 0))

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
            filetypes=[("Excel workbooks", "*.xlsx *.xlsm *.xls"), ("All files", "*.*")],
        )
        if path:
            self.workbook_path.set(path)

    def _choose_report(self) -> None:
        path = filedialog.askopenfilename(
            title="Select an SKM reference report",
            filetypes=[("SKM reports", "*.rpt"), ("All files", "*.*")],
        )
        if path:
            self.report_path.set(path)

    def _start_inspection(self) -> None:
        workbook_path = self.workbook_path.get().strip()
        report_path = self.report_path.get().strip()
        if not workbook_path or not report_path:
            messagebox.showwarning("Select input files", "Choose a spreadsheet and an SKM reference report first.")
            return

        self._clear_results()
        self.progress.configure(value=0)
        self.status.set("Inspecting...")
        self.analyze_button.configure(state="disabled")
        worker = threading.Thread(
            target=self._inspect_worker,
            args=(workbook_path, report_path),
            daemon=True,
        )
        worker.start()

    def _inspect_worker(self, workbook_path: str, report_path: str) -> None:
        try:
            workbook, report = inspect_inputs(
                workbook_path,
                report_path,
                progress=lambda percent, message: self.events.put(("progress", (percent, message))),
            )
            self.events.put(("result", (workbook, report)))
        except Exception as error:
            self.events.put(("error", str(error)))

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
                    self.status.set("Inspection complete")
                    self.analyze_button.configure(state="normal")
                elif event == "error":
                    self.status.set("Inspection failed")
                    self.analyze_button.configure(state="normal")
                    messagebox.showerror("Could not inspect files", payload)
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

    def _clear_results(self) -> None:
        for item in self.results.get_children():
            self.results.delete(item)


def main() -> None:
    root = tk.Tk()
    ImporterApp(root)
    root.mainloop()