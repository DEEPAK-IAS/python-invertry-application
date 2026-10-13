from __future__ import annotations
from PySide2.QtWidgets import (QDialog, QFormLayout, QLineEdit,
                                QComboBox, QDoubleSpinBox, QSpinBox,
                                QDialogButtonBox, QPushButton, QHBoxLayout,
                                QVBoxLayout, QWidget, QMessageBox, QLabel)
import json
import os
from app.config.settings import APP_DIR
from app.design.icons import icon

SIZES_FILE = os.path.join(APP_DIR, "sizes.json")
DEFAULT_SIZES = ["Small", "Medium", "Big"]


def load_sizes() -> list:
    if os.path.exists(SIZES_FILE):
        try:
            with open(SIZES_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data
        except Exception:
            pass
    return DEFAULT_SIZES.copy()


def save_sizes(sizes: list):
    try:
        with open(SIZES_FILE, "w") as f:
            json.dump(sizes, f, indent=2)
    except Exception as e:
        print(f"Failed to save sizes: {e}")


class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Add Product" if not product else "Edit Product")
        self.setMinimumWidth(440)
        self._setup_ui()
        if product:
            self._populate(product)

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name_input = QLineEdit()
        self.sku_input  = QLineEdit()

        # ── Size section ───────────────────────────────────────────────
        size_widget = QWidget()
        size_outer = QVBoxLayout(size_widget)
        size_outer.setContentsMargins(0, 0, 0, 0)
        size_outer.setSpacing(4)

        # Row 1: dropdown to SELECT existing size
        self.size_combo = QComboBox()
        self.size_combo.setEditable(False)          # plain dropdown, no typing
        self.size_combo.addItems(load_sizes())
        self.size_combo.setCurrentIndex(0)
        self.size_combo.currentTextChanged.connect(self._on_size_selected)

        # Row 2: text input + buttons to ADD / REMOVE a size
        add_row = QHBoxLayout()
        add_row.setSpacing(4)

        self.new_size_input = QLineEdit()
        self.new_size_input.setPlaceholderText("Type new size to add...")
        self.new_size_input.returnPressed.connect(self._add_new_size)

        add_btn = QPushButton("Add")
        add_btn.setObjectName("SmallButton")
        add_btn.setIcon(icon("add"))
        add_btn.setToolTip("Add typed size to the list")
        add_btn.clicked.connect(self._add_new_size)

        del_btn = QPushButton("Remove")
        del_btn.setObjectName("SmallButton")
        del_btn.setIcon(icon("delete"))
        del_btn.setToolTip("Remove selected size from the list")
        del_btn.clicked.connect(self._remove_size)

        add_row.addWidget(self.new_size_input, stretch=1)
        add_row.addWidget(add_btn)
        add_row.addWidget(del_btn)

        size_outer.addWidget(self.size_combo)
        size_outer.addLayout(add_row)
        # ───────────────────────────────────────────────────────────────

        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(999999.99)
        self.price_input.setPrefix("₹ ")

        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(999999)

        self.gst_input = QDoubleSpinBox()
        self.gst_input.setRange(0, 100)
        self.gst_input.setSuffix("%")

        layout.addRow("Name:",     self.name_input)
        layout.addRow("SKU:",      self.sku_input)
        layout.addRow("Size:",     size_widget)
        layout.addRow("Price:",    self.price_input)
        layout.addRow("Stock:",    self.stock_input)
        layout.addRow("GST Rate:", self.gst_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_size_selected(self, text):
        """Keep new_size_input clear when user picks from dropdown."""
        self.new_size_input.clear()

    def _add_new_size(self):
        new_size = self.new_size_input.text().strip()
        if not new_size:
            QMessageBox.warning(self, "Empty", "Please type a size name first.")
            return

        existing = [self.size_combo.itemText(i) for i in range(self.size_combo.count())]
        if new_size in existing:
            # Just select it
            self.size_combo.setCurrentText(new_size)
            self.new_size_input.clear()
            return

        self.size_combo.addItem(new_size)
        self.size_combo.setCurrentText(new_size)
        self.new_size_input.clear()
        save_sizes(existing + [new_size])
        QMessageBox.information(self, "Added", f'"{new_size}" added to size list.')

    def _remove_size(self):
        current_text = self.size_combo.currentText()
        current_index = self.size_combo.currentIndex()

        if not current_text:
            return

        confirm = QMessageBox.question(
            self, "Remove Size",
            f'Remove "{current_text}" from the size list?',
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        self.size_combo.removeItem(current_index)
        sizes = [self.size_combo.itemText(i) for i in range(self.size_combo.count())]
        save_sizes(sizes)

        if self.size_combo.count() > 0:
            self.size_combo.setCurrentIndex(0)

    def _set_size(self, size_val: str):
        if not size_val:
            return
        index = self.size_combo.findText(size_val)
        if index != -1:
            self.size_combo.setCurrentIndex(index)
        else:
            # Size from DB not in local list — add it
            self.size_combo.addItem(size_val)
            self.size_combo.setCurrentText(size_val)

    def _populate(self, product):
        if isinstance(product, dict):
            self.name_input.setText(str(product.get("name", "")))
            self.sku_input.setText(str(product.get("sku", "")))
            self._set_size(product.get("size", ""))
            self.price_input.setValue(float(product.get("price", 0.0)))
            self.stock_input.setValue(int(product.get("stock_qty", 0)))
            self.gst_input.setValue(float(product.get("gst_rate", 0.0)))
        else:
            self.name_input.setText(str(product.name))
            self.sku_input.setText(str(product.sku))
            self._set_size(getattr(product, "size", ""))
            self.price_input.setValue(float(product.price))
            self.stock_input.setValue(int(product.stock_qty))
            self.gst_input.setValue(float(getattr(product, "gst_rate", 0.0)))

    def get_data(self) -> dict:
        return {
            "name":      self.name_input.text().strip(),
            "sku":       self.sku_input.text().strip(),
            "size":      self.size_combo.currentText().strip(),
            "price":     self.price_input.value(),
            "stock_qty": self.stock_input.value(),
            "gst_rate":  self.gst_input.value(),
        }

