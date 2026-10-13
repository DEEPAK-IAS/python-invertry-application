from __future__ import annotations
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide2.QtCore import Signal

from app.database.connection import get_session
from app.repositories.product_repository import ProductRepository
from app.repositories.customer_repository import CustomerRepository
from app.design.icons import icon


class StatCard(QFrame):
    def __init__(self, title: str, value: str):
        super().__init__()

        self.setObjectName("StatCard")
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("StatValue")

        title_lbl = QLabel(title)
        title_lbl.setObjectName("StatLabel")

        layout.addWidget(self.value_lbl)
        layout.addWidget(title_lbl)

    def set_value(self, value: str):
        self.value_lbl.setText(value)


class SectionTitle(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        # objectName-driven sizing (see app/design/qss_builder.py) instead
        # of a hardcoded setFont() -- keeps this in sync with the rest of
        # the app's typography and lets it inherit the Poppins family
        # loaded centrally by FontManager, instead of fighting it here.
        self.setObjectName("SectionTitle")

        self.setStyleSheet("""
            margin-top: 15px;
            margin-bottom: 5px;
        """)


class HomePage(QWidget):

    navigate_requested = Signal(int, str)

    def __init__(self, user_data: dict):
        super().__init__()

        self.user_data = user_data

        self._setup_ui()
        self.refresh()

    def _setup_ui(self):

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()

        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(24, 20, 24, 24)
        self.main_layout.setSpacing(16)

        # Header

        greet_lbl = QLabel(
            f"Welcome back, {self.user_data.get('full_name', 'User')}"
        )

        greet_lbl.setObjectName("TitleLabel")

        self.main_layout.addWidget(greet_lbl)

        # Overview

        self.main_layout.addWidget(
            SectionTitle("System Overview")
        )

        cards_layout = QHBoxLayout()

        self.card_products = StatCard(
            "Total Products", "0"
        )

        self.card_customers = StatCard(
            "Total Customers", "0"
        )

        self.card_lowstock = StatCard(
            "Low Stock", "0"
        )

        self.card_outstock = StatCard(
            "Out of Stock", "0"
        )

        for card in [
            self.card_products,
            self.card_customers,
            self.card_lowstock,
            self.card_outstock
        ]:
            cards_layout.addWidget(card)

        self.main_layout.addLayout(cards_layout)

        # Tables

        two_col = QHBoxLayout()

        left_col = QVBoxLayout()

        left_col.addWidget(
            SectionTitle("Low Stock Alert")
        )

        self.low_stock_table = self._make_table(
            ["Product", "SKU", "Stock"]
        )

        self.low_stock_table.setMinimumHeight(200)

        left_col.addWidget(
            self.low_stock_table
        )

        right_col = QVBoxLayout()

        right_col.addWidget(
            SectionTitle("Stock Summary")
        )

        self.summary_frame = QFrame()
        self.summary_frame.setObjectName(
            "SummaryFrame"
        )

        self.summary_layout = QVBoxLayout(
            self.summary_frame
        )

        right_col.addWidget(
            self.summary_frame
        )

        right_col.addStretch()

        two_col.addLayout(left_col, 65)
        two_col.addLayout(right_col, 35)

        self.main_layout.addLayout(two_col)

        # Products

        self.main_layout.addWidget(
            SectionTitle("All Products")
        )

        self.all_products_table = self._make_table(
            ["Name", "SKU", "Price", "Stock"]
        )

        self.all_products_table.setMinimumHeight(
            250
        )

        self.main_layout.addWidget(
            self.all_products_table
        )

        scroll.setWidget(container)

        outer = QVBoxLayout(self)

        outer.setContentsMargins(
            0, 0, 0, 0
        )

        outer.addWidget(scroll)

    def _make_table(self, headers):
        table = QTableWidget()

        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Fix header height
        header.setMinimumHeight(45)
        header.setDefaultSectionSize(45)

        # Fix font
        font = header.font()
        font.setPointSize(11)
        font.setBold(True)
        header.setFont(font)

        return table

    def _summary_row(self, icon_name, label, value):

        row = QWidget()

        layout = QHBoxLayout(row)

        layout.setContentsMargins(
            5, 5, 5, 5
        )
        layout.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon(icon_name).pixmap(16, 16))

        lbl = QLabel(label)

        val = QLabel(value)

        val.setStyleSheet("""
            font-weight:bold;
        """)

        layout.addWidget(icon_lbl)
        layout.addWidget(lbl)
        layout.addStretch()
        layout.addWidget(val)

        return row

    def refresh(self):

        session = get_session()

        try:

            prod_repo = ProductRepository(
                session
            )

            products = prod_repo.get_all()

            customers = CustomerRepository(
                session
            ).get_all()

            low_stock = [
                p for p in products
                if 0 < p.stock_qty <= 10
            ]

            out_stock = [
                p for p in products
                if p.stock_qty == 0
            ]

            in_stock = [
                p for p in products
                if p.stock_qty > 10
            ]

            total_value = sum(
                p.price * p.stock_qty
                for p in products
            )

            self.card_products.set_value(
                str(len(products))
            )

            self.card_customers.set_value(
                str(len(customers))
            )

            self.card_lowstock.set_value(
                str(len(low_stock))
            )

            self.card_outstock.set_value(
                str(len(out_stock))
            )

            while self.summary_layout.count():

                item = self.summary_layout.takeAt(0)

                if item.widget():
                    item.widget().deleteLater()

            summary_rows = [

                ("check", "In Stock",
                 str(len(in_stock))),

                ("warning", "Low Stock",
                 str(len(low_stock))),

                ("close", "Out of Stock",
                 str(len(out_stock))),

                ("payment", "Total Value",
                 f"₹{total_value:,.0f}")
            ]

            for icon_name, label, value in summary_rows:

                self.summary_layout.addWidget(
                    self._summary_row(
                        icon_name,
                        label,
                        value
                    )
                )

            self.low_stock_table.setRowCount(
                len(low_stock)
            )

            for row, product in enumerate(
                low_stock
            ):

                self.low_stock_table.setItem(
                    row, 0,
                    QTableWidgetItem(product.name)
                )

                self.low_stock_table.setItem(
                    row, 1,
                    QTableWidgetItem(product.sku)
                )

                self.low_stock_table.setItem(
                    row, 2,
                    QTableWidgetItem(
                        str(product.stock_qty)
                    )
                )

            self.all_products_table.setRowCount(
                len(products)
            )

            for row, product in enumerate(
                products
            ):

                self.all_products_table.setItem(
                    row, 0,
                    QTableWidgetItem(product.name)
                )

                self.all_products_table.setItem(
                    row, 1,
                    QTableWidgetItem(product.sku)
                )

                self.all_products_table.setItem(
                    row, 2,
                    QTableWidgetItem(
                        f"₹{product.price:.2f}"
                    )
                )

                self.all_products_table.setItem(
                    row, 3,
                    QTableWidgetItem(
                        str(product.stock_qty)
                    )
                )

        finally:
            session.close()

