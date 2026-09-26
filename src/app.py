"""4Bucks - multi-view Flet UI for GTA IV CE PlayerInfo + Garages editing."""

from __future__ import annotations

import sys
from pathlib import Path

import flet as ft

from . import APP_NAME, __version__
from .detect import SaveSlot, find_profile_dirs, is_gtaiv_running, list_slots
from .playerinfo import WEAPON_SLOT_COUNT
from .safehouse_parking import SAFEHOUSES
from .save_garage import (
    FLAG_VALID,
    STORED_CAR_COUNT,
    StoredCar,
    list_safehouse_slots,
    proofs_to_flags,
    read_stored_cars_file,
    spawn_at_safehouse,
    update_stored_car,
)
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
from .vehicles_catalog import list_vehicles, vehicle_name
from .versioning import check_write, inspect_save, status_chip
from .weapon_detect import (
    classify_weapon,
    inspect_install,
    list_gtaiv_installs,
    load_mod_weapon_names,
)
from .weapons_catalog import picker_options, short_name

BG = "#12161a"
PANEL = "#1a2228"
FG = "#f0f4f0"
MUTED = "#b0bbb4"
GOLD = "#e0c04a"
GREEN = "#245a42"
GREEN_HI = "#3a8f68"
OUTLINE = "#4a7a60"
FOCUS = "#f0d878"
ERROR = "#f08080"
BTN_ON_GREEN = "#12161a"

# Per-view fitted window sizes (user cannot resize; snap on navigate).
# Sized to content — no scrollbars. Includes brand + status chrome.
WINDOW_SIZES: dict[str, tuple[int, int]] = {
    "gate": (640, 540),
    "menu": (560, 560),
    "money": (600, 290),
    "weapons": (780, 680),
    "vitality": (620, 360),
    "garage": (720, 560),
    "settings": (560, 420),
}



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
        self.active_slot: SaveSlot | None = None
        self.active_install: Path | None = None
        self._mod_names: dict[int, str] = {}
        self._installs: list[Path] = []
        self._view = "gate"
        self._equipped_slot = 0
        self._weapon_ids: list[int] = [0] * WEAPON_SLOT_COUNT
        self._ammo_fields: list[ft.TextField] = []
        self._slot_name_labels: list[ft.Text] = []
        self._slot_badge_labels: list[ft.Text] = []
        self._slot_cards: list[ft.Container] = []
        self._picker_slot: int | None = None
        self._garage_safehouse = SAFEHOUSES[0].id
        self._garage_draft: list[StoredCar | None] = [None] * STORED_CAR_COUNT
        self._vehicle_picker_spot: tuple[str, int] | None = None  # safehouse, spot
        self._vehicle_picker_mode: str = "edit"  # edit | spawn
        self._vehicle_picker_car_index: int | None = None

        page.title = f"{APP_NAME} v{__version__}"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = BG
        page.padding = 16
        page.window.resizable = False
        page.window.maximizable = False
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

        field_kw = dict(
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            focused_border_width=2,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
            cursor_color=FOCUS,
        )

        self.profile_dd = ft.Dropdown(
            label="Profile",
            expand=True,
            options=[],
            on_select=lambda _e: self._on_gate_profile(),
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            focused_border_width=2,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG, size=13),
            tooltip="Rockstar Profiles folder",
        )
        self.slot_dd = ft.Dropdown(
            label="Save",
            expand=True,
            options=[],
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            focused_border_width=2,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG, size=13),
            tooltip="SGTA4xx slot to edit",
        )
        self.install_dd = ft.Dropdown(
            label="GTA IV install",
            expand=True,
            options=[],
            on_select=lambda _e: self._on_gate_install(),
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            focused_border_width=2,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG, size=12),
            tooltip="Auto-detected game folder (version + mods)",
        )
        self.install_status = ft.Text("", color=MUTED, size=12)
        self.last_used_hint = ft.Text("", color=MUTED, size=12)
        self.active_chip = ft.Text("", color=GOLD, weight=ft.FontWeight.W_600, size=12)
        self.status = ft.Text("", color=MUTED, size=12, selectable=True)
        self._file_picker = ft.FilePicker()
        try:
            page.services.append(self._file_picker)
        except Exception:
            page.overlay.append(self._file_picker)

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
            expand=True,
            tooltip=f"Current health ({UI_CLAMP_MIN:g}–{UI_CLAMP_MAX:g})",
            border_color=GOLD,
            focused_border_color=FOCUS,
            focused_border_width=2,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
            cursor_color=FOCUS,
        )
        self.armour_field = ft.TextField(
            label="Armour",
            value="100",
            expand=True,
            tooltip=f"Current armour ({UI_CLAMP_MIN:g}–{UI_CLAMP_MAX:g})",
            border_color=GOLD,
            focused_border_color=FOCUS,
            focused_border_width=2,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
            cursor_color=FOCUS,
        )
        self.max_health_field = ft.TextField(
            label="Max health",
            value="200",
            expand=True,
            tooltip=f"Max health (0–{UI_MAX_CLAMP})",
            border_color=GOLD,
            focused_border_color=FOCUS,
            focused_border_width=2,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
            cursor_color=FOCUS,
        )
        self.max_armour_field = ft.TextField(
            label="Max armour",
            value="100",
            expand=True,
            tooltip=f"Max armour (0–{UI_MAX_CLAMP})",
            border_color=GOLD,
            focused_border_color=FOCUS,
            focused_border_width=2,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
            cursor_color=FOCUS,
        )
        self.autobackup = ft.Checkbox(
            label="Autobackup before write",
            value=bool(self._settings.get("autobackup", True)),
            active_color=GOLD,
            on_change=lambda _e: self._persist_settings(),
            label_style=ft.TextStyle(color=FG, size=13),
            tooltip="Copy beside the save as .backup and under app backups/",
        )
        self.also_autosave = ft.Checkbox(
            label="Also update autosave",
            value=bool(self._settings.get("also_autosave", True)),
            active_color=GOLD,
            on_change=lambda _e: self._persist_settings(),
            label_style=ft.TextStyle(color=FG, size=13),
            tooltip="When editing a manual slot, also write SGTA412",
        )

        self.switcher = ft.AnimatedSwitcher(
            content=self._build_gate(),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=280,
            reverse_duration=200,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
        )

        self.brand = ft.Semantics(
            label=f"{APP_NAME} version {__version__}",
            heading_level=1,
            content=ft.Text(APP_NAME, size=24, weight=ft.FontWeight.BOLD, color=GOLD),
        )

        page.add(
            ft.Column(
                [
                    self.brand,
                    self.switcher,
                    ft.Semantics(label="Status", live_region=True, content=self.status),
                ],
                spacing=10,
                tight=True,
            )
        )
        self._fit_window("gate")
        self.refresh_gate()

    # --- window / nav ---

    def _fit_window(self, view: str) -> None:
        """Snap window to the view's fitted size (no scroll, no wasted chrome)."""
        w, h = WINDOW_SIZES.get(view, (640, 500))
        win = self.page.window
        # Do not pin max_* to the current size — that blocks shrink on navigate.
        # User resize is already disabled via resizable=False.
        win.min_width = 0
        win.min_height = 0
        win.max_width = None
        win.max_height = None
        win.width = w
        win.height = h

    def _on_keyboard(self, e: ft.KeyboardEvent) -> None:
        key = (e.key or "").lower()
        if key in ("escape", "esc"):
            if self._view not in ("gate", "menu"):
                self._goto("menu")
            return
        if self._view == "gate" and key in ("enter", "return") and not e.ctrl and not e.alt:
            self._continue_from_gate()
            return
        if self._view == "menu" and not e.ctrl and not e.alt and not e.meta:
            mapping = {
                "1": "money",
                "2": "weapons",
                "3": "vitality",
                "4": "garage",
                "5": "settings",
                "s": "settings",
            }
            if key in mapping:
                self._goto(mapping[key])

    def _focus_primary(self) -> None:
        async def _do_focus() -> None:
            try:
                if self._view == "money":
                    await self.amount_field.focus()
                elif self._view == "vitality":
                    await self.health_field.focus()
                elif self._view == "gate":
                    await self.slot_dd.focus()
            except Exception:
                pass

        try:
            self.page.run_task(_do_focus)
        except Exception:
            pass

    def _goto(self, view: str) -> None:
        if view != "gate" and self.active_slot is None and view != "menu":
            self._goto("gate")
            return
        self._view = view
        builders = {
            "gate": self._build_gate,
            "menu": self._build_menu,
            "money": self._build_money,
            "weapons": self._build_weapons,
            "vitality": self._build_vitality,
            "garage": self._build_garage,
            "settings": self._build_settings,
        }
        self.switcher.content = builders[view]()
        if view == "weapons":
            self._load_weapons_into_ui()
        elif view == "vitality":
            self._load_vitality_into_ui()
        elif view == "garage":
            self._load_garage_into_ui()
        elif view in ("money", "weapons", "vitality", "garage", "menu"):
            self._refresh_active_chip()
        self._fit_window(view)
        self.page.update()
        self._focus_primary()

    # --- icons / menu ---

    def _menu_icon(self, name: str) -> ft.Control:
        path = _resource_path("assets", "menu", f"{name}.svg")
        if path.is_file():
            return ft.Image(
                src=f"menu/{name}.svg",
                width=48,
                height=48,
                fit=ft.BoxFit.CONTAIN,
                exclude_from_semantics=True,
            )
        return ft.Container(width=48, height=48)

    def _gold_icon(self, name: str, *, size: int = 22) -> ft.Control:
        path = _resource_path("assets", "menu", f"{name}.svg")
        if path.is_file():
            return ft.Image(
                src=f"menu/{name}.svg",
                width=size,
                height=size,
                fit=ft.BoxFit.CONTAIN,
                exclude_from_semantics=True,
            )
        return ft.Container(width=size, height=size)

    def _menu_tile(
        self, title: str, blurb: str, view: str, shortcut: str, *, icon: str
    ) -> ft.Control:
        tip = f"{title} - {blurb}. Press {shortcut}."
        return ft.Container(
            content=ft.OutlinedButton(
                content=ft.Column(
                    [
                        self._menu_icon(icon),
                        ft.Text(title, size=15, weight=ft.FontWeight.W_600, color=GOLD),
                    ],
                    spacing=6,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                style=ft.ButtonStyle(
                    bgcolor=PANEL,
                    side=ft.BorderSide(1.5, GOLD),
                    shape=ft.RoundedRectangleBorder(radius=6),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                    overlay_color="#e0c04a22",
                ),
                tooltip=tip,
                expand=True,
                on_click=lambda _e, v=view: self._goto(v),
            ),
            expand=True,
            height=118,
        )

    def _wheel_tile(
        self,
        title: str,
        blurb: str,
        view: str,
        shortcut: str,
        *,
        icon: str,
        size: int = 108,
    ) -> ft.Control:
        tip = f"{title} - {blurb}. Press {shortcut}."
        return ft.Container(
            content=ft.OutlinedButton(
                content=ft.Column(
                    [
                        self._menu_icon(icon),
                        ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=GOLD),
                    ],
                    spacing=4,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                style=ft.ButtonStyle(
                    bgcolor=PANEL,
                    side=ft.BorderSide(1.5, GOLD),
                    shape=ft.RoundedRectangleBorder(radius=size // 2),
                    padding=ft.Padding.all(10),
                    overlay_color="#e0c04a33",
                ),
                tooltip=tip,
                width=size,
                height=size,
                on_click=lambda _e, v=view: self._goto(v),
            ),
            width=size,
            height=size,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            scale=1.0,
            on_hover=lambda e, c=None: self._wheel_hover(e),
        )

    def _wheel_hover(self, e: ft.ControlEvent) -> None:
        ctrl = e.control
        try:
            ctrl.scale = 1.06 if e.data == "true" else 1.0
            ctrl.update()
        except Exception:
            pass

    def _wheel_center_settings(self, *, size: int = 96) -> ft.Control:
        tip = "Settings - Backup and options. Press 5 or S."
        return ft.Container(
            content=ft.OutlinedButton(
                content=ft.Column(
                    [
                        self._menu_icon("settings"),
                        ft.Text("Settings", size=12, weight=ft.FontWeight.W_600, color=GOLD),
                    ],
                    spacing=2,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                style=ft.ButtonStyle(
                    bgcolor="#243028",
                    side=ft.BorderSide(2, GOLD),
                    shape=ft.RoundedRectangleBorder(radius=size // 2),
                    padding=ft.Padding.all(8),
                    overlay_color="#e0c04a44",
                ),
                tooltip=tip,
                width=size,
                height=size,
                on_click=lambda _e: self._goto("settings"),
            ),
            width=size,
            height=size,
            animate_scale=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
            scale=1.0,
            on_hover=lambda e: self._wheel_hover(e),
        )

    def _build_menu(self) -> ft.Control:
        wheel = 400
        tile = 108
        center = 96
        mid = (wheel - tile) / 2
        cmid = (wheel - center) / 2
        stack = ft.Stack(
            [
                # Outer ring: Money N, Weapons E, Vitality S, Garage W
                ft.Container(
                    content=self._wheel_tile(
                        "Money", "Set or add cash", "money", "1", icon="money", size=tile
                    ),
                    left=mid,
                    top=8,
                    width=tile,
                    height=tile,
                ),
                ft.Container(
                    content=self._wheel_tile(
                        "Weapons",
                        "Guns and ammo",
                        "weapons",
                        "2",
                        icon="weapons",
                        size=tile,
                    ),
                    left=wheel - tile - 8,
                    top=mid,
                    width=tile,
                    height=tile,
                ),
                ft.Container(
                    content=self._wheel_tile(
                        "Vitality",
                        "Health and armour",
                        "vitality",
                        "3",
                        icon="vitality",
                        size=tile,
                    ),
                    left=mid,
                    top=wheel - tile - 8,
                    width=tile,
                    height=tile,
                ),
                ft.Container(
                    content=self._wheel_tile(
                        "Garage",
                        "Safehouse cars",
                        "garage",
                        "4",
                        icon="garage",
                        size=tile,
                    ),
                    left=8,
                    top=mid,
                    width=tile,
                    height=tile,
                ),
                # Center Settings
                ft.Container(
                    content=self._wheel_center_settings(size=center),
                    left=cmid,
                    top=cmid,
                    width=center,
                    height=center,
                ),
            ],
            width=wheel,
            height=wheel,
        )
        return ft.Column(
            [
                self.active_chip,
                ft.Container(content=stack, alignment=ft.Alignment.CENTER, expand=True),
                ft.TextButton(
                    "Change save",
                    style=ft.ButtonStyle(color=MUTED),
                    tooltip="Pick a different profile or slot",
                    on_click=lambda _e: self._goto("gate"),
                ),
            ],
            spacing=8,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

    # --- save gate ---

    def _build_gate(self) -> ft.Control:
        return ft.Column(
            [
                ft.Text("Select save", size=18, weight=ft.FontWeight.W_600, color=GOLD),
                self.last_used_hint,
                ft.Text("Game", size=13, weight=ft.FontWeight.W_600, color=GOLD),
                self.install_dd,
                self.install_status,
                ft.Text("Save file", size=13, weight=ft.FontWeight.W_600, color=GOLD),
                self.profile_dd,
                self.slot_dd,
                ft.Row(
                    [
                        ft.OutlinedButton(
                            "Refresh",
                            style=ft.ButtonStyle(color=GOLD, side=ft.BorderSide(1.5, GOLD)),
                            tooltip="Rescan profiles and known GTA IV installs",
                            on_click=lambda _e: self.refresh_gate(),
                        ),
                        ft.OutlinedButton(
                            "Browse…",
                            style=ft.ButtonStyle(color=MUTED, side=ft.BorderSide(1, OUTLINE)),
                            tooltip="Pick a GTA IV folder manually",
                            on_click=lambda _e: self.page.run_task(self._browse_install),
                        ),
                        ft.FilledButton(
                            "Continue",
                            bgcolor=GREEN_HI,
                            color=BTN_ON_GREEN,
                            on_click=lambda _e: self._continue_from_gate(),
                        ),
                    ],
                    spacing=12,
                    wrap=True,
                ),
            ],
            spacing=10,
            tight=True,
        )

    def refresh_gate(self) -> None:
        self.refresh_installs()
        self.refresh_profiles()

    def refresh_installs(self) -> None:
        load_mod_weapon_names.cache_clear()
        self._installs = list_gtaiv_installs()
        last = str(self._settings.get("last_install") or "")
        if last:
            last_path = Path(last)
            if last_path not in self._installs and (
                (last_path / "GTAIV.exe").is_file()
                or (last_path / "common" / "data").is_dir()
            ):
                self._installs.insert(0, last_path.resolve())
        labels = [str(p) for p in self._installs]
        self.install_dd.options = [
            ft.DropdownOption(key=lab, text=lab) for lab in labels
        ]
        if labels:
            if last in labels:
                self.install_dd.value = last
            elif self.install_dd.value not in labels:
                self.install_dd.value = labels[0]
            self._apply_selected_install()
        else:
            self.install_dd.value = None
            self.active_install = None
            self._mod_names = {}
            self.install_status.value = "No GTA IV install found in known locations."
        self.page.update()

    def _on_gate_install(self) -> None:
        self._apply_selected_install()
        self.page.update()

    def _apply_selected_install(self) -> None:
        path_str = self.install_dd.value
        if not path_str:
            self.active_install = None
            self._mod_names = {}
            self.install_status.value = ""
            return
        path = Path(path_str)
        self.active_install = path
        load_mod_weapon_names.cache_clear()
        self._mod_names = load_mod_weapon_names(path)
        info = inspect_install(path)
        self.install_status.value = info.status_line if info else "Install not readable."

    async def _browse_install(self) -> None:
        try:
            picked = await self._file_picker.get_directory_path(
                dialog_title="Select GTA IV install folder"
            )
        except Exception as e:
            self._alert(APP_NAME, f"Folder picker failed:\n{e}", error=True)
            return
        if not picked:
            return
        path = Path(picked)
        # Prefer nested GTAIV/ if user picked the Steam package root
        nested = path / "GTAIV"
        if not (path / "GTAIV.exe").is_file() and (nested / "GTAIV.exe").is_file():
            path = nested
        if not (
            (path / "GTAIV.exe").is_file() or (path / "common" / "data").is_dir()
        ):
            self._alert(
                APP_NAME,
                "That folder does not look like a GTA IV install (need GTAIV.exe or common/data).",
                error=True,
            )
            return
        path = path.resolve()
        key = str(path)
        if path not in self._installs:
            self._installs.insert(0, path)
            self.install_dd.options = [
                ft.DropdownOption(key=str(p), text=str(p)) for p in self._installs
            ]
        self.install_dd.value = key
        self._apply_selected_install()
        self.page.update()

    def refresh_profiles(self) -> None:
        self.profiles = find_profile_dirs()
        labels = [str(p) for p in self.profiles]
        self.profile_dd.options = [ft.DropdownOption(key=lab, text=lab) for lab in labels]
        last_p = str(self._settings.get("last_profile") or "")
        last_s = str(self._settings.get("last_slot") or "")
        if labels:
            if last_p in labels:
                self.profile_dd.value = last_p
            elif self.profile_dd.value not in labels:
                self.profile_dd.value = labels[0]
            self._reload_gate_slots(prefer_slot=last_s)
            if last_p and last_s and self.slot_dd.value == last_s:
                picked = next((s for s in self.slots if s.slot_name == last_s), None)
                label = picked.label if picked else last_s
                self.last_used_hint.value = f"Last used · {label}"
            else:
                self.last_used_hint.value = ""
            self.set_status(f"Found {len(self.profiles)} profile(s). Close GTAIV.exe before writing.")
        else:
            self.profile_dd.value = None
            self.slot_dd.options = []
            self.slot_dd.value = None
            self.slots = []
            self.last_used_hint.value = ""
            self.set_status("No GTA IV Profiles with SGTA saves found under Documents.")
        self.page.update()

    def _on_gate_profile(self) -> None:
        self._reload_gate_slots()

    def _reload_gate_slots(self, prefer_slot: str = "") -> None:
        self.slots = []
        path_str = self.profile_dd.value
        if not path_str:
            self.slot_dd.options = []
            self.slot_dd.value = None
            return
        self.slots = list_slots(Path(path_str))
        opts = []
        for s in self.slots:
            money = f"${s.money:,}" if s.money is not None else "—"
            opts.append(
                ft.DropdownOption(
                    key=s.slot_name,
                    text=f"{s.label} · {s.slot_name} · {money}",
                )
            )
        self.slot_dd.options = opts
        names = [s.slot_name for s in self.slots]
        if prefer_slot and prefer_slot in names:
            self.slot_dd.value = prefer_slot
        elif self.slot_dd.value not in names:
            prefer = next((n for n in names if n == "SGTA412"), names[0] if names else None)
            self.slot_dd.value = prefer

    def _continue_from_gate(self) -> None:
        path_str = self.profile_dd.value
        slot_name = self.slot_dd.value
        if not path_str or not slot_name:
            self._alert(APP_NAME, "Choose a profile and save slot.", error=True)
            return
        slot = next((s for s in self.slots if s.slot_name == slot_name), None)
        if slot is None:
            self._alert(APP_NAME, "Save slot not found. Refresh and try again.", error=True)
            return
        if slot.error:
            self._alert(APP_NAME, f"Cannot use this save:\n{slot.error}", error=True)
            return
        self.active_slot = slot
        if self.install_dd.value:
            self._settings["last_install"] = str(self.install_dd.value)
            self._apply_selected_install()
        self._settings["last_profile"] = path_str
        self._settings["last_slot"] = slot_name
        self._persist_settings()
        self._refresh_active_chip()
        self._goto("menu")

    def _refresh_active_chip(self) -> None:
        slot = self.active_slot
        if slot is None:
            self.active_chip.value = ""
            return
        try:
            ident = inspect_save(slot.path)
            check = check_write(slot.path, allow_non_ce_path=False)
            if not check.allowed and "Non-CE" in check.reason:
                soft = check_write(slot.path, allow_non_ce_path=True)
                text = status_chip(ident, soft if soft.allowed else check)
            else:
                text = status_chip(ident, check)
            title = ident.mission_title[:32] if ident.mission_title else slot.label
            self.active_chip.value = f"{slot.slot_name} · {title} · {text}"
        except Exception as e:
            self.active_chip.value = f"{slot.slot_name} · {e}"

    # --- editor chrome ---

    def _back_bar(self, title: str) -> ft.Control:
        return ft.Row(
            [
                ft.OutlinedButton(
                    "Menu",
                    style=ft.ButtonStyle(color=GOLD, side=ft.BorderSide(2, FOCUS)),
                    tooltip="Back to menu (Esc)",
                    on_click=lambda _e: self._goto("menu"),
                ),
                ft.Semantics(
                    label=title,
                    heading_level=2,
                    content=ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=GOLD),
                ),
                ft.Container(expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_money(self) -> ft.Control:
        return ft.Column(
            [
                self._back_bar("Money"),
                self.active_chip,
                ft.Row(
                    [
                        self.amount_field,
                        ft.FilledButton(
                            "Set money",
                            bgcolor=GREEN_HI,
                            color=BTN_ON_GREEN,
                            on_click=lambda _e: self.on_set(),
                        ),
                        ft.FilledButton(
                            "Add money",
                            bgcolor=GREEN,
                            color=BTN_ON_GREEN,
                            on_click=lambda _e: self.on_add(),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            spacing=12,
            tight=True,
        )

    def _vitality_cell(self, icon: str, field: ft.TextField) -> ft.Control:
        return ft.Container(
            content=ft.Row(
                [
                    self._gold_icon(icon, size=22),
                    field,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
        )

    def _build_vitality(self) -> ft.Control:
        return ft.Column(
            [
                self._back_bar("Vitality"),
                self.active_chip,
                ft.Row(
                    [
                        self._vitality_cell("heart", self.health_field),
                        self._vitality_cell("shield", self.armour_field),
                    ],
                    spacing=12,
                ),
                ft.Row(
                    [
                        self._vitality_cell("heart", self.max_health_field),
                        self._vitality_cell("shield", self.max_armour_field),
                    ],
                    spacing=12,
                ),
                ft.Row(
                    [
                        ft.OutlinedButton(
                            "Max health",
                            style=ft.ButtonStyle(
                                color=GOLD, side=ft.BorderSide(1.5, GOLD)
                            ),
                            tooltip=f"Set max health to {UI_MAX_CLAMP}",
                            on_click=lambda _e: self._vitality_max_health(),
                        ),
                        ft.OutlinedButton(
                            "Max armour",
                            style=ft.ButtonStyle(
                                color=GOLD, side=ft.BorderSide(1.5, GOLD)
                            ),
                            tooltip=f"Set max armour to {UI_MAX_CLAMP}",
                            on_click=lambda _e: self._vitality_max_armour(),
                        ),
                        ft.OutlinedButton(
                            "Tank",
                            style=ft.ButtonStyle(
                                color=GOLD, side=ft.BorderSide(1.5, GOLD)
                            ),
                            tooltip=f"Set all four fields to {UI_MAX_CLAMP}",
                            on_click=lambda _e: self._vitality_tank(),
                        ),
                        ft.Container(expand=True),
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
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=12,
            tight=True,
        )

    def _build_settings(self) -> ft.Control:
        return ft.Column(
            [
                self._back_bar("Settings"),
                self.autobackup,
                self.also_autosave,
                ft.Divider(color=OUTLINE, height=16),
                ft.Text("Writes", color=GOLD, weight=ft.FontWeight.W_600),
                ft.Text(
                    "PlayerInfo (money, weapons, vitality) and Block 4 Garages. "
                    "Unsupported save versions are blocked.",
                    color=MUTED,
                    size=13,
                ),
                ft.FilledButton(
                    "Change save",
                    bgcolor=GREEN_HI,
                    color=BTN_ON_GREEN,
                    on_click=lambda _e: self._goto("gate"),
                ),
            ],
            spacing=10,
            tight=True,
        )

    def _build_garage(self) -> ft.Control:
        self.garage_house_dd = ft.Dropdown(
            label="Safehouse",
            options=[
                ft.DropdownOption(key=s.id, text=s.name) for s in SAFEHOUSES
            ],
            value=self._garage_safehouse,
            on_select=lambda _e: self._on_garage_house(),
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
            expand=True,
        )
        self.garage_slots_col = ft.Column(spacing=8, tight=True)
        return ft.Column(
            [
                self._back_bar("Garage"),
                self.active_chip,
                self.garage_house_dd,
                self.garage_slots_col,
                ft.Row(
                    [
                        ft.FilledButton(
                            "Reload",
                            bgcolor=PANEL,
                            color=GOLD,
                            style=ft.ButtonStyle(side=ft.BorderSide(1, GOLD)),
                            on_click=lambda _e: self._load_garage_into_ui(),
                        ),
                        ft.Container(expand=True),
                        ft.Text(
                            "Spawn fills a free parking spot",
                            color=MUTED,
                            size=11,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=10,
            tight=True,
            expand=True,
        )

    # --- weapons UI ---

    def _slot_card(self, index: int) -> ft.Container:
        name_lbl = ft.Text("Empty", size=13, weight=ft.FontWeight.W_600, color=FG)
        badge = ft.Text("", size=10, color=MUTED)
        ammo = ft.TextField(
            label="Ammo",
            value="0",
            width=78,
            height=36,
            text_size=12,
            dense=True,
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            label_style=ft.TextStyle(color=MUTED, size=10),
            text_style=ft.TextStyle(color=FG, size=12),
            cursor_color=FOCUS,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        )
        self._slot_name_labels.append(name_lbl)
        self._slot_badge_labels.append(badge)
        self._ammo_fields.append(ammo)

        card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(f"#{index}", size=11, color=MUTED),
                            name_lbl,
                            ft.Container(expand=True),
                            badge,
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            ft.OutlinedButton(
                                "Pick",
                                height=30,
                                style=ft.ButtonStyle(
                                    color=GOLD,
                                    side=ft.BorderSide(1, GOLD),
                                    padding=ft.Padding.symmetric(horizontal=10, vertical=0),
                                ),
                                on_click=lambda _e, i=index: self._open_weapon_picker(i),
                            ),
                            ft.Container(expand=True),
                            ammo,
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=6,
                tight=True,
            ),
            bgcolor=PANEL,
            border=ft.Border.all(1.5, OUTLINE),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            expand=True,
            height=72,
            ink=True,
            on_click=lambda _e, i=index: self._mark_equipped(i),
        )
        self._slot_cards.append(card)
        return card

    def _mark_equipped(self, index: int) -> None:
        self._equipped_slot = index
        self._paint_equipped()
        self.page.update()

    def _paint_equipped(self) -> None:
        for i, card in enumerate(self._slot_cards):
            card.border = ft.Border.all(
                2 if i == self._equipped_slot else 1.5,
                GOLD if i == self._equipped_slot else OUTLINE,
            )

    def _build_weapons(self) -> ft.Control:
        self._ammo_fields = []
        self._slot_name_labels = []
        self._slot_badge_labels = []
        self._slot_cards = []
        rows: list[ft.Control] = []
        for r in range(5):
            rows.append(
                ft.Row(
                    [self._slot_card(r * 2), self._slot_card(r * 2 + 1)],
                    spacing=10,
                )
            )
        grid = ft.Column(rows, spacing=6, tight=True)
        return ft.Column(
            [
                self._back_bar("Weapons"),
                self.active_chip,
                grid,
                ft.Row(
                    [
                        ft.FilledButton(
                            "Reload",
                            bgcolor=GREEN,
                            color=BTN_ON_GREEN,
                            on_click=lambda _e: self._load_weapons_into_ui(),
                        ),
                        ft.FilledButton(
                            "Apply",
                            bgcolor=GREEN_HI,
                            color=BTN_ON_GREEN,
                            on_click=lambda _e: self._apply_weapons(),
                        ),
                        ft.OutlinedButton(
                            "Max ammo",
                            style=ft.ButtonStyle(color=GOLD, side=ft.BorderSide(1, GOLD)),
                            on_click=lambda _e: self._max_ammo(),
                        ),
                        ft.OutlinedButton(
                            "Clear empty",
                            style=ft.ButtonStyle(color=MUTED, side=ft.BorderSide(1, OUTLINE)),
                            on_click=lambda _e: self._clear_empty_slots(),
                        ),
                    ],
                    spacing=8,
                    wrap=True,
                ),
            ],
            spacing=8,
            tight=True,
        )

    def _open_weapon_picker(self, index: int) -> None:
        self._picker_slot = index
        search = ft.TextField(
            label="Search",
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
            cursor_color=FOCUS,
        )
        list_col = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, height=280)
        custom = ft.TextField(
            label="Custom / mod ID",
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
            cursor_color=FOCUS,
            tooltip="Use for mod weapons not in the stock list",
        )

        def fill(query: str = "") -> None:
            list_col.controls.clear()
            q = (query or "").lower().strip()
            stock_ids = {wid for _, wid in picker_options("all")}
            for label, wid in picker_options("all"):
                if q and q not in label.lower() and q not in str(wid):
                    continue

                def pick(_e: ft.ControlEvent, w: int = wid) -> None:
                    self._apply_picked_weapon(w)
                    self.page.pop_dialog()

                list_col.controls.append(
                    ft.ListTile(
                        title=ft.Text(label, color=FG, size=13),
                        dense=True,
                        on_click=pick,
                    )
                )
            # Named mod weapons from the selected GTA IV install.
            for wid, name in sorted(self._mod_names.items()):
                if wid in stock_ids:
                    continue
                label = f"{name}  ·  {wid}  ·  mod"
                if q and q not in label.lower() and q not in str(wid):
                    continue

                def pick_mod(_e: ft.ControlEvent, w: int = wid) -> None:
                    self._apply_picked_weapon(w)
                    self.page.pop_dialog()

                list_col.controls.append(
                    ft.ListTile(
                        title=ft.Text(label, color=GOLD, size=13),
                        dense=True,
                        on_click=pick_mod,
                    )
                )
            if not list_col.controls:
                list_col.controls.append(
                    ft.Text(
                        "No matches — enter a custom / mod ID below.",
                        color=MUTED,
                        size=12,
                    )
                )
            self.page.update()

        def on_search(_e: ft.ControlEvent) -> None:
            fill(search.value or "")

        def use_custom(_e: ft.ControlEvent) -> None:
            raw = (custom.value or "").strip()
            try:
                wid = int(raw, 0)
            except ValueError:
                self._alert(APP_NAME, "Enter a valid custom weapon ID.", error=True)
            return
            self._apply_picked_weapon(wid)
            self.page.pop_dialog()

        fill()
        search.on_change = on_search

        def close(_e: ft.ControlEvent) -> None:
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Slot {index} weapon", color=GOLD),
                bgcolor=PANEL,
                content=ft.Column(
                    [search, list_col, custom],
                    tight=True,
                    spacing=8,
                    width=360,
                ),
                actions=[
                    ft.TextButton(
                        "Use ID",
                        on_click=use_custom,
                        style=ft.ButtonStyle(color=GOLD),
                    ),
                    ft.TextButton(
                        "Cancel", on_click=close, style=ft.ButtonStyle(color=MUTED)
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _apply_picked_weapon(self, wid: int) -> None:
        idx = self._picker_slot
        if idx is None or idx < 0 or idx >= WEAPON_SLOT_COUNT:
            return
        self._weapon_ids[idx] = wid
        if wid == 0 and idx < len(self._ammo_fields):
            self._ammo_fields[idx].value = "0"
        self._sync_weapon_card_labels()
        self.page.update()

    def _sync_weapon_card_labels(self) -> None:
        for i in range(min(len(self._slot_name_labels), WEAPON_SLOT_COUNT)):
            wid = self._weapon_ids[i]
            det = classify_weapon(wid, mod_names=self._mod_names)
            if wid == 0:
                self._slot_name_labels[i].value = "Empty"
                self._slot_badge_labels[i].value = ""
                if i < len(self._ammo_fields):
                    self._ammo_fields[i].value = "0"
                    self._ammo_fields[i].disabled = True
            else:
                self._slot_name_labels[i].value = (
                    short_name(wid) if det.kind == "stock" else det.name
                )
                self._slot_badge_labels[i].value = det.kind
                if i < len(self._ammo_fields):
                    self._ammo_fields[i].disabled = False
            self._slot_badge_labels[i].color = (
                GREEN_HI
                if det.kind == "stock"
                else (GOLD if det.kind == "mod" else MUTED)
            )
        self._paint_equipped()

    def _load_weapons_into_ui(self) -> None:
        slot = self.active_slot
        if slot is None or slot.error:
            return
        if not self._slot_name_labels:
            return
        try:
            loadout = read_loadout_file(slot.path)
        except Exception as e:
            self.set_status(f"Loadout read failed: {e}")
            return
        self._weapon_ids = list(loadout.weapon_ids)
        self._equipped_slot = int(loadout.current_slot) if loadout.current_slot < WEAPON_SLOT_COUNT else 0
        for i, ammo_f in enumerate(self._ammo_fields):
            # Empty slots never show/store ammo
            ammo_f.value = "0" if self._weapon_ids[i] == 0 else str(loadout.ammo[i])
        self._sync_weapon_card_labels()
        self.page.update()

    def _collect_weapons(self) -> tuple[list[int], list[int]] | None:
        while len(self._weapon_ids) < WEAPON_SLOT_COUNT:
            self._weapon_ids.append(0)
        ammo: list[int] = []
        for i, ammo_f in enumerate(self._ammo_fields):
            if self._weapon_ids[i] == 0:
                ammo.append(0)
                ammo_f.value = "0"
                continue
            raw = (ammo_f.value or "0").strip()
            try:
                a = int(raw)
            except ValueError:
                self._alert(APP_NAME, f"Slot {i}: ammo must be a whole number.", error=True)
            return None
            if a < 0 or a > 0xFFFF:
                self._alert(APP_NAME, f"Slot {i}: ammo must be 0..65535.", error=True)
                return None
            ammo.append(a)
        return list(self._weapon_ids[:WEAPON_SLOT_COUNT]), ammo

    def _max_ammo(self) -> None:
        for i, f in enumerate(self._ammo_fields):
            if i < len(self._weapon_ids) and self._weapon_ids[i] != 0:
                f.value = "9999"
            else:
                f.value = "0"
        self.page.update()

    def _clear_empty_slots(self) -> None:
        for i in range(WEAPON_SLOT_COUNT):
            if self._weapon_ids[i] == 0 and i < len(self._ammo_fields):
                self._ammo_fields[i].value = "0"
        self._sync_weapon_card_labels()
        self.page.update()

    def _apply_weapons(self) -> None:
        slot = self.active_slot
        if slot is None:
            self._alert(APP_NAME, "Select a save first.", error=True)
            return
        if not self._gate_write(slot):
            return
        collected = self._collect_weapons()
        if collected is None:
            return
        weapons, ammo = collected

        def go() -> None:
            self._write_weapons_paths(
                self.targets_for(slot), weapons, ammo, current_slot=self._equipped_slot
            )

        self._confirm_paths_generic(slot, go)

    def _write_weapons_paths(
        self,
        paths: list[Path],
        weapons: list[int],
        ammo: list[int],
        *,
        current_slot: int | None = None,
    ) -> None:
        lines: list[str] = []
        try:
            for path in paths:
                allow_non_ce = "Non-CE" in check_write(path, allow_non_ce_path=False).reason
                old, new, bak, _c = write_loadout(
                    path,
                    weapons,
                    ammo,
                    current_slot=current_slot,
                    backup=bool(self.autobackup.value),
                    allow_non_ce_path=allow_non_ce,
                    app_base=Path.cwd(),
                )
                lines.append(
                    f"{path.name}: {sum(1 for w in old.weapon_ids if w)} → "
                    f"{sum(1 for w in new.weapon_ids if w)} armed"
                )
                if bak:
                    lines.append(f"  backup: {bak.beside.name}")
            self._load_weapons_into_ui()
            self.set_status(" | ".join(lines))
            self._alert(APP_NAME, "Loadout updated.\n\n" + "\n".join(lines))
        except Exception as e:
            self._alert(APP_NAME, str(e), error=True)

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
        slot = self.active_slot
        amount = self.parse_amount()
        if slot is None or amount is None or not self._gate_write(slot):
            if slot is None:
                self._alert(APP_NAME, "Select a save first.", error=True)
            return
        if mode == "set" and amount > 100_000_000:
            self._confirm(
                APP_NAME,
                f"Set money to ${amount:,}?\n\nVery large values can look odd in-game.",
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
            self._do_money(mode, paths, amount)
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

    def _do_money(self, mode: str, paths: list[Path], amount: int) -> None:
        lines: list[str] = []
        try:
            for path in paths:
                allow_non_ce = "Non-CE" in check_write(path, allow_non_ce_path=False).reason
                fn = set_money if mode == "set" else add_money
                old, new, bak, _c = fn(
                    path,
                    amount,
                    backup=bool(self.autobackup.value),
                    allow_non_ce_path=allow_non_ce,
                    app_base=Path.cwd(),
                )
                lines.append(f"{path.name}: ${old:,} → ${new:,}")
                if bak:
                    lines.append(f"  backup: {bak.beside.name}")
            self.set_status(" | ".join(lines))
            self._alert(APP_NAME, "Money updated.\n\n" + "\n".join(lines))
            self._refresh_active_chip()
            self.page.update()
        except Exception as e:
            self._alert(APP_NAME, str(e), error=True)

    # --- garage ---

    def _on_garage_house(self) -> None:
        self._garage_safehouse = self.garage_house_dd.value or SAFEHOUSES[0].id
        self._refresh_garage_slots()
        self.page.update()

    def _load_garage_into_ui(self) -> None:
        slot = self.active_slot
        if slot is None or slot.error:
            return
        if not hasattr(self, "garage_slots_col"):
            return
        try:
            cars = read_stored_cars_file(slot.path)
        except Exception as e:
            self.set_status(f"Garage read failed: {e}")
            return
        self._garage_draft = list(cars)
        self._refresh_garage_slots()
        self.page.update()

    def _refresh_garage_slots(self) -> None:
        if not hasattr(self, "garage_slots_col"):
            return
        sid = self._garage_safehouse
        try:
            raw = (
                self.active_slot.path.read_bytes()
                if self.active_slot and not self.active_slot.error
                else b""
            )
            spots = [s for s in list_safehouse_slots(raw) if s.safehouse_id == sid] if raw else []
        except Exception as e:
            self.garage_slots_col.controls = [
                ft.Text(f"Could not read garages: {e}", color=ERROR)
            ]
            return
        cards: list[ft.Control] = []
        for spot in spots:
            cards.append(self._garage_spot_card(spot.spot_index, spot))
        if not cards:
            cards.append(ft.Text("No parking spots for this safehouse.", color=MUTED))
        self.garage_slots_col.controls = cards

    def _garage_spot_card(self, spot_i: int, spot) -> ft.Control:
        car = spot.car
        install = self.active_install
        if car and car.valid:
            title = vehicle_name(car.model, install)
            colors = ",".join(str(c) for c in car.colors)
            body = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                f"Spot {spot_i + 1}: {title}",
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=FG,
                            ),
                            ft.Container(expand=True),
                            ft.Text(f"#{car.model}", size=11, color=MUTED),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(f"Colors {colors} · Livery {car.livery}", size=11, color=MUTED),
                    ft.Row(
                        [
                            ft.OutlinedButton(
                                "Change",
                                height=30,
                                style=ft.ButtonStyle(
                                    color=GOLD, side=ft.BorderSide(1, GOLD)
                                ),
                                on_click=lambda _e, si=spot_i: self._open_vehicle_picker(
                                    "edit", si, car_index=car.index
                                ),
                            ),
                            ft.OutlinedButton(
                                "Clear",
                                height=30,
                                style=ft.ButtonStyle(
                                    color=ERROR, side=ft.BorderSide(1, ERROR)
                                ),
                                on_click=lambda _e, idx=car.index: self._garage_clear(idx),
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=4,
                tight=True,
            )
        else:
            body = ft.Column(
                [
                    ft.Text(
                        f"Spot {spot_i + 1}: Empty",
                        size=13,
                        weight=ft.FontWeight.W_600,
                        color=MUTED,
                    ),
                    ft.OutlinedButton(
                        "Spawn",
                        height=30,
                        style=ft.ButtonStyle(color=GOLD, side=ft.BorderSide(1, GOLD)),
                        on_click=lambda _e, si=spot_i: self._open_vehicle_picker(
                            "spawn", si
                        ),
                    ),
                ],
                spacing=6,
                tight=True,
            )
        return ft.Container(
            content=body,
            bgcolor=PANEL,
            border=ft.Border.all(1.5, OUTLINE),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
        )

    def _open_vehicle_picker(
        self, mode: str, spot_index: int, *, car_index: int | None = None
    ) -> None:
        self._vehicle_picker_mode = mode
        self._vehicle_picker_spot = (self._garage_safehouse, spot_index)
        self._vehicle_picker_car_index = car_index
        vehicles = list_vehicles(self.active_install)
        options = [
            ft.DropdownOption(key=str(i), text=f"{name}  [{i}]") for i, name in vehicles
        ]
        dd = ft.Dropdown(
            label="Vehicle",
            options=options[:400],
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
            expand=True,
        )
        idx_field = ft.TextField(
            label="Model index",
            value="",
            width=120,
            border_color=GREEN_HI,
            focused_border_color=FOCUS,
            label_style=ft.TextStyle(color=MUTED),
            text_style=ft.TextStyle(color=FG),
        )

        def close(_e=None) -> None:
            self.page.pop_dialog()

        def apply(_e=None) -> None:
            raw = (dd.value or idx_field.value or "").strip()
            if dd.value:
                raw = dd.value.strip()
            try:
                mid = int(raw)
            except ValueError:
                self._alert(APP_NAME, "Pick a vehicle or enter a model index.", error=True)
                return
            if mid <= 0:
                self._alert(APP_NAME, "Model index must be positive.", error=True)
                return
            close()
            if mode == "spawn":
                self._garage_spawn(mid)
            else:
                if car_index is None:
                    return
                self._garage_change_model(car_index, mid)

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Pick vehicle", color=GOLD),
                content=ft.Column(
                    [dd, idx_field],
                    tight=True,
                    spacing=10,
                    width=420,
                    height=140,
                ),
                actions=[
                    ft.TextButton(
                        "Cancel", on_click=close, style=ft.ButtonStyle(color=MUTED)
                    ),
                    ft.FilledButton(
                        "OK",
                        bgcolor=GREEN_HI,
                        color=BTN_ON_GREEN,
                        on_click=apply,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _garage_clear(self, car_index: int) -> None:
        slot = self.active_slot
        if slot is None or not self._gate_write(slot):
            return

        def go() -> None:
            try:
                allow = "Non-CE" in check_write(slot.path, allow_non_ce_path=False).reason
                update_stored_car(
                    slot.path,
                    car_index,
                    clear=True,
                    backup=bool(self._settings.get("autobackup", True)),
                    allow_non_ce_path=allow,
                )
                for p in self.targets_for(slot)[1:]:
                    update_stored_car(
                        p,
                        car_index,
                        clear=True,
                        backup=False,
                        allow_non_ce_path=True,
                    )
                self.set_status(f"Cleared garage slot {car_index}")
                self._load_garage_into_ui()
            except Exception as e:
                self._alert(APP_NAME, str(e), error=True)

        self._confirm_paths_generic(slot, go)

    def _garage_change_model(self, car_index: int, model: int) -> None:
        slot = self.active_slot
        if slot is None or not self._gate_write(slot):
            return

        def go() -> None:
            try:
                allow = "Non-CE" in check_write(slot.path, allow_non_ce_path=False).reason
                update_stored_car(
                    slot.path,
                    car_index,
                    model=model,
                    backup=bool(self._settings.get("autobackup", True)),
                    allow_non_ce_path=allow,
                )
                for p in self.targets_for(slot)[1:]:
                    update_stored_car(
                        p,
                        car_index,
                        model=model,
                        backup=False,
                        allow_non_ce_path=True,
                    )
                self.set_status(
                    f"Slot {car_index} → {vehicle_name(model, self.active_install)}"
                )
                self._load_garage_into_ui()
            except Exception as e:
                self._alert(APP_NAME, str(e), error=True)

        self._confirm_paths_generic(slot, go)

    def _garage_spawn(self, model: int) -> None:
        slot = self.active_slot
        if slot is None or not self._gate_write(slot):
            return
        sid = self._garage_safehouse

        def go() -> None:
            try:
                allow = "Non-CE" in check_write(slot.path, allow_non_ce_path=False).reason
                new, _, _ = spawn_at_safehouse(
                    slot.path,
                    sid,
                    model=model,
                    flags=proofs_to_flags(valid=True),
                    backup=bool(self._settings.get("autobackup", True)),
                    allow_non_ce_path=allow,
                )
                for p in self.targets_for(slot)[1:]:
                    try:
                        spawn_at_safehouse(
                            p,
                            sid,
                            model=model,
                            flags=FLAG_VALID,
                            backup=False,
                            allow_non_ce_path=True,
                        )
                    except RuntimeError:
                        pass
                self.set_status(
                    f"Spawned {vehicle_name(new.model, self.active_install)} at {sid}"
                )
                self._load_garage_into_ui()
            except Exception as e:
                self._alert(APP_NAME, str(e), error=True)

        self._confirm_paths_generic(slot, go)

    # --- vitality ---

    def _load_vitality_into_ui(self) -> None:
        slot = self.active_slot
        if slot is None or slot.error:
            return
        try:
            v = read_vitality_file(slot.path)
        except Exception as e:
            self.set_status(f"Vitality read failed: {e}")
            return
        self.health_field.value = f"{v.health:.1f}"
        self.armour_field.value = f"{v.armour:.1f}"
        self.max_health_field.value = str(v.max_health)
        self.max_armour_field.value = str(v.max_armour)
        self.page.update()

    def _vitality_max_health(self) -> None:
        self.max_health_field.value = str(UI_MAX_CLAMP)
        self.page.update()

    def _vitality_max_armour(self) -> None:
        self.max_armour_field.value = str(UI_MAX_CLAMP)
        self.page.update()

    def _vitality_tank(self) -> None:
        """Set current and maxima health/armour to the game max dword."""
        cap = str(UI_MAX_CLAMP)
        self.health_field.value = cap
        self.armour_field.value = cap
        self.max_health_field.value = cap
        self.max_armour_field.value = cap
        self.page.update()

    def _apply_vitality(self) -> None:
        slot = self.active_slot
        if slot is None or not self._gate_write(slot):
            if slot is None:
                self._alert(APP_NAME, "Select a save first.", error=True)
            return
        try:
            health = float((self.health_field.value or "0").strip())
            armour = float((self.armour_field.value or "0").strip())
            max_health = int((self.max_health_field.value or "0").strip())
            max_armour = int((self.max_armour_field.value or "0").strip())
        except ValueError:
            self._alert(APP_NAME, "Enter valid numbers for vitality fields.", error=True)
            return
        if not (0 <= max_health <= UI_MAX_CLAMP and 0 <= max_armour <= UI_MAX_CLAMP):
            self._alert(APP_NAME, f"Max health/armour must be 0..{UI_MAX_CLAMP}.", error=True)
            return

        def go() -> None:
            self._write_vitality_paths(
                self.targets_for(slot), health, armour, max_health, max_armour
            )

        if health > UI_CLAMP_MAX or armour > UI_CLAMP_MAX:
            self._confirm(
                APP_NAME,
                f"Values above {UI_CLAMP_MAX:g} may behave oddly in-game. Continue?",
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
        lines: list[str] = []
        try:
            for path in paths:
                allow_non_ce = "Non-CE" in check_write(path, allow_non_ce_path=False).reason
                old, new, bak, _c = set_vitality(
                    path,
                    health,
                    armour,
                    max_health,
                    max_armour,
                    backup=bool(self.autobackup.value),
                    allow_non_ce_path=allow_non_ce,
                    app_base=Path.cwd(),
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
    assets = str(_resource_path("assets"))
    ft.run(main, assets_dir=assets if Path(assets).is_dir() else None)


if __name__ == "__main__":
    run()
