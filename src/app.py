"""Save 4Bucks - tkinter UI for GTA IV CE save money editing."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from . import APP_NAME, __version__
from .detect import SaveSlot, find_profile_dirs, is_gtaiv_running, list_slots
from .save_money import add_money, set_money
from .settings import load_settings, save_settings
from .versioning import check_write, inspect_save, status_chip


# Liberty City greys + federal green / $4 gold
BG = "#12161a"
PANEL = "#1a2228"
FG = "#e8ece8"
MUTED = "#8a9490"
GOLD = "#d4af37"
GREEN = "#1e4d3a"
GREEN_HI = "#2d6b52"
ACCENT = "#c4a035"


def _resource_path(*parts: str) -> Path:
    """Resolve assets for source runs and PyInstaller onefile."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    return base.joinpath(*parts)


class Save4BucksApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} v{__version__}")
        self.minsize(600, 480)
        self.geometry("680x520")
        self.configure(bg=BG)

        icon = _resource_path("assets", "icon.ico")
        if icon.is_file():
            try:
                self.iconbitmap(default=str(icon))
            except Exception:
                pass

        self._settings = load_settings()
        self.profiles: list[Path] = []
        self.slots: list[SaveSlot] = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TFrame", background=BG)
        style.configure("TCheckbutton", background=BG, foreground=FG)
        style.configure(
            "Header.TLabel",
            font=("Segoe UI", 16, "bold"),
            foreground=GOLD,
            background=BG,
        )
        style.configure("Sub.TLabel", foreground=MUTED, background=BG, font=("Segoe UI", 9))
        style.configure("Status.TLabel", foreground=MUTED, background=BG)
        style.configure("Chip.TLabel", foreground=GREEN_HI, background=BG, font=("Segoe UI", 9, "bold"))
        style.configure("TButton", padding=4)
        style.configure(
            "Treeview",
            background=PANEL,
            fieldbackground=PANEL,
            foreground=FG,
            rowheight=24,
        )
        style.configure("Treeview.Heading", background=GREEN, foreground=GOLD, relief="flat")
        style.map("Treeview", background=[("selected", GREEN_HI)])

        root = ttk.Frame(self, padding=14)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(root, text=f"{APP_NAME}", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            root,
            text="Offline save editor · GTA IV Complete Edition · $4 Liberty bills (not live memory)",
            style="Sub.TLabel",
        ).pack(anchor=tk.W, pady=(0, 8))

        top = ttk.Frame(root)
        top.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(top, text="Profile:").pack(side=tk.LEFT)
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(top, textvariable=self.profile_var, state="readonly", width=52)
        self.profile_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self.profile_combo.bind("<<ComboboxSelected>>", lambda _e: self.load_slots())
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side=tk.LEFT)

        self.version_chip = ttk.Label(root, text="", style="Chip.TLabel")
        self.version_chip.pack(anchor=tk.W, pady=(0, 4))

        cols = ("label", "file", "money", "modified")
        self.tree = ttk.Treeview(root, columns=cols, show="headings", height=10, selectmode="browse")
        self.tree.heading("label", text="Slot")
        self.tree.heading("file", text="File")
        self.tree.heading("money", text="Money")
        self.tree.heading("modified", text="Modified")
        self.tree.column("label", width=130)
        self.tree.column("file", width=100)
        self.tree.column("money", width=120)
        self.tree.column("modified", width=160)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=6)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self.update_version_chip())

        form = ttk.Frame(root)
        form.pack(fill=tk.X, pady=6)
        ttk.Label(form, text="Amount:").pack(side=tk.LEFT)
        self.amount_var = tk.StringVar(value="500000")
        ttk.Entry(form, textvariable=self.amount_var, width=16).pack(side=tk.LEFT, padx=6)
        ttk.Button(form, text="Set money", command=self.on_set).pack(side=tk.LEFT, padx=2)
        ttk.Button(form, text="Add money", command=self.on_add).pack(side=tk.LEFT, padx=2)

        self.autobackup = tk.BooleanVar(value=bool(self._settings.get("autobackup", True)))
        ttk.Checkbutton(
            root,
            text="Autobackup (beside save as .backup + copy under app backups/)",
            variable=self.autobackup,
            command=self._persist_settings,
        ).pack(anchor=tk.W)

        self.also_autosave = tk.BooleanVar(value=bool(self._settings.get("also_autosave", True)))
        ttk.Checkbutton(
            root,
            text="Also apply to autosave (SGTA412) when editing a manual slot",
            variable=self.also_autosave,
            command=self._persist_settings,
        ).pack(anchor=tk.W)

        self.status = ttk.Label(root, text="", style="Status.TLabel")
        self.status.pack(anchor=tk.W, pady=(8, 0))

    def _persist_settings(self) -> None:
        self._settings["autobackup"] = bool(self.autobackup.get())
        self._settings["also_autosave"] = bool(self.also_autosave.get())
        try:
            save_settings(self._settings)
        except OSError:
            pass

    def set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def update_version_chip(self) -> None:
        slot = None
        sel = self.tree.selection()
        if sel:
            slot = self.slots[int(sel[0])]
        if slot is None:
            self.version_chip.configure(text="")
            return
        try:
            ident = inspect_save(slot.path)
            check = check_write(slot.path, allow_non_ce_path=False)
            # chip shows identity; blocked state if hard fail
            if not check.allowed and "Non-CE" in check.reason:
                soft = check_write(slot.path, allow_non_ce_path=True)
                text = status_chip(ident, soft if soft.allowed else check)
                if soft.allowed:
                    text += " (path warning)"
            else:
                text = status_chip(ident, check)
            if ident.mission_title:
                text += f" · {ident.mission_title[:40]}"
            self.version_chip.configure(text=text)
        except Exception as e:
            self.version_chip.configure(text=f"Cannot inspect save: {e}")

    def refresh(self) -> None:
        self.profiles = find_profile_dirs()
        labels = [str(p) for p in self.profiles]
        self.profile_combo["values"] = labels
        if labels:
            current = self.profile_var.get()
            if current not in labels:
                self.profile_var.set(labels[0])
            self.load_slots()
            self.set_status(f"Found {len(self.profiles)} profile(s). Save editor only - close GTAIV.exe before writing.")
        else:
            self.profile_var.set("")
            self.tree.delete(*self.tree.get_children())
            self.slots = []
            self.version_chip.configure(text="")
            self.set_status("No GTA IV Profiles with SGTA saves found under Documents.")

    def load_slots(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.slots = []
        path_str = self.profile_var.get()
        if not path_str:
            return
        profile = Path(path_str)
        self.slots = list_slots(profile)
        for i, s in enumerate(self.slots):
            money_txt = f"${s.money:,}" if s.money is not None else (s.error or "error")
            self.tree.insert(
                "",
                tk.END,
                iid=str(i),
                values=(s.label, s.slot_name, money_txt, s.modified.strftime("%Y-%m-%d %H:%M")),
            )
        if self.slots:
            prefer = next((i for i, s in enumerate(self.slots) if s.slot_name == "SGTA412"), 0)
            self.tree.selection_set(str(prefer))
            self.tree.focus(str(prefer))
            self.update_version_chip()

    def selected_slot(self) -> SaveSlot | None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(APP_NAME, "Select a save slot first.")
            return None
        return self.slots[int(sel[0])]

    def parse_amount(self) -> int | None:
        raw = self.amount_var.get().strip().replace(",", "").replace("$", "")
        try:
            amount = int(raw)
        except ValueError:
            messagebox.showerror(APP_NAME, "Enter a whole-number amount.")
            return None
        if amount < 0:
            messagebox.showerror(APP_NAME, "Amount cannot be negative.")
            return None
        if amount > 999_999_999:
            if not messagebox.askyesno(
                APP_NAME,
                f"${amount:,} is above the usual UI clamp (999,999,999).\nContinue anyway?",
            ):
                return None
        return amount

    def ensure_game_closed(self) -> bool:
        if is_gtaiv_running():
            messagebox.showerror(
                APP_NAME,
                "GTAIV.exe is running.\n\nClose the game completely before editing saves, "
                "or your changes may be overwritten.",
            )
            return False
        return True

    def confirm_write(self, path: Path) -> bool:
        check = check_write(path, allow_non_ce_path=False)
        if check.allowed:
            if check.warnings:
                return messagebox.askyesno(
                    APP_NAME,
                    "Warnings:\n- " + "\n- ".join(check.warnings) + "\n\nContinue?",
                )
            return True
        if "Non-CE" in check.reason:
            return messagebox.askyesno(
                APP_NAME,
                check.reason + "\n\nForce write anyway?",
            )
        messagebox.showerror(APP_NAME, f"Write blocked:\n{check.reason}")
        return False

    def targets_for(self, slot: SaveSlot) -> list[Path]:
        paths = [slot.path]
        if (
            self.also_autosave.get()
            and slot.slot_name != "SGTA412"
            and slot.path.parent.joinpath("SGTA412").is_file()
        ):
            paths.append(slot.path.parent / "SGTA412")
        return paths

    def _apply(self, mode: str) -> None:
        slot = self.selected_slot()
        amount = self.parse_amount()
        if slot is None or amount is None:
            return
        if slot.error:
            messagebox.showerror(APP_NAME, f"Cannot edit this save:\n{slot.error}")
            return
        if not self.ensure_game_closed():
            return

        paths = self.targets_for(slot)
        for path in paths:
            if not self.confirm_write(path):
                return

        try:
            lines: list[str] = []
            backup_lines: list[str] = []
            for path in paths:
                allow_non_ce = "Non-CE" in check_write(path, allow_non_ce_path=False).reason
                if mode == "set":
                    old, new, bak, _check = set_money(
                        path,
                        amount,
                        backup=bool(self.autobackup.get()),
                        allow_non_ce_path=allow_non_ce,
                    )
                else:
                    old, new, bak, _check = add_money(
                        path,
                        amount,
                        backup=bool(self.autobackup.get()),
                        allow_non_ce_path=allow_non_ce,
                    )
                lines.append(f"{path.name}: ${old:,} → ${new:,}")
                if bak:
                    backup_lines.append(f"{path.name}:\n  {bak.beside}\n  {bak.app_copy}")
            self.load_slots()
            self.set_status(" | ".join(lines))
            msg = "Money updated.\n\n" + "\n".join(lines)
            if backup_lines:
                msg += "\n\nBacked up →\n" + "\n".join(backup_lines)
            messagebox.showinfo(APP_NAME, msg)
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    def on_set(self) -> None:
        self._apply("set")

    def on_add(self) -> None:
        self._apply("add")


def run() -> None:
    app = Save4BucksApp()
    app.mainloop()


if __name__ == "__main__":
    run()
