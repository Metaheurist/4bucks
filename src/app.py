"""Save 4Bucks - multi-view Flet UI for GTA IV CE PlayerInfo editing."""

from __future__ import annotations

import sys
from pathlib import Path

import flet as ft

from . import APP_NAME, __version__
from .detect import SaveSlot, find_profile_dirs, is_gtaiv_running, list_slots
from .playerinfo import WEAPON_SLOT_COUNT
from .save_money import add_money, set_money
from .save_vitality import (
    UI_CLAMP_MAX,
    UI_CLAMP_MIN,
    UI_MAX_CLAMP,
    read_vitality_file,
    set_vitality,
)
from .save_weapons import read_loadout_file, write_loadout
from .settings import load_settings, save_settings
from .versioning import check_write, inspect_save, status_chip
from .weapons_catalog import dropdown_options

# Liberty City greys + federal green / $4 gold
# Contrast: FG/MUTED/GOLD chosen for AA-ish text on BG/PANEL (dark UI)
BG = "#12161a"
PANEL = "#1a2228"
FG = "#f0f4f0"
MUTED = "#b0bbb4"  # brighter than chrome grey for secondary text contrast
GOLD = "#e0c04a"
GREEN = "#245a42"
GREEN_HI = "#3a8f68"
OUTLINE = "#4a7a60"
FOCUS = "#f0d878"
ERROR = "#f08080"
BTN_ON_GREEN = "#12161a"  # text on filled green buttons (was gold-on-green)


def _resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    return base.joinpath(*parts)


def _outlined(content: ft.Control, *, expand: bool = False, padding: int = 12) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=PANEL,
        border=ft.Border.all(1.5, OUTLINE),
        border_radius=4,
        padding=padding,
        expand=expand,
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
    )


class Save4BucksApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._settings = load_settings()
        self.profiles: list[Path] = []
        self.slots: list[SaveSlot] = []
        self._selected_index: int | None = None
        self._view = "menu"
        self._weapon_rows: list[dict] = []

        page.title = f"{APP_NAME} v{__version__}"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = BG
        page.padding = 16
        page.window.width = 780
        page.window.height = 640
        page.window.min_width = 640
        page.window.min_height = 520
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=GOLD,
                on_primary=BG,
                secondary=GREEN_HI,
                on_secondary=BTN_ON_GREEN,
                surface=PANEL,
                on_surface=FG,
                outline=OUTLINE,
                error=ERROR,
                on_error=BG,
            ),
            focus_color=FOCUS,
        )
        page.on_keyboard_event = self._on_keyboard

        icon = _resource_path("assets", "icon.png")
        if icon.is_file():
            page.window.icon = str(icon)

        self.profile_dd = ft.Dropdown(
            label="Profile",
            expand=True,
            options=[],
            on_select=lambda _e: self.load_slots(),
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            focused_border_width=2,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG, size=13),
            tooltip="Select Rockstar Profiles folder",
            autofocus=False,
        )
        self.version_chip = ft.Text(
            "",
            color=GOLD,
            weight=ft.FontWeight.BOLD,
            size=12,
            selectable=True,
        )
        self.status = ft.Text("", color=MUTED, size=13, selectable=True)
        field_kw = dict(
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            focused_border_width=2,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
            cursor_color=FOCUS,
        )
        self.amount_field = ft.TextField(
            label="Amount",
            value="500000",
            width=160,
            tooltip="Cash amount to set or add",
            **field_kw,
        )
        self.health_field = ft.TextField(
            label="Health",
            value="200",
            width=110,
            tooltip="Current health (float)",
            **field_kw,
        )
        self.armour_field = ft.TextField(
            label="Armour",
            value="100",
            width=110,
            tooltip="Current armour (float)",
            **field_kw,
        )
        self.max_health_field = ft.TextField(
            label="Max health",
            value="200",
            width=110,
            tooltip="Max health (uint16, 0-65535)",
            **field_kw,
        )
        self.max_armour_field = ft.TextField(
            label="Max armour",
            value="100",
            width=110,
            tooltip="Max armour (uint16, 0-65535)",
            **field_kw,
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
        self.slots_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Slot", color=GOLD)),
                ft.DataColumn(ft.Text("File", color=GOLD)),
                ft.DataColumn(ft.Text("Money", color=GOLD)),
                ft.DataColumn(ft.Text("Modified", color=GOLD)),
            ],
            rows=[],
            border=ft.Border.all(1, GREEN),
            border_radius=4,
            heading_row_color=GREEN,
            data_row_min_height=36,
            data_row_max_height=40,
            column_spacing=20,
            expand=True,
        )

        self._weapon_catalog_opts = [
            ft.DropdownOption(key=str(wid), text=label) for label, wid in dropdown_options()
        ]
        self._weapon_catalog_opts.append(ft.DropdownOption(key="custom", text="Custom ID (mod)…"))

        self.switcher = ft.AnimatedSwitcher(
            content=self._build_menu(),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=280,
            reverse_duration=200,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
            expand=True,
        )

        page.add(
            ft.Column(
                [
                    ft.Semantics(
                        label=f"{APP_NAME} version {__version__}",
                        heading_level=1,
                        content=ft.Text(
                            APP_NAME, size=24, weight=ft.FontWeight.BOLD, color=GOLD
                        ),
                    ),
                    ft.Text(
                        "Offline PlayerInfo editor · CE money · weapons · vitality · not live memory",
                        color=MUTED,
                        size=13,
                    ),
                    ft.Text(
                        "Keyboard: Tab moves focus · Enter activates · Esc returns to menu",
                        color=MUTED,
                        size=11,
                    ),
                    self.switcher,
                    ft.Semantics(
                        label="Status",
                        live_region=True,
                        content=self.status,
                    ),
                ],
                expand=True,
                spacing=10,
            )
        )
        self.refresh()

    def _on_keyboard(self, e: ft.KeyboardEvent) -> None:
        key = (e.key or "").lower()
        if key in ("escape", "esc") and self._view != "menu":
            self._goto("menu")
            return
        # Digit shortcuts on startup menu
        if self._view == "menu" and not e.ctrl and not e.alt and not e.meta:
            mapping = {"1": "money", "2": "weapons", "3": "vitality", "4": "settings"}
            if key in mapping:
                self._goto(mapping[key])

    def _focus_primary(self) -> None:
        """Move keyboard focus to the main control for the current view."""
        try:
            if self._view == "money":
                self.amount_field.focus()
            elif self._view == "vitality":
                self.health_field.focus()
            elif self._view in ("weapons", "settings"):
                self.profile_dd.focus()
            elif self._view == "menu":
                pass
        except Exception:
            pass

    # --- navigation ---

    def _goto(self, view: str) -> None:
        self._view = view
        builders = {
            "menu": self._build_menu,
            "money": self._build_money,
            "weapons": self._build_weapons,
            "vitality": self._build_vitality,
            "settings": self._build_settings,
        }
        self.switcher.content = builders[view]()
        if view in ("money", "weapons", "vitality"):
            self.load_slots()
            if view == "weapons":
                self._load_weapons_into_ui()
            elif view == "vitality":
                self._load_vitality_into_ui()
        self.page.update()
        self._focus_primary()

    def _menu_tile(self, title: str, subtitle: str, view: str, shortcut: str) -> ft.Control:
        """Focusable outlined button (keyboard + screen reader friendly)."""
        return ft.OutlinedButton(
            content=ft.Column(
                [
                    ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=GOLD),
                    ft.Text(subtitle, size=13, color=MUTED),
                    ft.Text(f"Shortcut [{shortcut}]", size=11, color=MUTED),
                ],
                spacing=4,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            style=ft.ButtonStyle(
                bgcolor=PANEL,
                side=ft.BorderSide(2, GOLD),
                shape=ft.RoundedRectangleBorder(radius=2),
                padding=20,
                overlay_color="#ffffff22",
            ),
            tooltip=f"Open {title} editor (press {shortcut} from menu)",
            expand=True,
            on_click=lambda _e, v=view: self._goto(v),
        )

    def _build_menu(self) -> ft.Control:
        return ft.Column(
            [
                ft.Text("Choose an editor", size=15, color=FG, weight=ft.FontWeight.W_500),
                ft.Row(
                    [
                        self._menu_tile("Money", "Set or add cash", "money", "1"),
                        self._menu_tile("Weapons", "Guns + ammo loadout", "weapons", "2"),
                    ],
                    spacing=12,
                    expand=True,
                ),
                ft.Row(
                    [
                        self._menu_tile(
                            "Vitality", "Health, armour, maxima", "vitality", "3"
                        ),
                        self._menu_tile(
                            "Settings", "Backup + write technique", "settings", "4"
                        ),
                    ],
                    spacing=12,
                    expand=True,
                ),
            ],
            spacing=14,
            expand=True,
        )

    def _back_bar(self, title: str) -> ft.Control:
        return ft.Row(
            [
                ft.OutlinedButton(
                    "Menu",
                    style=ft.ButtonStyle(color=GOLD, side=ft.BorderSide(2, FOCUS)),
                    tooltip="Back to startup menu (Esc)",
                    on_click=lambda _e: self._goto("menu"),
                ),
                ft.Semantics(
                    label=title,
                    heading_level=2,
                    content=ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=GOLD),
                ),
                ft.Container(expand=True),
                ft.FilledButton(
                    "Refresh",
                    bgcolor=GREEN_HI,
                    color=BTN_ON_GREEN,
                    tooltip="Reload profiles and save slots",
                    on_click=lambda _e: self.refresh(),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _profile_block(self) -> ft.Control:
        return ft.Column(
            [
                ft.Row(
                    [self.profile_dd],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self.version_chip,
                _outlined(
                    ft.Column([self.slots_table], scroll=ft.ScrollMode.AUTO, expand=True),
                    expand=True,
                    padding=8,
                ),
            ],
            spacing=8,
            expand=True,
        )

    def _build_money(self) -> ft.Control:
        return ft.Column(
            [
                self._back_bar("Money"),
                self._profile_block(),
                ft.Row(
                    [
                        self.amount_field,
                        ft.FilledButton(
                            "Set money",
                            bgcolor=GREEN_HI,
                            color=BTN_ON_GREEN,
                            tooltip="Overwrite cash with the amount field",
                            on_click=lambda _e: self.on_set(),
                        ),
                        ft.FilledButton(
                            "Add money",
                            bgcolor=GREEN,
                            color=BTN_ON_GREEN,
                            tooltip="Add the amount field to current cash",
                            on_click=lambda _e: self.on_add(),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            expand=True,
            spacing=8,
        )

    def _build_weapons(self) -> ft.Control:
        self._weapon_rows = []
        rows: list[ft.Control] = []
        for i in range(WEAPON_SLOT_COUNT):
            dd = ft.Dropdown(
                label=f"Slot {i}",
                width=260,
                options=list(self._weapon_catalog_opts),
                border_color=GREEN_HI,
                focused_border_color=FOCUS,
                focused_border_width=2,
                label_style=ft.TextStyle(color=MUTED, size=11),
                text_style=ft.TextStyle(color=FG, size=12),
                tooltip=f"Weapon for inventory slot {i}",
                on_select=lambda e, idx=i: self._on_weapon_select(idx, e),
            )
            custom = ft.TextField(
                label="Custom ID",
                width=100,
                visible=False,
                border_color=GREEN_HI,
                focused_border_color=FOCUS,
                focused_border_width=2,
                label_style=ft.TextStyle(color=MUTED, size=11),
                text_style=ft.TextStyle(color=FG, size=12),
                cursor_color=FOCUS,
                tooltip="Mod or unknown weapon id",
            )
            ammo = ft.TextField(
                label="Ammo",
                width=90,
                value="0",
                border_color=GREEN_HI,
                focused_border_color=FOCUS,
                focused_border_width=2,
                label_style=ft.TextStyle(color=MUTED, size=11),
                text_style=ft.TextStyle(color=FG, size=12),
                cursor_color=FOCUS,
                tooltip=f"Ammo for slot {i}",
            )
            badge = ft.Text("—", width=140, color=MUTED, size=11)
            self._weapon_rows.append(
                {"dd": dd, "custom": custom, "ammo": ammo, "badge": badge}
            )
            rows.append(
                ft.Row(
                    [dd, custom, ammo, badge],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                )
            )

        return ft.Column(
            [
                self._back_bar("Weapons"),
                self._profile_block(),
                _outlined(
                    ft.Column(
                        [
                            ft.Text("Loadout (10 slots)", color=GOLD, size=13),
                            ft.Column(rows, scroll=ft.ScrollMode.AUTO, expand=True, spacing=4),
                            ft.Row(
                                [
                                    ft.FilledButton(
                                        "Reload from save",
                                        bgcolor=GREEN,
                                        color=BTN_ON_GREEN,
                                        on_click=lambda _e: self._load_weapons_into_ui(),
                                    ),
                                    ft.FilledButton(
                                        "Apply loadout",
                                        bgcolor=GREEN_HI,
                                        color=BTN_ON_GREEN,
                                        on_click=lambda _e: self._apply_weapons(),
                                    ),
                                    ft.OutlinedButton(
                                        "Max ammo (9999)",
                                        style=ft.ButtonStyle(color=GOLD, side=ft.BorderSide(1, GOLD)),
                                        on_click=lambda _e: self._max_ammo(),
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        expand=True,
                        spacing=8,
                    ),
                    expand=True,
                ),
            ],
            expand=True,
            spacing=8,
        )

    def _build_vitality(self) -> ft.Control:
        return ft.Column(
            [
                self._back_bar("Vitality"),
                self._profile_block(),
                _outlined(
                    ft.Column(
                        [
                            ft.Text(
                                f"Current health/armour floats (UI suggest {UI_CLAMP_MIN:g}–{UI_CLAMP_MAX:g})",
                                color=MUTED,
                                size=12,
                            ),
                            ft.Row(
                                [self.health_field, self.armour_field],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(
                                f"Max health/armour uint16 (0–{UI_MAX_CLAMP})",
                                color=MUTED,
                                size=12,
                            ),
                            ft.Row(
                                [
                                    self.max_health_field,
                                    self.max_armour_field,
                                    ft.FilledButton(
                                        "Reload",
                                        bgcolor=GREEN,
                                        color=BTN_ON_GREEN,
                                        on_click=lambda _e: self._load_vitality_into_ui(),
                                    ),
                                    ft.FilledButton(
                                        "Apply",
                                        bgcolor=GREEN_HI,
                                        color=BTN_ON_GREEN,
                                        on_click=lambda _e: self._apply_vitality(),
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=10,
                    )
                ),
            ],
            expand=True,
            spacing=8,
        )

    def _build_settings(self) -> ft.Control:
        return ft.Column(
            [
                self._back_bar("Settings"),
                _outlined(
                    ft.Column(
                        [
                            self.autobackup,
                            self.also_autosave,
                            ft.Divider(color=OUTLINE),
                            ft.Text("Write technique", color=GOLD, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "Save dword v57 (CE and pre-CE families) uses PlayerInfo in-place patches (Parik: PlayerInfo "
                                "unchanged vs older IV; End-block / Radar Blip differ and are never "
                                "rewritten). Unsupported versions are refused. Status chip shows "
                                "the active technique for the selected slot.",
                                color=MUTED,
                                size=12,
                            ),
                        ],
                        spacing=10,
                    )
                ),
            ],
            expand=True,
            spacing=8,
        )

    # --- shared helpers ---

    def _persist_settings(self) -> None:
        self._settings["autobackup"] = bool(self.autobackup.value)
        self._settings["also_autosave"] = bool(self.also_autosave.value)
        try:
            save_settings(self._settings)
        except OSError:
            pass

    def set_status(self, text: str) -> None:
        self.status.value = text
        self.status.color = GOLD
        self.page.update()
        self.status.color = MUTED

    def _alert(self, title: str, message: str, *, error: bool = False) -> None:
        def close(_e: ft.ControlEvent | None = None) -> None:
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(title, color=GOLD if not error else ERROR),
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
        if self._view == "weapons":
            self._load_weapons_into_ui()
        elif self._view == "vitality":
            self._load_vitality_into_ui()

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
                f"Found {len(self.profiles)} profile(s). Close GTAIV.exe before writing."
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

    def targets_for(self, slot: SaveSlot) -> list[Path]:
        paths = [slot.path]
        if (
            bool(self.also_autosave.value)
            and slot.slot_name != "SGTA412"
            and slot.path.parent.joinpath("SGTA412").is_file()
        ):
            paths.append(slot.path.parent / "SGTA412")
        return paths

    def _gate_write(self, slot: SaveSlot) -> bool:
        if slot.error:
            self._alert(APP_NAME, f"Cannot edit this save:\n{slot.error}", error=True)
            return False
        if is_gtaiv_running():
            self._alert(
                APP_NAME,
                "GTAIV.exe is running.\n\nClose the game completely before editing saves.",
                error=True,
            )
            return False
        return True

    # --- money ---

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

    def on_set(self) -> None:
        self._start_money("set")

    def on_add(self) -> None:
        self._start_money("add")

    def _start_money(self, mode: str) -> None:
        slot = self.selected_slot()
        amount = self.parse_amount()
        if slot is None or amount is None or not self._gate_write(slot):
            return
        if amount > 999_999_999:
            self._confirm(
                APP_NAME,
                f"${amount:,} is above the usual UI clamp (999,999,999).\nContinue anyway?",
                on_yes=lambda: self._confirm_paths_money(mode, slot, amount),
            )
            return
        self._confirm_paths_money(mode, slot, amount)

    def _confirm_paths_money(self, mode: str, slot: SaveSlot, amount: int) -> None:
        paths = self.targets_for(slot)
        self._confirm_path_at_money(mode, slot, amount, paths, 0)

    def _confirm_path_at_money(
        self, mode: str, slot: SaveSlot, amount: int, paths: list[Path], index: int
    ) -> None:
        if index >= len(paths):
            self._do_money_write(mode, paths, amount)
            return
        path = paths[index]
        check = check_write(path, allow_non_ce_path=False)
        if check.allowed:
            if check.warnings:
                self._confirm(
                    APP_NAME,
                    "Warnings:\n- " + "\n- ".join(check.warnings) + "\n\nContinue?",
                    on_yes=lambda: self._confirm_path_at_money(
                        mode, slot, amount, paths, index + 1
                    ),
                )
                return
            self._confirm_path_at_money(mode, slot, amount, paths, index + 1)
            return
        if "Non-CE" in check.reason:
            self._confirm(
                APP_NAME,
                check.reason + "\n\nForce write anyway?",
                on_yes=lambda: self._confirm_path_at_money(mode, slot, amount, paths, index + 1),
            )
            return
        self._alert(APP_NAME, f"Write blocked:\n{check.reason}", error=True)

    def _do_money_write(self, mode: str, paths: list[Path], amount: int) -> None:
        try:
            lines: list[str] = []
            backup_lines: list[str] = []
            for path in paths:
                allow_non_ce = "Non-CE" in check_write(path, allow_non_ce_path=False).reason
                if mode == "set":
                    old, new, bak, _ = set_money(
                        path,
                        amount,
                        backup=bool(self.autobackup.value),
                        allow_non_ce_path=allow_non_ce,
                    )
                else:
                    old, new, bak, _ = add_money(
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

    # --- weapons ---

    def _on_weapon_select(self, idx: int, _e: ft.ControlEvent) -> None:
        row = self._weapon_rows[idx]
        is_custom = row["dd"].value == "custom"
        row["custom"].visible = is_custom
        self.page.update()

    def _load_weapons_into_ui(self) -> None:
        if not self._weapon_rows:
            return
        slot = (
            self.slots[self._selected_index]
            if self._selected_index is not None and self._selected_index < len(self.slots)
            else None
        )
        if slot is None or slot.error:
            return
        try:
            loadout = read_loadout_file(slot.path)
        except Exception as e:
            self.set_status(f"Loadout read failed: {e}")
            return
        catalog_keys = {o.key for o in self._weapon_catalog_opts}
        for i, row in enumerate(self._weapon_rows):
            wid = loadout.weapon_ids[i]
            ammo = loadout.ammo[i]
            det = loadout.detected[i]
            key = str(wid) if str(wid) in catalog_keys else "custom"
            row["dd"].value = key
            row["custom"].visible = key == "custom"
            row["custom"].value = str(wid) if key == "custom" else ""
            row["ammo"].value = str(ammo)
            color = GOLD if det.kind == "stock" else ("#c9a227" if det.kind == "mod" else MUTED)
            label = {"stock": "Stock", "mod": "Mod", "empty": "Empty"}[det.kind]
            row["badge"].value = f"{label}: {det.name}"
            row["badge"].color = color
        self.page.update()

    def _max_ammo(self) -> None:
        for row in self._weapon_rows:
            row["ammo"].value = "9999"
        self.page.update()

    def _collect_loadout(self) -> tuple[list[int], list[int]] | None:
        weapons: list[int] = []
        ammo: list[int] = []
        for i, row in enumerate(self._weapon_rows):
            key = row["dd"].value
            if key == "custom" or key is None:
                raw = (row["custom"].value or "").strip()
                try:
                    wid = int(raw, 0)
                except ValueError:
                    self._alert(APP_NAME, f"Slot {i}: enter a valid custom weapon ID.", error=True)
                    return None
            else:
                wid = int(key)
            try:
                a = int((row["ammo"].value or "0").strip())
            except ValueError:
                self._alert(APP_NAME, f"Slot {i}: ammo must be a whole number.", error=True)
                return None
            if a < 0 or a > 0xFFFF:
                self._alert(APP_NAME, f"Slot {i}: ammo must be 0..65535.", error=True)
                return None
            weapons.append(wid)
            ammo.append(a)
        return weapons, ammo

    def _apply_weapons(self) -> None:
        slot = self.selected_slot()
        if slot is None or not self._gate_write(slot):
            return
        collected = self._collect_loadout()
        if collected is None:
            return
        weapons, ammo = collected

        def go() -> None:
            self._write_weapons_paths(self.targets_for(slot), weapons, ammo)

        self._confirm_paths_generic(slot, go)

    def _write_weapons_paths(
        self, paths: list[Path], weapons: list[int], ammo: list[int]
    ) -> None:
        try:
            lines: list[str] = []
            for path in paths:
                allow_non_ce = "Non-CE" in check_write(path, allow_non_ce_path=False).reason
                old, new, bak, _ = write_loadout(
                    path,
                    weapons,
                    ammo,
                    backup=bool(self.autobackup.value),
                    allow_non_ce_path=allow_non_ce,
                )
                mod_n = sum(1 for d in new.detected if d.kind == "mod")
                lines.append(
                    f"{path.name}: {sum(1 for w in old.weapon_ids if w)} → "
                    f"{sum(1 for w in new.weapon_ids if w)} armed"
                    + (f" ({mod_n} mod)" if mod_n else "")
                )
                if bak:
                    lines.append(f"  backup: {bak.beside.name}")
            self._load_weapons_into_ui()
            self.set_status(" | ".join(lines))
            self._alert(APP_NAME, "Loadout updated.\n\n" + "\n".join(lines))
        except Exception as e:
            self._alert(APP_NAME, str(e), error=True)

    # --- vitality ---

    def _load_vitality_into_ui(self) -> None:
        slot = (
            self.slots[self._selected_index]
            if self._selected_index is not None and self._selected_index < len(self.slots)
            else None
        )
        if slot is None or slot.error:
            return
        try:
            v = read_vitality_file(slot.path)
            self.health_field.value = f"{v.health:.1f}".rstrip("0").rstrip(".")
            self.armour_field.value = f"{v.armour:.1f}".rstrip("0").rstrip(".")
            self.max_health_field.value = str(v.max_health)
            self.max_armour_field.value = str(v.max_armour)
            self.page.update()
        except Exception as e:
            self.set_status(f"Vitality read failed: {e}")

    def _apply_vitality(self) -> None:
        slot = self.selected_slot()
        if slot is None or not self._gate_write(slot):
            return
        try:
            health = float((self.health_field.value or "").strip())
            armour = float((self.armour_field.value or "").strip())
            max_health = int((self.max_health_field.value or "").strip())
            max_armour = int((self.max_armour_field.value or "").strip())
        except ValueError:
            self._alert(
                APP_NAME,
                "Health/armour must be numbers; max health/armour must be whole numbers.",
                error=True,
            )
            return
        if max_health < 0 or max_health > UI_MAX_CLAMP or max_armour < 0 or max_armour > UI_MAX_CLAMP:
            self._alert(APP_NAME, f"Max health/armour must be 0..{UI_MAX_CLAMP}.", error=True)
            return

        def go() -> None:
            self._write_vitality_paths(
                self.targets_for(slot), health, armour, max_health, max_armour
            )

        if health < UI_CLAMP_MIN or health > UI_CLAMP_MAX or armour < UI_CLAMP_MIN or armour > UI_CLAMP_MAX:
            self._confirm(
                APP_NAME,
                f"Current values outside usual UI range ({UI_CLAMP_MIN:g}–{UI_CLAMP_MAX:g}). Continue?",
                on_yes=lambda: self._confirm_paths_generic(slot, go),
            )
            return
        self._confirm_paths_generic(slot, go)

    def _write_vitality_paths(
        self,
        paths: list[Path],
        health: float,
        armour: float,
        max_health: int,
        max_armour: int,
    ) -> None:
        try:
            lines: list[str] = []
            for path in paths:
                allow_non_ce = "Non-CE" in check_write(path, allow_non_ce_path=False).reason
                old, new, bak, _ = set_vitality(
                    path,
                    health,
                    armour,
                    max_health,
                    max_armour,
                    backup=bool(self.autobackup.value),
                    allow_non_ce_path=allow_non_ce,
                )
                lines.append(
                    f"{path.name}: H {old.health:.1f}/{old.max_health} A {old.armour:.1f}/{old.max_armour} → "
                    f"{new.health:.1f}/{new.max_health} {new.armour:.1f}/{new.max_armour}"
                )
                if bak:
                    lines.append(f"  backup: {bak.beside.name}")
            self._load_vitality_into_ui()
            self.set_status(" | ".join(lines))
            self._alert(APP_NAME, "Vitality updated.\n\n" + "\n".join(lines))
        except Exception as e:
            self._alert(APP_NAME, str(e), error=True)

    def _confirm_paths_generic(self, slot: SaveSlot, on_ready) -> None:
        paths = self.targets_for(slot)

        def step(index: int) -> None:
            if index >= len(paths):
                on_ready()
                return
            path = paths[index]
            check = check_write(path, allow_non_ce_path=False)
            if check.allowed:
                if check.warnings:
                    self._confirm(
                        APP_NAME,
                        "Warnings:\n- " + "\n- ".join(check.warnings) + "\n\nContinue?",
                        on_yes=lambda: step(index + 1),
                    )
                    return
                step(index + 1)
                return
            if "Non-CE" in check.reason:
                self._confirm(
                    APP_NAME,
                    check.reason + "\n\nForce write anyway?",
                    on_yes=lambda: step(index + 1),
                )
                return
            self._alert(APP_NAME, f"Write blocked:\n{check.reason}", error=True)

        step(0)


def main(page: ft.Page) -> None:
    Save4BucksApp(page)


def run() -> None:
    assets = str(_resource_path("assets").parent / "assets")
    ft.run(main, assets_dir=assets if Path(assets).is_dir() else None)


if __name__ == "__main__":
    run()
