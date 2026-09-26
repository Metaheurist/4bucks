"""Save 4Bucks - Flet (Flutter) UI for GTA IV CE save money editing."""

from __future__ import annotations

import sys
from pathlib import Path

import flet as ft

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


def _resource_path(*parts: str) -> Path:
    """Resolve assets for source runs and PyInstaller onefile."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    return base.joinpath(*parts)


class Save4BucksApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._settings = load_settings()
        self.profiles: list[Path] = []
        self.slots: list[SaveSlot] = []
        self._selected_index: int | None = None

        page.title = f"{APP_NAME} v{__version__}"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = BG
        page.padding = 16
        page.window.width = 720
        page.window.height = 560
        page.window.min_width = 600
        page.window.min_height = 480

        icon = _resource_path("assets", "icon.png")
        if icon.is_file():
            page.window.icon = str(icon)

        self.profile_dd = ft.Dropdown(
            label="Profile",
            expand=True,
            options=[],
            on_select=lambda _e: self.load_slots(),
            border_color=GREEN_HI,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG, size=13),
        )
        self.version_chip = ft.Text("", color=GREEN_HI, weight=ft.FontWeight.BOLD, size=13)
        self.amount_field = ft.TextField(
            label="Amount",
            value="500000",
            width=160,
            border_color=GREEN_HI,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
        )
        self.autobackup = ft.Checkbox(
            label="Autobackup (beside save as .backup + copy under app backups/)",
            value=bool(self._settings.get("autobackup", True)),
            active_color=GOLD,
            on_change=lambda _e: self._persist_settings(),
            label_style=ft.TextStyle(color=FG, size=13),
        )
        self.also_autosave = ft.Checkbox(
            label="Also apply to autosave (SGTA412) when editing a manual slot",
            value=bool(self._settings.get("also_autosave", True)),
            active_color=GOLD,
            on_change=lambda _e: self._persist_settings(),
            label_style=ft.TextStyle(color=FG, size=13),
        )
        self.status = ft.Text("", color=MUTED, size=12)
        self.slots_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Slot", color=GOLD)),
                ft.DataColumn(ft.Text("File", color=GOLD)),
                ft.DataColumn(ft.Text("Money", color=GOLD)),
                ft.DataColumn(ft.Text("Modified", color=GOLD)),
            ],
            rows=[],
            border=ft.border.all(1, GREEN),
            border_radius=6,
            heading_row_color=GREEN,
            data_row_min_height=36,
            data_row_max_height=40,
            column_spacing=20,
            expand=True,
        )

        page.add(
            ft.Column(
                [
                    ft.Text(APP_NAME, size=22, weight=ft.FontWeight.BOLD, color=GOLD),
                    ft.Text(
                        "Offline save editor · GTA IV Complete Edition · $4 Liberty bills (not live memory)",
                        color=MUTED,
                        size=12,
                    ),
                    ft.Row(
                        [
                            self.profile_dd,
                            ft.FilledButton(
                                "Refresh",
                                bgcolor=GREEN_HI,
                                color=GOLD,
                                on_click=lambda _e: self.refresh(),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.version_chip,
                    ft.Container(
                        content=ft.Column([self.slots_table], scroll=ft.ScrollMode.AUTO, expand=True),
                        bgcolor=PANEL,
                        border_radius=6,
                        padding=8,
                        expand=True,
                    ),
                    ft.Row(
                        [
                            self.amount_field,
                            ft.FilledButton(
                                "Set money",
                                bgcolor=GREEN_HI,
                                color=GOLD,
                                on_click=lambda _e: self.on_set(),
                            ),
                            ft.FilledButton(
                                "Add money",
                                bgcolor=GREEN,
                                color=GOLD,
                                on_click=lambda _e: self.on_add(),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.autobackup,
                    self.also_autosave,
                    self.status,
                ],
                expand=True,
                spacing=8,
            )
        )
        self.refresh()

    def _persist_settings(self) -> None:
        self._settings["autobackup"] = bool(self.autobackup.value)
        self._settings["also_autosave"] = bool(self.also_autosave.value)
        try:
            save_settings(self._settings)
        except OSError:
            pass

    def set_status(self, text: str) -> None:
        self.status.value = text
        self.page.update()

    def _alert(self, title: str, message: str, *, error: bool = False) -> None:
        def close(_e: ft.ControlEvent | None = None) -> None:
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(title, color=GOLD if not error else "#e07070"),
                content=ft.Text(message, color=FG),
                bgcolor=PANEL,
                actions=[ft.TextButton("OK", on_click=close, style=ft.ButtonStyle(color=GOLD))],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _confirm(self, title: str, message: str, on_yes) -> None:
        def cancel(_e: ft.ControlEvent) -> None:
            self.page.pop_dialog()

        def accept(_e: ft.ControlEvent) -> None:
            self.page.pop_dialog()
            on_yes()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(title, color=GOLD),
                content=ft.Text(message, color=FG),
                bgcolor=PANEL,
                actions=[
                    ft.TextButton("Cancel", on_click=cancel, style=ft.ButtonStyle(color=MUTED)),
                    ft.TextButton("Continue", on_click=accept, style=ft.ButtonStyle(color=GOLD)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def update_version_chip(self) -> None:
        if self._selected_index is None or self._selected_index >= len(self.slots):
            self.version_chip.value = ""
            self.page.update()
            return
        slot = self.slots[self._selected_index]
        try:
            ident = inspect_save(slot.path)
            check = check_write(slot.path, allow_non_ce_path=False)
            if not check.allowed and "Non-CE" in check.reason:
                soft = check_write(slot.path, allow_non_ce_path=True)
                text = status_chip(ident, soft if soft.allowed else check)
                if soft.allowed:
                    text += " (path warning)"
            else:
                text = status_chip(ident, check)
            if ident.mission_title:
                text += f" · {ident.mission_title[:40]}"
            self.version_chip.value = text
        except Exception as e:
            self.version_chip.value = f"Cannot inspect save: {e}"
        self.page.update()

    def _on_row_select(self, index: int) -> None:
        self._selected_index = index
        for i, row in enumerate(self.slots_table.rows):
            row.selected = i == index
        self.update_version_chip()

    def refresh(self) -> None:
        self.profiles = find_profile_dirs()
        labels = [str(p) for p in self.profiles]
        self.profile_dd.options = [ft.DropdownOption(key=lab, text=lab) for lab in labels]
        if labels:
            current = self.profile_dd.value
            if current not in labels:
                self.profile_dd.value = labels[0]
            self.load_slots()
            self.set_status(
                f"Found {len(self.profiles)} profile(s). Save editor only - close GTAIV.exe before writing."
            )
        else:
            self.profile_dd.value = None
            self.slots = []
            self._selected_index = None
            self.slots_table.rows = []
            self.version_chip.value = ""
            self.set_status("No GTA IV Profiles with SGTA saves found under Documents.")
            self.page.update()

    def load_slots(self) -> None:
        self.slots = []
        self._selected_index = None
        path_str = self.profile_dd.value
        if not path_str:
            self.slots_table.rows = []
            self.page.update()
            return
        profile = Path(path_str)
        self.slots = list_slots(profile)
        rows: list[ft.DataRow] = []
        for i, s in enumerate(self.slots):
            money_txt = f"${s.money:,}" if s.money is not None else (s.error or "error")

            def tap(index: int):
                return lambda _e: self._on_row_select(index)

            rows.append(
                ft.DataRow(
                    selected=(self._selected_index == i),
                    cells=[
                        ft.DataCell(ft.Text(s.label, color=FG), on_tap=tap(i)),
                        ft.DataCell(ft.Text(s.slot_name, color=FG), on_tap=tap(i)),
                        ft.DataCell(ft.Text(money_txt, color=FG), on_tap=tap(i)),
                        ft.DataCell(
                            ft.Text(s.modified.strftime("%Y-%m-%d %H:%M"), color=MUTED),
                            on_tap=tap(i),
                        ),
                    ],
                )
            )
        self.slots_table.rows = rows
        if self.slots:
            prefer = next((i for i, s in enumerate(self.slots) if s.slot_name == "SGTA412"), 0)
            if self._selected_index is None:
                self._selected_index = prefer
            # refresh selected flags
            for i, row in enumerate(self.slots_table.rows):
                row.selected = i == self._selected_index
            self.update_version_chip()
        else:
            self.version_chip.value = ""
            self.page.update()

    def selected_slot(self) -> SaveSlot | None:
        if self._selected_index is None or self._selected_index >= len(self.slots):
            self._alert(APP_NAME, "Select a save slot first.")
            return None
        return self.slots[self._selected_index]

    def parse_amount(self) -> int | None:
        raw = (self.amount_field.value or "").strip().replace(",", "").replace("$", "")
        try:
            amount = int(raw)
        except ValueError:
            self._alert(APP_NAME, "Enter a whole-number amount.", error=True)
            return None
        if amount < 0:
            self._alert(APP_NAME, "Amount cannot be negative.", error=True)
            return None
        return amount

    def targets_for(self, slot: SaveSlot) -> list[Path]:
        paths = [slot.path]
        if (
            bool(self.also_autosave.value)
            and slot.slot_name != "SGTA412"
            and slot.path.parent.joinpath("SGTA412").is_file()
        ):
            paths.append(slot.path.parent / "SGTA412")
        return paths

    def on_set(self) -> None:
        self._start_apply("set")

    def on_add(self) -> None:
        self._start_apply("add")

    def _start_apply(self, mode: str) -> None:
        slot = self.selected_slot()
        amount = self.parse_amount()
        if slot is None or amount is None:
            return
        if slot.error:
            self._alert(APP_NAME, f"Cannot edit this save:\n{slot.error}", error=True)
            return
        if is_gtaiv_running():
            self._alert(
                APP_NAME,
                "GTAIV.exe is running.\n\nClose the game completely before editing saves, "
                "or your changes may be overwritten.",
                error=True,
            )
            return

        if amount > 999_999_999:
            self._confirm(
                APP_NAME,
                f"${amount:,} is above the usual UI clamp (999,999,999).\nContinue anyway?",
                on_yes=lambda: self._confirm_paths(mode, slot, amount),
            )
            return
        self._confirm_paths(mode, slot, amount)

    def _confirm_paths(self, mode: str, slot: SaveSlot, amount: int) -> None:
        paths = self.targets_for(slot)
        self._confirm_path_at(mode, slot, amount, paths, 0)

    def _confirm_path_at(
        self, mode: str, slot: SaveSlot, amount: int, paths: list[Path], index: int
    ) -> None:
        if index >= len(paths):
            self._do_write(mode, paths, amount)
            return
        path = paths[index]
        check = check_write(path, allow_non_ce_path=False)
        if check.allowed:
            if check.warnings:
                self._confirm(
                    APP_NAME,
                    "Warnings:\n- " + "\n- ".join(check.warnings) + "\n\nContinue?",
                    on_yes=lambda: self._confirm_path_at(mode, slot, amount, paths, index + 1),
                )
                return
            self._confirm_path_at(mode, slot, amount, paths, index + 1)
            return
        if "Non-CE" in check.reason:
            self._confirm(
                APP_NAME,
                check.reason + "\n\nForce write anyway?",
                on_yes=lambda: self._confirm_path_at(mode, slot, amount, paths, index + 1),
            )
            return
        self._alert(APP_NAME, f"Write blocked:\n{check.reason}", error=True)

    def _do_write(self, mode: str, paths: list[Path], amount: int) -> None:
        try:
            lines: list[str] = []
            backup_lines: list[str] = []
            for path in paths:
                allow_non_ce = "Non-CE" in check_write(path, allow_non_ce_path=False).reason
                if mode == "set":
                    old, new, bak, _check = set_money(
                        path,
                        amount,
                        backup=bool(self.autobackup.value),
                        allow_non_ce_path=allow_non_ce,
                    )
                else:
                    old, new, bak, _check = add_money(
                        path,
                        amount,
                        backup=bool(self.autobackup.value),
                        allow_non_ce_path=allow_non_ce,
                    )
                lines.append(f"{path.name}: ${old:,} -> ${new:,}")
                if bak:
                    backup_lines.append(f"{path.name}:\n  {bak.beside}\n  {bak.app_copy}")
            self.load_slots()
            self.set_status(" | ".join(lines))
            msg = "Money updated.\n\n" + "\n".join(lines)
            if backup_lines:
                msg += "\n\nBacked up ->\n" + "\n".join(backup_lines)
            self._alert(APP_NAME, msg)
        except Exception as e:
            self._alert(APP_NAME, str(e), error=True)


def main(page: ft.Page) -> None:
    Save4BucksApp(page)


def run() -> None:
    assets = str(_resource_path("assets").parent / "assets")
    ft.run(main, assets_dir=assets if Path(assets).is_dir() else None)


if __name__ == "__main__":
    run()
