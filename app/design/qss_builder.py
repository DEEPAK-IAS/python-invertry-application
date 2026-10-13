"""
Builds a complete QSS stylesheet string from a Palette + the shared sizing
tokens. Both themes are generated from this ONE template, so dark/light
can never drift out of structural sync with each other (only colors
differ) and every selector is defined exactly once — no more duplicate/
contradictory blocks like the old hand-written QSS files had.

Usage:
    from app.design.qss_builder import build_stylesheet
    from app.design.tokens import DARK
    qss_text = build_stylesheet(DARK)

Regenerating the on-disk .qss files (optional — ThemeManager can also
build in memory) is done by scripts/generate_themes.py.
"""
from __future__ import annotations
from app.design.tokens import (
    Palette, Spacing, Radius, FontSize, ButtonSize, InputSize,
    TableSize, SIDEBAR_WIDTH, TOPBAR_HEIGHT, FONT_FAMILY_FALLBACK,
)


def build_stylesheet(p: Palette) -> str:
    btn_md = ButtonSize.MEDIUM
    btn_sm = ButtonSize.SMALL
    btn_lg = ButtonSize.LARGE
    btn_nav = ButtonSize.NAV
    btn_tbl = ButtonSize.TABLE_ACTION

    return f"""
/* ══════════════════════════════════════════════════════════
   Generated from app/design/tokens.py — do not hand-edit values
   here; change the tokens and regenerate instead.
   ══════════════════════════════════════════════════════════ */

* {{
    font-family: {FONT_FAMILY_FALLBACK};
}}

QMainWindow, QWidget {{
    background-color: {p.bg};
    color: {p.text};
    font-size: {FontSize.BODY}px;
}}

/* ── Sidebar ── */
#Sidebar {{
    background-color: {p.surface_alt};
    border-right: 1px solid {p.border};
    min-width: {SIDEBAR_WIDTH}px;
    max-width: {SIDEBAR_WIDTH}px;
}}

#SidebarTitle {{
    color: {p.accent};
    font-size: {FontSize.TITLE}px;
    font-weight: 700;
    padding: {Spacing.SM}px;
    background: transparent;
}}

#UserCard {{
    background-color: {p.surface_raised};
    border: 1px solid {p.border};
    border-radius: {Radius.MD}px;
}}
QLabel#UserName {{
    color: {p.text};
    font-size: {FontSize.LABEL}px;
    font-weight: 700;
    background: transparent;
}}
QLabel#UserHandle {{
    color: {p.text_muted};
    font-size: {FontSize.CAPTION}px;
    background: transparent;
}}

QPushButton#SidebarButton {{
    background-color: transparent;
    color: {p.text};
    border: none;
    border-radius: {Radius.MD}px;
    text-align: left;
    padding: 0px {btn_nav['padding']}px;
    min-height: {btn_nav['height']}px;
    font-size: {btn_nav['font']}px;
    font-weight: 600;
    icon-size: {btn_nav['icon']}px {btn_nav['icon']}px;
}}
QPushButton#SidebarButton:hover {{
    background-color: {p.surface_raised};
    color: {p.text};
}}
QPushButton#SidebarButton:checked {{
    background-color: {p.accent};
    color: {p.text_on_accent};
    font-weight: 700;
}}

/* ── Top bar ── */
#TopBar {{
    background-color: {p.surface_alt};
    border-bottom: 1px solid {p.border};
    min-height: {TOPBAR_HEIGHT}px;
}}
QLabel#TitleLabel {{
    font-size: {FontSize.HEADING}px;
    font-weight: 700;
    color: {p.text};
    background: transparent;
}}
QLabel#SubtitleLabel {{
    font-size: {FontSize.BODY}px;
    color: {p.text_muted};
    background: transparent;
}}
QLabel#PageTitle {{
    font-size: {FontSize.HEADING}px;
    font-weight: 700;
    color: {p.text};
    background: transparent;
}}
QLabel#SectionTitle {{
    font-size: {FontSize.TITLE}px;
    font-weight: 700;
    color: {p.text};
    background: transparent;
}}

/* ── Buttons (default = secondary variant) ── */
QPushButton {{
    background-color: {p.surface_raised};
    color: {p.text};
    border: 1px solid {p.border_strong};
    border-radius: {Radius.SM}px;
    min-height: {btn_md['height']}px;
    padding: 0px {btn_md['padding']}px;
    font-size: {btn_md['font']}px;
    font-weight: 600;
    icon-size: {btn_md['icon']}px {btn_md['icon']}px;
}}
QPushButton:hover {{
    background-color: {p.surface};
    border-color: {p.accent};
}}
QPushButton:pressed {{
    background-color: {p.border};
}}
QPushButton:disabled {{
    color: {p.text_muted};
    border-color: {p.border};
    background-color: transparent;
}}

QPushButton#PrimaryButton {{
    background-color: {p.accent};
    color: {p.text_on_accent};
    border: none;
    font-weight: 700;
}}
QPushButton#PrimaryButton:hover {{ background-color: {p.accent_hover}; }}
QPushButton#PrimaryButton:pressed {{ background-color: {p.accent_pressed}; }}
QPushButton#PrimaryButton:disabled {{ background-color: {p.border_strong}; color: {p.text_muted}; }}

QPushButton#DangerButton {{
    background-color: transparent;
    color: {p.danger};
    border: 1px solid {p.danger};
    font-weight: 700;
}}
QPushButton#DangerButton:hover {{ background-color: {p.danger}; color: #ffffff; }}
QPushButton#DangerButton:pressed {{ background-color: {p.danger}; color: #ffffff; }}

QPushButton#WarningButton {{
    background-color: transparent;
    color: {p.warning};
    border: 1px solid {p.warning};
    font-weight: 700;
}}
QPushButton#WarningButton:hover {{ background-color: {p.warning}; color: #ffffff; }}

QPushButton#SuccessButton {{
    background-color: transparent;
    color: {p.success};
    border: 1px solid {p.success};
    font-weight: 700;
}}
QPushButton#SuccessButton:hover {{ background-color: {p.success}; color: #ffffff; }}

QPushButton#SmallButton {{
    min-height: {btn_sm['height']}px;
    padding: 0px {btn_sm['padding']}px;
    font-size: {btn_sm['font']}px;
    icon-size: {btn_sm['icon']}px {btn_sm['icon']}px;
}}
QPushButton#LargeButton {{
    min-height: {btn_lg['height']}px;
    padding: 0px {btn_lg['padding']}px;
    font-size: {btn_lg['font']}px;
    icon-size: {btn_lg['icon']}px {btn_lg['icon']}px;
}}

#LinkButton {{
    background: transparent;
    color: {p.accent};
    border: none;
    font-size: {FontSize.BODY}px;
    text-decoration: underline;
    padding: 0px;
}}
#LinkButton:hover {{ color: {p.accent_hover}; background: transparent; }}

/* ── Table row-action icon buttons (edit/delete/view/print/pay) ── */
QToolButton#TableActionButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {Radius.SM}px;
    min-width: {btn_tbl['width']}px;
    max-width: {btn_tbl['width']}px;
    min-height: {btn_tbl['height']}px;
    max-height: {btn_tbl['height']}px;
    icon-size: {btn_tbl['icon']}px {btn_tbl['icon']}px;
    padding: 0px;
}}
QToolButton#TableActionButton:hover {{
    background-color: {p.surface_raised};
    border-color: {p.border_strong};
}}
QToolButton#TableActionButton:pressed {{
    background-color: {p.border};
}}
QToolButton#TableActionButton:disabled {{
    background-color: transparent;
}}

/* ── Inputs ── */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit {{
    background-color: {p.surface};
    color: {p.text};
    border: 1px solid {p.border_strong};
    border-radius: {Radius.SM}px;
    min-height: {InputSize.HEIGHT}px;
    padding: 0px {InputSize.PADDING_H}px;
    selection-background-color: {p.accent};
    selection-color: {p.text_on_accent};
}}
QTextEdit {{ padding: {Spacing.SM}px {InputSize.PADDING_H}px; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QTextEdit:focus, QDateEdit:focus {{
    border: 1.5px solid {p.accent};
}}
QLineEdit:disabled, QComboBox:disabled {{
    color: {p.text_muted};
    background-color: {p.surface_alt};
}}
QComboBox::drop-down {{ border: none; padding-right: {Spacing.SM}px; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {p.surface};
    color: {p.text};
    selection-background-color: {p.accent};
    selection-color: {p.text_on_accent};
    border: 1px solid {p.border_strong};
    outline: none;
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {p.surface_raised};
    border: none;
    border-radius: 3px;
    width: 18px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {p.accent};
}}

QLabel#FieldLabel {{
    font-size: {FontSize.BODY}px;
    color: {p.text_muted};
    font-weight: 600;
    background: transparent;
}}

/* ── Tables — every interaction state explicit (fixes hover/focus contrast) ── */
QTableWidget, QTableView {{
    background-color: {p.row_bg};
    alternate-background-color: {p.row_alt_bg};
    gridline-color: {p.border};
    border: 1px solid {p.border};
    border-radius: {Radius.MD}px;
    outline: none;
}}
QTableWidget::item, QTableView::item {{
    padding: {TableSize.CELL_PADDING_V}px {TableSize.CELL_PADDING_H}px;
    border: none;
    color: {p.text};
    background-color: transparent;
}}
QTableWidget::item:hover, QTableView::item:hover {{
    background-color: {p.row_hover_bg};
    color: {p.row_hover_text};
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {p.row_selected_bg};
    color: {p.row_selected_text};
}}
QTableWidget::item:selected:!active, QTableView::item:selected:!active {{
    background-color: {p.row_selected_inactive_bg};
    color: {p.row_selected_inactive_text};
}}
QHeaderView::section {{
    background-color: {p.header_bg};
    color: {p.header_text};
    padding: 0px {TableSize.CELL_PADDING_H}px;
    min-height: {TableSize.HEADER_HEIGHT}px;
    border: none;
    border-bottom: 2px solid {p.accent};
    font-weight: 700;
    font-size: {FontSize.BODY}px;
}}
QHeaderView::section:hover {{
    background-color: {p.surface_raised};
}}
QTableCornerButton::section {{
    background-color: {p.header_bg};
    border: none;
}}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {p.border};
    border-radius: {Radius.SM}px;
    background-color: {p.surface};
}}
QTabBar::tab {{
    background-color: {p.surface_raised};
    color: {p.text_muted};
    padding: {Spacing.SM}px {Spacing.LG}px;
    border-radius: {Radius.SM}px;
    margin-right: {Spacing.XS}px;
    margin-bottom: 2px;
    min-height: 28px;
}}
QTabBar::tab:selected {{
    background-color: {p.accent};
    color: {p.text_on_accent};
    font-weight: 700;
}}
QTabBar::tab:hover:!selected {{
    background-color: {p.border};
    color: {p.text};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background-color: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background-color: {p.border_strong};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background-color: {p.accent}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background-color: transparent;
    height: 10px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background-color: {p.border_strong};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background-color: {p.accent}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

/* ── Dialogs / message boxes ── */
QDialog {{ background-color: {p.bg}; }}
QDialogButtonBox QPushButton {{ min-width: 88px; }}
QMessageBox {{ background-color: {p.surface}; }}
QMessageBox QLabel {{ color: {p.text}; background: transparent; }}

/* ── Labels ── */
QLabel {{ color: {p.text}; background: transparent; }}

/* ── Stat / dashboard cards ── */
QFrame#StatCard {{
    background-color: {p.surface};
    border: 1px solid {p.border};
    border-radius: {Radius.LG}px;
}}
QFrame#StatCard:hover {{
    border-color: {p.accent};
    background-color: {p.surface_raised};
}}
QLabel#StatValue {{
    font-size: {FontSize.DISPLAY}px;
    font-weight: 700;
    color: {p.accent};
    background: transparent;
}}
QLabel#StatLabel {{
    font-size: {FontSize.CAPTION}px;
    color: {p.text_muted};
    background: transparent;
}}

/* ── Checkbox ── */
QCheckBox {{ color: {p.text}; spacing: {Spacing.SM}px; background: transparent; }}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 1.5px solid {p.border_strong};
    border-radius: 4px;
    background-color: {p.surface};
}}
QCheckBox::indicator:checked {{
    background-color: {p.accent};
    border-color: {p.accent};
}}

/* ── Menu ── */
QMenuBar {{ background-color: {p.surface_alt}; color: {p.text}; }}
QMenuBar::item:selected {{ background-color: {p.surface_raised}; }}
QMenu {{
    background-color: {p.surface};
    color: {p.text};
    border: 1px solid {p.border_strong};
}}
QMenu::item:selected {{ background-color: {p.accent}; color: {p.text_on_accent}; }}

/* ── Status bar ── */
QStatusBar {{
    background-color: {p.surface_alt};
    color: {p.text_muted};
    font-size: {FontSize.CAPTION}px;
    border-top: 1px solid {p.border};
}}

/* ── Tooltip ── */
QToolTip {{
    background-color: {p.surface_raised};
    color: {p.text};
    border: 1px solid {p.border_strong};
    border-radius: {Radius.SM}px;
    padding: {Spacing.XS}px {Spacing.SM}px;
}}

/* ── Login / Auth screen ── */
#LoginBrand {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p.accent}, stop:1 {p.accent_pressed});
}}
#LoginPanel {{ background-color: {p.bg}; }}
#AuthTitle {{ font-size: {FontSize.HEADING}px; font-weight: 700; color: {p.text}; background: transparent; }}
#AuthSubtitle {{ font-size: {FontSize.BODY}px; color: {p.text_muted}; background: transparent; }}
#ErrorLabel {{
    color: {p.danger}; font-size: {FontSize.BODY}px; padding: {Spacing.SM}px {Spacing.MD}px;
    background-color: {p.danger_bg}; border-radius: {Radius.SM}px;
    border: 1px solid {p.danger};
}}
#SuccessLabel {{
    color: {p.success}; font-size: {FontSize.BODY}px; padding: {Spacing.SM}px {Spacing.MD}px;
    background-color: {p.success_bg}; border-radius: {Radius.SM}px;
    border: 1px solid {p.success};
}}

/* ── Settings page cards ── */
#SettingsCard {{
    background-color: {p.surface};
    border: 1px solid {p.border};
    border-radius: {Radius.LG}px;
    padding: {Spacing.XL}px;
}}
#CardTitle {{
    font-size: {FontSize.TITLE}px;
    font-weight: 700;
    color: {p.text};
    background: transparent;
}}
#CardDescription {{
    font-size: {FontSize.BODY}px;
    color: {p.text_muted};
    background: transparent;
}}

/* ── Status pill (payment status, stock status, etc.) ── */
QLabel#StatusPillPaid, QLabel#StatusPillSuccess {{
    background-color: {p.success_bg}; color: {p.success};
    border-radius: {Radius.PILL}px; padding: 3px {Spacing.SM}px;
    font-weight: 700; font-size: {FontSize.CAPTION}px;
}}
QLabel#StatusPillPartial, QLabel#StatusPillWarning {{
    background-color: {p.warning_bg}; color: {p.warning};
    border-radius: {Radius.PILL}px; padding: 3px {Spacing.SM}px;
    font-weight: 700; font-size: {FontSize.CAPTION}px;
}}
QLabel#StatusPillUnpaid, QLabel#StatusPillDanger {{
    background-color: {p.danger_bg}; color: {p.danger};
    border-radius: {Radius.PILL}px; padding: 3px {Spacing.SM}px;
    font-weight: 700; font-size: {FontSize.CAPTION}px;
}}
""".strip() + "\n"
