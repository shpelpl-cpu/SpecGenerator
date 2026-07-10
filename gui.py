from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import traceback

from exporter import Exporter
from grouper import InvoiceGrouper
from history import GenerationHistory
from mapper import DescriptionMapper
from parser import InvoiceParser
from validator import InvoiceValidator


class MappingCancelled(Exception):
    """Raised when the user cancels adding a missing description."""


class SpecGeneratorApp:

    def __init__(
        self,
        root: tk.Tk,
        dnd_files=None,
    ):

        self.root = root
        self.dnd_files = dnd_files
        self.base_dir = Path(__file__).resolve().parent
        self.config_path = self.base_dir / "config.json"
        self.history = GenerationHistory(
            self.base_dir / "history" / "history.json"
        )
        self.controls = []

        self.invoice_path = tk.StringVar(
            value=str(self.base_dir / "invoice.xlsx")
        )
        self.template_path = tk.StringVar(
            value=str(self.base_dir / "templates" / "spec_template.xlsx")
        )
        self.output_dir = tk.StringVar(
            value=str(self.base_dir / "output")
        )
        self.remember_paths = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Gotowy")

        self._configure_window()
        self._load_config()
        self._build_ui()
        self._center_window()
        self._configure_drag_and_drop()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_window(self):

        self.root.title("SpecGenerator")
        self.root.geometry("700x300")
        self.root.resizable(False, False)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self._set_window_icon()

    def _set_window_icon(self):

        self.icon_image = tk.PhotoImage(width=16, height=16)
        self.icon_image.put("#1f6aa5", to=(0, 0, 16, 16))
        self.icon_image.put("#ffffff", to=(4, 3, 12, 13))
        self.icon_image.put("#1f6aa5", to=(6, 5, 10, 11))
        self.root.iconphoto(True, self.icon_image)

    def _center_window(self):

        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):

        frame = ttk.Frame(self.root, padding=15)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        self._add_path_field(
            frame,
            row=0,
            label="Faktura:",
            variable=self.invoice_path,
            command=self._browse_invoice,
        )
        self._add_path_field(
            frame,
            row=1,
            label="Szablon:",
            variable=self.template_path,
            command=self._browse_template,
        )
        self._add_path_field(
            frame,
            row=2,
            label="Folder wyjściowy:",
            variable=self.output_dir,
            command=self._browse_output_dir,
        )

        remember_checkbox = ttk.Checkbutton(
            frame,
            text="Zapamiętaj ostatnie ścieżki",
            variable=self.remember_paths,
        )
        remember_checkbox.grid(
            row=3,
            column=1,
            sticky="w",
            pady=(8, 16),
        )
        self.controls.append(remember_checkbox)

        generate_button = ttk.Button(
            frame,
            text="GENERUJ",
            width=20,
            command=self._generate,
        )
        generate_button.grid(
            row=4,
            column=0,
            columnspan=2,
            pady=(0, 8),
        )
        self.controls.append(generate_button)

        history_button = ttk.Button(
            frame,
            text="Historia",
            command=self._show_history,
        )
        history_button.grid(row=4, column=2, pady=(0, 8))
        self.controls.append(history_button)

        self.progress = ttk.Progressbar(
            self.root,
            mode="indeterminate",
        )
        self.progress.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 6))

        ttk.Separator(self.root, orient="horizontal").grid(
            row=2,
            column=0,
            sticky="ew",
        )
        ttk.Label(
            self.root,
            textvariable=self.status,
            anchor="w",
            padding=(15, 6),
        ).grid(row=3, column=0, sticky="ew")

    def _add_path_field(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command,
    ):

        ttk.Label(parent, text=label).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=6)
        button = ttk.Button(parent, text="Przeglądaj", command=command)
        button.grid(
            row=row,
            column=2,
            padx=(10, 0),
            pady=6,
        )

        self.controls.extend((entry, button))

    def _configure_drag_and_drop(self):

        if self.dnd_files is None:
            return

        self.root.drop_target_register(self.dnd_files)
        self.root.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event):

        try:
            paths = self.root.tk.splitlist(event.data)

            for value in paths:
                path = Path(value)

                if path.suffix.lower() in {".xlsx", ".xls"}:
                    self.invoice_path.set(str(path))
                    return

            raise ValueError("Upuść plik Excel (.xlsx lub .xls).")

        except Exception:
            self._show_traceback()

    def _load_config(self):

        if not self.config_path.exists():
            return

        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            self.invoice_path.set(data.get("invoice_path", self.invoice_path.get()))
            self.template_path.set(
                data.get("template_path", self.template_path.get())
            )
            self.output_dir.set(data.get("output_dir", self.output_dir.get()))
            self.remember_paths.set(data.get("remember_paths", True))

        except Exception:
            self._show_traceback("Błąd konfiguracji")

    def _save_config(self):

        data = {
            "invoice_path": self.invoice_path.get(),
            "template_path": self.template_path.get(),
            "output_dir": self.output_dir.get(),
            "remember_paths": self.remember_paths.get(),
        }

        with self.config_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def _browse_invoice(self):

        path = filedialog.askopenfilename(
            parent=self.root,
            title="Wybierz fakturę",
            initialdir=self._initial_directory(self.invoice_path.get()),
            filetypes=[("Pliki Excel", "*.xlsx *.xls")],
        )

        if path:
            self.invoice_path.set(path)

    def _browse_template(self):

        path = filedialog.askopenfilename(
            parent=self.root,
            title="Wybierz szablon",
            initialdir=self._initial_directory(self.template_path.get()),
            filetypes=[("Pliki Excel", "*.xlsx")],
        )

        if path:
            self.template_path.set(path)

    def _browse_output_dir(self):

        path = filedialog.askdirectory(
            parent=self.root,
            title="Wybierz folder wyjściowy",
            initialdir=self._initial_directory(self.output_dir.get()),
        )

        if path:
            self.output_dir.set(path)

    def _initial_directory(self, value: str) -> str:

        path = Path(value)

        if path.is_dir():
            return str(path)

        if path.parent.is_dir():
            return str(path.parent)

        return str(self.base_dir)

    def _set_busy(self, is_busy: bool):

        for control in self.controls:
            control.state(["disabled"] if is_busy else ["!disabled"])

        if is_busy:
            self.progress.start(10)
        else:
            self.progress.stop()

        self.root.update_idletasks()

    def _generate(self):

        self.status.set("Przetwarzanie...")
        self._set_busy(True)

        try:
            invoice_path = Path(self.invoice_path.get()).expanduser()
            template_path = Path(self.template_path.get()).expanduser()
            output_dir_text = self.output_dir.get().strip()

            if not invoice_path.is_file():
                raise FileNotFoundError(f"Nie znaleziono faktury: {invoice_path}")

            if not template_path.is_file():
                raise FileNotFoundError(
                    f"Nie znaleziono szablonu: {template_path}"
                )

            if not output_dir_text:
                raise ValueError("Wybierz folder wyjściowy.")

            output_dir = Path(output_dir_text).expanduser()
            invoice = InvoiceParser(invoice_path).parse()
            mapper = DescriptionMapper(self.base_dir / "mappings.json")
            for item in invoice.items:
                try:
                    item.description_pl = mapper.map(item.description_original)
                except ValueError:
                    translated = self._ask_for_mapping(item.description_original)
                    if translated is None:
                        raise MappingCancelled

                    mapper.learn(item.description_original, translated)
                    item.description_pl = mapper.map(item.description_original)

            groups = InvoiceGrouper().group(invoice)
            result = InvoiceValidator().validate(invoice, groups)

            if not result.success:
                raise ValueError("\n".join(result.errors))

            output_path = output_dir / "specyfikacja_wypelniona.xlsx"
            Exporter(template_path).export(groups, output_path)
            self.history.add(
                invoice=invoice_path.name,
                output=str(output_path.resolve()),
                positions=len(invoice.items),
                groups=len(groups),
                value=float(invoice.total_value),
            )

            if self.remember_paths.get():
                self._save_config()

        except MappingCancelled:
            self.status.set("Anulowano")
            self._set_busy(False)
            return

        except Exception:
            self.status.set("Błąd")
            self._set_busy(False)
            self._show_traceback()
            return

        self.status.set("Gotowe")
        self._set_busy(False)
        messagebox.showinfo(
            "Gotowe",
            f"Wygenerowano plik:\n{output_path}",
            parent=self.root,
        )

    def _ask_for_mapping(self, original: str) -> str | None:

        dialog = tk.Toplevel(self.root)
        dialog.title("Nieznany opis")
        dialog.resizable(False, False)
        dialog.transient(self.root)

        result = {"translated": None}
        translated = tk.StringVar()

        frame = ttk.Frame(dialog, padding=16)
        frame.grid(sticky="nsew")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Nieznany opis:").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(frame, text=original, wraplength=360).grid(
            row=1, column=0, sticky="w", pady=(2, 12)
        )
        ttk.Label(frame, text="Polski opis:").grid(
            row=2, column=0, sticky="w"
        )
        entry = ttk.Entry(frame, textvariable=translated, width=45)
        entry.grid(row=3, column=0, sticky="ew", pady=(2, 14))

        def save():
            value = translated.get().strip()
            if not value:
                messagebox.showwarning(
                    "Brak opisu",
                    "Wpisz polski opis.",
                    parent=dialog,
                )
                entry.focus_set()
                return

            result["translated"] = value
            dialog.destroy()

        def cancel():
            dialog.destroy()

        ttk.Button(frame, text="Zapisz", command=save).grid(row=4, column=0)

        dialog.bind("<Return>", lambda event: save())
        dialog.bind("<Escape>", lambda event: cancel())
        dialog.protocol("WM_DELETE_WINDOW", cancel)
        dialog.grab_set()
        entry.focus_set()
        dialog.wait_window()

        return result["translated"]

    def _show_history(self):

        window = tk.Toplevel(self.root)
        window.title("Historia wygenerowanych specyfikacji")
        window.geometry("900x360")
        window.minsize(700, 240)
        window.transient(self.root)

        frame = ttk.Frame(window, padding=12)
        frame.pack(fill="both", expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        columns = ("date", "invoice", "positions", "groups", "value", "output")
        table = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
        )
        headings = {
            "date": "Data",
            "invoice": "Faktura",
            "positions": "Pozycji",
            "groups": "CN",
            "value": "Wartość",
            "output": "Plik",
        }
        widths = {
            "date": 145,
            "invoice": 150,
            "positions": 70,
            "groups": 60,
            "value": 90,
            "output": 330,
        }
        for column in columns:
            table.heading(column, text=headings[column])
            table.column(column, width=widths[column], anchor="w")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        buttons = ttk.Frame(frame)
        buttons.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="e")
        ttk.Button(
            buttons,
            text="Otwórz folder",
            command=lambda: self._open_history_file(table),
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(
            buttons,
            text="Usuń wpis",
            command=lambda: self._delete_history_entry(table),
        ).grid(row=0, column=1)

        self._refresh_history_table(table)
        table.bind("<Double-1>", lambda event: self._open_history_file(table))
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        window.grab_set()
        window.wait_window()

    def _refresh_history_table(self, table: ttk.Treeview):

        table.delete(*table.get_children())
        entries = self.history.load()
        sorted_entries = sorted(
            enumerate(entries),
            key=lambda item: item[1]["date"],
            reverse=True,
        )

        for index, entry in sorted_entries:
            table.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    entry["date"],
                    entry["invoice"],
                    entry["positions"],
                    entry["groups"],
                    f"{entry['value']:.2f}",
                    entry["output"],
                ),
            )

    def _open_history_file(self, table: ttk.Treeview):

        selection = table.selection()
        if not selection:
            return

        output_path = Path(table.item(selection[0], "values")[5])

        if output_path.is_file():
            subprocess.Popen(["explorer.exe", f"/select,{output_path}"])
        else:
            messagebox.showwarning(
                "Brak pliku",
                f"Nie znaleziono pliku:\n{output_path}",
                parent=table.winfo_toplevel(),
            )

    def _delete_history_entry(self, table: ttk.Treeview):

        selection = table.selection()
        if not selection:
            return

        if not messagebox.askyesno(
            "Usuń wpis",
            "Czy na pewno chcesz usunąć wybrany wpis historii?",
            parent=table.winfo_toplevel(),
        ):
            return

        self.history.delete(int(selection[0]))
        self._refresh_history_table(table)

    def _show_traceback(self, title: str = "Błąd"):

        messagebox.showerror(title, traceback.format_exc(), parent=self.root)

    def _on_close(self):

        try:
            if self.remember_paths.get():
                self._save_config()
        except Exception:
            self._show_traceback()
            return

        self.root.destroy()


def run():

    dnd_files = None

    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD

        root = TkinterDnD.Tk()
        dnd_files = DND_FILES
    except ImportError:
        root = tk.Tk()

    SpecGeneratorApp(root, dnd_files=dnd_files)
    root.mainloop()
