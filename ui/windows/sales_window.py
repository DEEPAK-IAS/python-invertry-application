from __future__ import annotations
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QSpinBox, QDoubleSpinBox, QMessageBox, QComboBox, QStyle, QCompleter,
)
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import QShortcut
from PySide2.QtCore import Qt

from app.services.billing_service import BillingService
from app.database.connection import SessionLocal
from app.models.product import Product
from app.models.customer import Customer


class SalesWindow(QWidget):
    def __init__(self, company_name="Dindigul School Point", user_data=None):
        super().__init__()
        self.company_name = company_name
        self.user_data = user_data or {}
        self.cart_items = []
        self.setWindowTitle("Point of Sale / Billing")
        self.resize(1000, 680)
        self._setup_ui()
        self._setup_shortcuts()
        self._load_products()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # ── Customer info ──
        customer_layout = QHBoxLayout()
        self.cust_name_input = QLineEdit()
        self.cust_name_input.setPlaceholderText("Customer Name (Optional)")
        self.cust_name_input.setMinimumHeight(44)
        self.cust_phone_input = QLineEdit()
        self.cust_phone_input.setPlaceholderText("Customer Phone (Optional)")
        self.cust_gstin_input = QLineEdit()
        self.cust_gstin_input.setPlaceholderText("Customer GSTIN (Optional)")
        self.cust_address_input = QLineEdit()
        self.cust_address_input.setPlaceholderText("Customer Address (Optional)")
        customer_layout.addWidget(QLabel("Customer:"))
        customer_layout.addWidget(self.cust_name_input)
        customer_layout.addWidget(QLabel("Phone:"))
        customer_layout.addWidget(self.cust_phone_input)
        customer_layout.addWidget(QLabel("GSTIN:"))
        customer_layout.addWidget(self.cust_gstin_input)
        customer_layout.addWidget(QLabel("Address:"))
        customer_layout.addWidget(self.cust_address_input)
        main_layout.addLayout(customer_layout)
        self.cust_phone_input.textChanged.connect(self._search_customer_by_phone)

        self._name_completer = QCompleter()
        self._name_completer.setCompletionMode(QCompleter.PopupCompletion)
        self._name_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._name_completer.setFilterMode(Qt.MatchContains)
        self.cust_name_input.setCompleter(self._name_completer)
        self._name_completer.activated.connect(self._search_customer_by_name)
        self.cust_name_input.editingFinished.connect(self._search_customer_by_name)
        self._load_customer_names()

        # ── Product selection ──
        product_layout = QHBoxLayout()
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setInsertPolicy(QComboBox.NoInsert)
        self.product_combo.setMinimumHeight(44)

        completer = QCompleter()
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.product_combo.setCompleter(completer)

        self.qty_spinbox = QSpinBox()
        self.qty_spinbox.setMinimum(1)
        self.qty_spinbox.setMinimumWidth(80)
        self.qty_spinbox.setMinimumHeight(44)
        self.qty_spinbox.setMaximum(9999)
        self.qty_spinbox.setKeyboardTracking(False)

        self.add_btn = QPushButton(" Add to Cart")
        self.add_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        self.add_btn.setStyleSheet(
            "background-color: #2b5797; color: white; font-weight: bold; padding: 5px;"
        )
        self.add_btn.setMinimumHeight(44)
        self.add_btn.clicked.connect(self.add_to_cart)
        
        self.btn_reset_cart = QPushButton("Reset Cart")
        self.btn_reset_cart.setObjectName("DangerButton")
        self.btn_reset_cart.clicked.connect(self._reset_cart)

        product_layout.addWidget(QLabel("Search Product (Ctrl+F):"))
        product_layout.addWidget(self.product_combo, stretch=1)
        product_layout.addWidget(QLabel("Qty:"))
        product_layout.addWidget(self.qty_spinbox)
        product_layout.addWidget(self.add_btn)
        product_layout.addWidget(self.btn_reset_cart)
        
        main_layout.addLayout(product_layout)

        # ── Cart table ──
        self.cart_table = QTableWidget(0, 8)
        self.cart_table.setHorizontalHeaderLabels(
            ["ID", "Product Name", "Qty", "Unit Price", "Subtotal", "GST %", "GST Amt", "Action"]
        )
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cart_table.setColumnWidth(0, 40)
        self.cart_table.setColumnWidth(5, 60)
        self.cart_table.setColumnWidth(6, 80)
        self.cart_table.setColumnWidth(7, 60)
        main_layout.addWidget(self.cart_table)

        # ── Totals + checkout ──
        bottom_layout = QHBoxLayout()

        # Options layout (GST & Discount)
        options_layout = QVBoxLayout()
        self.gst_checkbox = QCheckBox("Apply GST (per-product rate)")
        self.gst_checkbox.setChecked(True)
        self.gst_checkbox.stateChanged.connect(self.update_totals)

        # Discount Controls
        disc_layout = QHBoxLayout()
        self.discount_checkbox = QCheckBox("Apply Discount (%)")
        self.discount_spinbox = QDoubleSpinBox()
        self.discount_spinbox.setRange(0.0, 100.0)
        self.discount_spinbox.setValue(0.0)
        self.discount_spinbox.setSuffix("%")
        self.discount_spinbox.setEnabled(False)  # Off by default
        
        self.discount_checkbox.toggled.connect(self.discount_spinbox.setEnabled)
        self.discount_checkbox.toggled.connect(self.update_totals)
        self.discount_spinbox.valueChanged.connect(self.update_totals)

        disc_layout.addWidget(self.discount_checkbox)
        disc_layout.addWidget(self.discount_spinbox)

        options_layout.addWidget(self.gst_checkbox)
        options_layout.addLayout(disc_layout)

        # Totals Labels
        self.subtotal_label = QLabel("Subtotal: ₹0.00")
        self.discount_label = QLabel("Discount (0%): -₹0.00")
        self.gst_label      = QLabel("GST: ₹0.00")
        self.total_label    = QLabel("<b>Grand Total: ₹0.00</b>")
        self.total_label.setStyleSheet("font-size: 18px;")

        # ── Pending Bill / Partial Payment ──
        self.full_payment_checkbox = QCheckBox("Full Payment")
        self.full_payment_checkbox.setChecked(True)
        self.full_payment_checkbox.stateChanged.connect(self._on_full_payment_toggled)

        self.paid_label = QLabel("Amount Paid:")
        self.paid_input = QDoubleSpinBox()
        self.paid_input.setPrefix("₹")
        self.paid_input.setDecimals(2)
        self.paid_input.setMaximum(10_000_000.0)
        self.paid_input.setEnabled(False)  
        self.paid_input.valueChanged.connect(self._update_due_label)

        self.due_label = QLabel("Balance Due: ₹0.00")
        self.due_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f38ba8;")

        payment_layout = QHBoxLayout()
        payment_layout.addWidget(self.full_payment_checkbox)
        payment_layout.addWidget(self.paid_label)
        payment_layout.addWidget(self.paid_input)
        payment_layout.addWidget(self.due_label)

        self.checkout_btn = QPushButton(" Checkout & Print (F12)")
        self.checkout_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.checkout_btn.setStyleSheet(
            "background-color: #2E8B57; color: white; font-weight: bold; padding: 10px 20px;"
        )
        self.checkout_btn.clicked.connect(self.process_checkout)

        totals_layout = QVBoxLayout()
        totals_layout.addWidget(self.subtotal_label, alignment=Qt.AlignRight)
        totals_layout.addWidget(self.discount_label, alignment=Qt.AlignRight)
        totals_layout.addWidget(self.gst_label,      alignment=Qt.AlignRight)
        totals_layout.addWidget(self.total_label,    alignment=Qt.AlignRight)

        bottom_layout.addLayout(options_layout)
        bottom_layout.addStretch()
        bottom_layout.addLayout(totals_layout)
        bottom_layout.addWidget(self.checkout_btn)
        main_layout.addLayout(bottom_layout)
        main_layout.addLayout(payment_layout)

    def _search_customer_by_phone(self):
        phone = self.cust_phone_input.text().strip()
        if len(phone) >= 10:
            with SessionLocal() as db:
                customer = db.query(Customer).filter(Customer.phone == phone).first()
                if customer:
                    self.cust_name_input.setText(customer.name)

    def _load_customer_names(self):
        from PySide2.QtCore import QStringListModel
        with SessionLocal() as db:
            names = [c.name for c in db.query(Customer).all() if c.name]
        self._name_completer.setModel(QStringListModel(names))

    def _search_customer_by_name(self, *_):
        name = self.cust_name_input.text().strip()
        if not name:
            return
        with SessionLocal() as db:
            customer = db.query(Customer).filter(Customer.name == name).first()
            if customer:
                self.cust_phone_input.setText(customer.phone or "")
                self.cust_address_input.setText(customer.address or "")

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.product_combo.setFocus)
        QShortcut(QKeySequence("F12"),    self).activated.connect(self.process_checkout)
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.add_to_cart)
        QShortcut(QKeySequence("Return"), self).activated.connect(self.add_to_cart) 

    def _load_products(self):
        self.product_combo.clear()
        with SessionLocal() as db:
            products = db.query(Product).filter(Product.stock_qty > 0).all()
            for p in products:
                size_label = getattr(p, "size", "N/A") or "N/A"
                gst_rate   = getattr(p, "gst_rate", 0.0) or 0.0
                display_text = (
                    f"{p.name} ({size_label}) - ₹{p.price:.2f} "
                    f"[GST:{gst_rate:.0f}%] (Stock: {p.stock_qty})"
                )
                self.product_combo.addItem(display_text, userData=p)

        if self.product_combo.completer():
            self.product_combo.completer().setModel(self.product_combo.model())
        self.product_combo.setCurrentIndex(-1)

    def showEvent(self, event):
        self._load_products()
        super().showEvent(event)

    def add_to_cart(self):
        self.qty_spinbox.interpretText()
        search_text = self.product_combo.currentText().strip().lower()
        product = None
        for i in range(self.product_combo.count()):
            if search_text in self.product_combo.itemText(i).lower():
                product = self.product_combo.itemData(i)
                break

        if not product:
            QMessageBox.warning(self, "Invalid", "Please select a valid product.")
            return

        qty = self.qty_spinbox.value()
        if qty > product.stock_qty:
            QMessageBox.warning(self, "Stock", f"Only {product.stock_qty} available.")
            return

        gst_rate    = getattr(product, "gst_rate", 0.0) or 0.0
        total_price = product.price * qty
        gst_amount  = total_price * (gst_rate / 100)

        self.cart_items.append({
            "product_id": product.id,
            "name":       product.name,
            "quantity":   qty,
            "price":      product.price,
            "total":      total_price,
            "gst_rate":   gst_rate,
            "gst_amount": gst_amount,
        })

        row = self.cart_table.rowCount()
        self.cart_table.insertRow(row)
        self.cart_table.setItem(row, 0, QTableWidgetItem(str(product.id)))
        display_name = f"{product.name} ({product.size or 'N/A'})"
        self.cart_table.setItem(row, 1, QTableWidgetItem(display_name))
        self.cart_table.setItem(row, 2, QTableWidgetItem(str(qty)))
        self.cart_table.setItem(row, 3, QTableWidgetItem(f"₹{product.price:.2f}"))
        self.cart_table.setItem(row, 4, QTableWidgetItem(f"₹{total_price:.2f}"))
        self.cart_table.setItem(row, 5, QTableWidgetItem(f"{gst_rate:.0f}%"))

        gst_item = QTableWidgetItem(f"₹{gst_amount:.2f}")
        gst_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cart_table.setItem(row, 6, gst_item)

        remove_btn = QPushButton()
        remove_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        remove_btn.clicked.connect(self._remove_item_from_cart)
        self.cart_table.setCellWidget(row, 7, remove_btn)

        self.update_totals()
        self.product_combo.setCurrentText("")
        self.product_combo.setFocus()
        
    def _reset_cart(self):
        if QMessageBox.question(
            self, "Clear Cart",
            "Are you sure you want to clear all items?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.cart_table.setRowCount(0)
            self.selected_product = None
            self.update_totals()

    def _calculate_financials(self):
        subtotal = sum(item["total"] for item in self.cart_items)
        
        # Discount Calculation
        apply_disc = self.discount_checkbox.isChecked()
        disc_pct = self.discount_spinbox.value() if apply_disc else 0.0
        disc_amt = (subtotal * disc_pct) / 100.0
        taxable_subtotal = subtotal - disc_amt

        # Proportional multiplier for GST if discount is active
        ratio = taxable_subtotal / subtotal if subtotal > 0 else 1.0

        # GST Calculation
        apply_gst = self.gst_checkbox.isChecked()
        if apply_gst:
            gst = sum((item["total"] * ratio) * (item["gst_rate"] / 100) for item in self.cart_items)
        else:
            gst = 0.0

        grand_total = taxable_subtotal + gst
        return subtotal, disc_pct, disc_amt, gst, grand_total

    def update_totals(self):
        subtotal, disc_pct, disc_amt, gst, grand_total = self._calculate_financials()

        self.subtotal_label.setText(f"Subtotal: ₹{subtotal:.2f}")
        if disc_amt > 0:
            self.discount_label.setText(f"Discount ({disc_pct:.1f}%): -₹{disc_amt:.2f}")
            self.discount_label.show()
        else:
            self.discount_label.setText("Discount (0%): -₹0.00")
            self.discount_label.setVisible(self.discount_checkbox.isChecked())

        self.gst_label.setText(f"GST: ₹{gst:.2f}")
        self.total_label.setText(f"<b>Grand Total: ₹{grand_total:.2f}</b>")

        self.cart_table.setColumnHidden(6, not self.gst_checkbox.isChecked())

        self.paid_input.setMaximum(max(grand_total, 0.0))
        if self.full_payment_checkbox.isChecked():
            self.paid_input.blockSignals(True)
            self.paid_input.setValue(grand_total)
            self.paid_input.blockSignals(False)
        self._update_due_label()

    def _on_full_payment_toggled(self, state):
        is_full = self.full_payment_checkbox.isChecked()
        self.paid_input.setEnabled(not is_full)
        if is_full:
            _, _, _, _, grand_total = self._calculate_financials()
            self.paid_input.blockSignals(True)
            self.paid_input.setValue(grand_total)
            self.paid_input.blockSignals(False)
        self._update_due_label()

    def _update_due_label(self):
        _, _, _, _, grand_total = self._calculate_financials()
        due = max(0.0, round(grand_total - self.paid_input.value(), 2))
        self.due_label.setText(f"Balance Due: ₹{due:.2f}")
        self.due_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: %s;"
            % ("#a6e3a1" if due <= 0.001 else "#f38ba8")
        )

    def _remove_item_from_cart(self):
        button = self.sender()
        for row in range(self.cart_table.rowCount()):
            if self.cart_table.cellWidget(row, 7) == button:
                self.cart_items.pop(row)
                self.cart_table.removeRow(row)
                self.update_totals()
                break

    def process_checkout(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Empty", "Add items to cart.")
            return

        self.checkout_btn.setEnabled(False)
        _, disc_pct, disc_amt, _, _ = self._calculate_financials()

        customer_data = {
            "name":               self.cust_name_input.text().strip() or "Walk-in",
            "phone":              self.cust_phone_input.text().strip(),
            "gstin":              self.cust_gstin_input.text().strip(),
            "address":            self.cust_address_input.text().strip(),
            "discount_percentage": disc_pct,
            "discount_amount":    disc_amt,
        }
        
        address = self.user_data.get("company_address", "")
        gst_no  = self.user_data.get("company_gst", "")
        phone_no = self.user_data.get("company_phone", "")
        email_id = self.user_data.get("email", "")

        try:
            with SessionLocal() as db:
                sale = BillingService.process_checkout(
                    db,
                    customer_data,
                    self.cart_items,
                    self.gst_checkbox.isChecked(),
                    company_name=self.company_name,
                    company_address=address,
                    company_gst=gst_no,
                    company_phone=phone_no,
                    company_email=email_id,
                    company_logo_path=self.user_data.get("company_logo_path", ""),
                    amount_paid=self.paid_input.value(),
                    preferred_printer=self.user_data.get("preferred_printer", "")
                )
            if sale.due_amount > 0.001:
                QMessageBox.information(
                    self, "Success",
                    f"Invoice #{sale.id} generated.\n\n"
                    f"Paid: ₹{sale.paid_amount:.2f}\n"
                    f"Pending (Due): ₹{sale.due_amount:.2f}\n\n"
                    "This bill has been added to Pending Bills."
                )
            else:
                QMessageBox.information(self, "Success", f"Invoice #{sale.id} generated. Fully paid.")
            self._reset_window()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.checkout_btn.setEnabled(True)

    def _reset_window(self):
        self.cart_items = []
        self.cart_table.setRowCount(0)
        self.cust_name_input.clear()
        self.cust_phone_input.clear()
        self.cust_gstin_input.clear()
        self.cust_address_input.clear()
        self.gst_checkbox.setChecked(True)
        self.discount_checkbox.setChecked(False)
        self.discount_spinbox.setValue(0.0)
        self.qty_spinbox.setValue(1)
        self.full_payment_checkbox.setChecked(True)
        self.paid_input.setEnabled(False)
        self.update_totals()
        self._load_products()
        self._load_customer_names()

    def refresh(self):
        self._load_products()