# Refactor Changelog

Scope: UI/UX design system, icon system, table styling, pending-bills
workflow, customer purchase history. No business logic, calculations,
database schema, or service behavior was changed.

## 1. New design system (app/design/)
- `tokens.py` — single source of truth for spacing, radius, font sizes,
  button-size variants, and full dark/light color palettes (including
  explicit table hover/selected/selected-inactive colors).
- `qss_builder.py` — generates the complete stylesheet for either theme
  from those tokens. No more duplicate/contradictory QSS blocks (the old
  `dark.qss`/`light.qss` had `#SettingsCard` and `#Sidebar` each defined
  twice with conflicting values — one of them made settings cards render
  pure black in dark mode).
- `icons.py` — theme-aware icon system built on `qtawesome` (bundles its
  own icon fonts, no missing-asset risk), with a Qt-standard-icon
  fallback and a live refresh registry so open windows recolor icons on
  theme toggle.
- `ui/themes/dark.qss` / `light.qss` are now *generated reference copies*
  (via `scripts/generate_themes.py`) — the running app builds its
  stylesheet in memory from the tokens.

## 2. Font system
- `app/utils/font_manager.py` loads the bundled Poppins `.ttf` files
  (in `assets/fonts/`, fetched from Google's official OFL-licensed repo)
  via `QFontDatabase` at startup, so it renders even on machines without
  Poppins installed. Wired into `main.py` before any window is created.

## 3. Buttons & tables
- Every button now uses one of a small set of token-driven variants
  (`PrimaryButton`, `DangerButton`, `WarningButton`, `SuccessButton`,
  `SmallButton`, `LargeButton`, default) instead of one-off inline
  `setStyleSheet()`/`setFixedHeight()` calls scattered per window —
  this is what fixes "icon bigger than button" / inconsistent sizing.
- `ui/widgets/table_action_button.py` — new reusable icon-only button
  for table row actions, fixed square size, themed hover/pressed states.
- Table QSS now explicitly styles `::item`, `::item:hover`,
  `::item:selected`, and `::item:selected:!active` (the previous QSS
  only styled `::item:selected`, so hovered/unfocused-selected rows fell
  back to default Qt palette colors — the actual cause of the "hover/
  focus text not showing" bug).

## 4. Icon cleanup
Replaced raw emoji glyphs (which render inconsistently across Windows
font/DPI settings) with themed vector icons via `app/design/icons.py`
in: sidebar, theme toggle, product/customer/supplier/pending-bills/
reports windows, product/purchase dialogs, settings window, login
window. `home_page.py` was already emoji-free.

## 5. Pending bills workflow
- `app/repositories/sale_repository.py` — added `get_by_customer_phone()`
  (additive read-only query).
- `app/utils/pdf_generator.py` — added `generate_payment_receipt_pdf()`,
  a short receipt document separate from the invoice. The original
  invoice is never regenerated/overwritten when a payment comes in.
- `ui/windows/pending_bills_window.py` — rewritten. Each row now has
  three distinct actions: **Pay** (records payment via the *unchanged*
  `BillingService.record_payment`, then offers a payment receipt),
  **History** (view all items + every payment made against the
  invoice), **Reprint** (regenerates the original invoice unchanged).

## 6. Customer purchase history
- `ui/dialogs/sale_history_dialog.py` — new: one invoice's items +
  payment history in one view.
- `ui/dialogs/customer_history_dialog.py` — new: customer summary
  (total purchases/paid/pending) + full purchase history, drill into
  any invoice directly.
- `ui/windows/customer_window.py` — added a History button; double-click
  a customer now opens purchase history (previously opened Edit).

## 7. Packaging
- `requirements.txt` — added `qtawesome`.
- `stock_manager.spec` — bundles `assets/fonts` and qtawesome's icon
  fonts so the packaged `.exe` doesn't ship blank icons/fonts.

## Not included in this pass (recommend as follow-up)
- Alembic migration wiring (package is already a dependency, not yet
  connected to `init_db()`)
- Registration/company branding fields + dynamic login branding
- `home_page.py` / `reports_window.py` deeper layout redesign (icon
  cleanup done; full visual redesign not attempted)

## How to run
```
pip install -r requirements.txt
python main.py
```
Toggle dark/light from the theme button to see both palettes; sizing
and icons should now be consistent across every screen.
