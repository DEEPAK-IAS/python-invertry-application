"""
Design tokens — the single source of truth for the app's visual language.

This module contains NO business logic and NO Qt imports beyond what's
needed to describe sizes. It only describes numbers and colors. The QSS
theme files (ui/themes/dark.qss, ui/themes/light.qss) are generated from
these tokens by app/design/qss_builder.py — so changing a size or color
here changes it everywhere, instead of hunting through per-window styling.

Do NOT hardcode pixel sizes, colors, or font weights anywhere else in the
UI code. If a new value is needed, add it here first.
"""
from __future__ import annotations
from dataclasses import dataclass, field


# ─────────────────────────────────────────
# Spacing scale (px) — use these instead of magic numbers
# ─────────────────────────────────────────
class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


# ─────────────────────────────────────────
# Corner radius scale (px)
# ─────────────────────────────────────────
class Radius:
    SM = 6
    MD = 8
    LG = 12
    PILL = 999


# ─────────────────────────────────────────
# Typography scale (px). All widgets should reference these instead of
# calling font.setPointSize()/setBold() individually.
# ─────────────────────────────────────────
class FontSize:
    CAPTION = 13
    BODY = 16
    BODY_LARGE = 17
    LABEL = 16
    SUBTITLE = 18
    NAV = 20
    TITLE = 22
    HEADING = 26
    DISPLAY = 34


class FontWeight:
    REGULAR = 400
    MEDIUM = 500
    SEMIBOLD = 600
    BOLD = 700

FONT_FAMILY = "Poppins"
FONT_FAMILY_FALLBACK = '"Poppins", "Segoe UI", Arial, sans-serif'


# ─────────────────────────────────────────
# Component sizing contract.
# Every button/icon in the app must use ONE of these variants so that
# icon size never exceeds button size and text never gets clipped.
# ─────────────────────────────────────────
class ButtonSize:
    # (height_px, h_padding_px, icon_px, font_px)
    SMALL       = dict(height=32, padding=13, icon=15, font=FontSize.BODY)
    MEDIUM      = dict(height=42, padding=18, icon=18, font=FontSize.BODY_LARGE)
    LARGE       = dict(height=50, padding=22, icon=20, font=FontSize.SUBTITLE)
    NAV         = dict(height=54, padding=18, icon=20, font=FontSize.NAV)
    TABLE_ACTION = dict(height=34, width=34, icon=17)   # square icon-only button


class InputSize:
    HEIGHT = 44
    PADDING_H = 12


class TableSize:
    ROW_MIN_HEIGHT = 48
    HEADER_HEIGHT = 46
    CELL_PADDING_H = 10
    CELL_PADDING_V = 9


SIDEBAR_WIDTH = 260
TOPBAR_HEIGHT = 72


# ─────────────────────────────────────────
# Color palettes. Two full palettes (dark / light), same key names,
# so the QSS builder can stay theme-agnostic.
# ─────────────────────────────────────────
@dataclass(frozen=True)
class Palette:
    # Surfaces
    bg: str
    surface: str          # cards / panels
    surface_alt: str      # sidebar / topbar
    surface_raised: str   # hovered card
    border: str
    border_strong: str

    # Text
    text: str
    text_muted: str
    text_on_accent: str
    text_on_dark_surface: str = "#ffffff"

    # Brand / accent
    accent: str = "#4f7cff"
    accent_hover: str = "#3d68f0"
    accent_pressed: str = "#2f56d6"

    # Semantic
    success: str = "#2fb673"
    success_bg: str = "rgba(47,182,115,0.12)"
    warning: str = "#e2932c"
    warning_bg: str = "rgba(226,147,44,0.12)"
    danger: str = "#e5484d"
    danger_bg: str = "rgba(229,72,77,0.12)"
    info: str = "#4f7cff"
    info_bg: str = "rgba(79,124,255,0.12)"

    # Table specific (explicit — this is what fixes the hover/focus bug)
    row_bg: str = ""
    row_alt_bg: str = ""
    row_hover_bg: str = ""
    row_hover_text: str = ""
    row_selected_bg: str = ""
    row_selected_text: str = ""
    row_selected_inactive_bg: str = ""   # selected but window not focused
    row_selected_inactive_text: str = ""
    header_bg: str = ""
    header_text: str = ""

    # Icon tint (neutral, theme-aware — used by icon_manager)
    icon_color: str = ""
    icon_color_muted: str = ""
    icon_color_on_accent: str = "#ffffff"


DARK = Palette(
    bg="#15161e",
    surface="#1c1e29",
    surface_alt="#12131a",
    surface_raised="#232534",
    border="#2b2d3c",
    border_strong="#3a3d52",

    text="#e7e8f0",
    text_muted="#9799ab",
    text_on_accent="#ffffff",

    accent="#5b7fff",
    accent_hover="#4b6bef",
    accent_pressed="#3a58d6",

    row_bg="#1c1e29",
    row_alt_bg="#20222f",
    row_hover_bg="#2a2d3f",
    row_hover_text="#ffffff",
    row_selected_bg="#3d4a7a",
    row_selected_text="#ffffff",
    row_selected_inactive_bg="#2c2f45",
    row_selected_inactive_text="#e7e8f0",
    header_bg="#171821",
    header_text="#a6b1ff",

    icon_color="#c3c5d6",
    icon_color_muted="#71738a",
)

LIGHT = Palette(
    bg="#f5f6fa",
    surface="#ffffff",
    surface_alt="#ffffff",
    surface_raised="#f0f2fa",
    border="#e2e4ee",
    border_strong="#c9cce0",

    text="#1c1e2b",
    text_muted="#666a80",
    text_on_accent="#ffffff",

    accent="#3d63ea",
    accent_hover="#3153cc",
    accent_pressed="#2745ac",

    row_bg="#ffffff",
    row_alt_bg="#f7f8fc",
    row_hover_bg="#eef1fd",
    row_hover_text="#1c1e2b",
    row_selected_bg="#dbe4ff",
    row_selected_text="#152159",
    row_selected_inactive_bg="#eceffb",
    row_selected_inactive_text="#1c1e2b",
    header_bg="#eef0f8",
    header_text="#3d4360",

    icon_color="#4b4f66",
    icon_color_muted="#9497ab",
)

PALETTES = {"dark": DARK, "light": LIGHT}
