from __future__ import annotations
import os
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QCheckBox, QFrame,
                                QStackedWidget, QScrollArea, QFileDialog)
from PySide2.QtCore import Qt, Signal
from app.services.auth_service import AuthService
from app.design.icons import icon as themed_icon
from PySide2.QtGui import QPixmap

# Used only when NOBODY has registered a company yet (fresh install).
# Once a company is registered, every one of these is replaced by the
# real data from AuthService.get_branding() -- nothing below this line
# is shown once branding exists.
_PLACEHOLDER_NAME = "Stock Manager"
_PLACEHOLDER_TAGLINE = "Register your company to personalize this screen."


class LoginWindow(QWidget):
    login_success = Signal(dict)   # emits user_data on success

    def __init__(self):
        super().__init__()
        self._branding = AuthService.get_branding()  # None if nobody registered yet
        title = self._branding["company_name"] if self._branding else _PLACEHOLDER_NAME
        self.setWindowTitle(f"{title} — Login")
        self.setFixedSize(820, 600)
        self._setup_ui()

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left panel (branding) ──
        left = QFrame()
        left.setObjectName("LoginBrand")
        left.setFixedWidth(380)
        left_layout = QVBoxLayout(left)
        left_layout.setAlignment(Qt.AlignCenter)
        left_layout.setSpacing(12)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)

        self.brand_label = QLabel()
        self.brand_label.setAlignment(Qt.AlignCenter)
        self.brand_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #ffffff;")

        self.tagline_label = QLabel()
        self.tagline_label.setAlignment(Qt.AlignCenter)
        self.tagline_label.setWordWrap(True)
        self.tagline_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.7); line-height: 1.6;")

        self._apply_branding()  # fills in logo/brand/tagline from self._branding

        left_layout.addStretch()
        left_layout.addWidget(self.logo_label)
        left_layout.addWidget(self.brand_label)
        left_layout.addWidget(self.tagline_label)
        left_layout.addStretch()

        # ── Right panel (forms) ──
        right = QFrame()
        right.setObjectName("LoginPanel")
        right_layout = QVBoxLayout(right)
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.setContentsMargins(48, 20, 48, 20)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_login_form())

        signup_scroll = QScrollArea()
        signup_scroll.setObjectName("SignupScroll")
        signup_scroll.setWidgetResizable(True)
        signup_scroll.setFrameShape(QFrame.NoFrame)
        signup_scroll.setStyleSheet("QScrollArea#SignupScroll { background: transparent; border: none; }")
        signup_scroll.setWidget(self._build_signup_form())
        self.stack.addWidget(signup_scroll)

        right_layout.addWidget(self.stack)

        root.addWidget(left)
        root.addWidget(right)

    def _apply_branding(self):
        """
        Fills in the left branding panel (logo, company name, tagline)
        from AuthService.get_branding(). If nobody has registered a
        company yet, shows generic placeholder text instead of any
        specific business name -- so an unregistered/fresh install never
        shows someone else's company details.

        Called once from _setup_ui(); Settings can call this again after
        a company-details update by re-creating/refreshing the window,
        since the login screen itself is only shown before login.
        """
        branding = self._branding

        # -- Logo --
        logo_path = (branding or {}).get("company_logo_path", "")
        pixmap = QPixmap(logo_path) if logo_path else QPixmap()
        if not pixmap.isNull():
            self.logo_label.setPixmap(
                pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            # No logo registered/found -- themed placeholder icon instead
            # of a raw emoji, consistent with the rest of the icon system.
            self.logo_label.setPixmap(themed_icon("building", color="#ffffff").pixmap(64, 64))

        # -- Name --
        name = branding["company_name"] if branding else _PLACEHOLDER_NAME
        self.brand_label.setText(name)

        # -- Tagline (address + phone if registered, else a hint) --
        if branding:
            parts = [p for p in [branding.get("company_address", ""),
                                  branding.get("company_phone", "")] if p]
            self.tagline_label.setText("\n".join(parts) if parts else " ")
        else:
            self.tagline_label.setText(_PLACEHOLDER_TAGLINE)

    # ── Login form ──
    def _build_login_form(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(4) # Base spacing kept tight

        title = QLabel("Welcome back")
        title.setObjectName("AuthTitle")
        subtitle = QLabel("Sign in to your account")
        subtitle.setObjectName("AuthSubtitle")

        self.login_username = self._input("Username", False)
        self.login_password = self._input("Password", True)

        self.remember_me = QCheckBox("Remember me for 7 days")
        self.remember_me.setChecked(True)

        self.login_error = QLabel("")
        self.login_error.setObjectName("ErrorLabel")
        self.login_error.setWordWrap(True)
        self.login_error.hide()

        login_btn = QPushButton("Sign In")
        login_btn.setObjectName("PrimaryButton")
        login_btn.setFixedHeight(42)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self._do_login)
        self.login_password.returnPressed.connect(self._do_login)

        switch_row = QHBoxLayout()
        switch_lbl = QLabel("Don't have an account?")
        switch_lbl.setObjectName("AuthSubtitle")
        switch_btn = QPushButton("Create one")
        switch_btn.setFlat(True)
        switch_btn.setObjectName("LinkButton")
        switch_btn.setCursor(Qt.PointingHandCursor)
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        switch_row.addStretch()
        switch_row.addWidget(switch_lbl)
        switch_row.addWidget(switch_btn)
        switch_row.addStretch()

        # THE FIX: Add stretch to push everything together into the center
        layout.addStretch() 
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20) # Space below subtitle
        
        layout.addWidget(self._label("Username"))
        layout.addWidget(self.login_username)
        layout.addSpacing(12) # Small controlled space between username and password
        
        layout.addWidget(self._label("Password"))
        layout.addWidget(self.login_password)
        layout.addSpacing(10)
        
        layout.addWidget(self.remember_me)
        layout.addWidget(self.login_error)
        layout.addSpacing(20) # Space before button
        
        layout.addWidget(login_btn)
        layout.addSpacing(10)
        layout.addLayout(switch_row)
        
        layout.addStretch() # THE FIX: Push from the bottom up

        return page

    # ── Signup form ──
    def _build_signup_form(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(6) 

        title = QLabel("Create account")
        title.setObjectName("AuthTitle")
        subtitle = QLabel("Fill in the details below")
        subtitle.setObjectName("AuthSubtitle")

        self.reg_fullname = self._input("Full Name", False)
        self.reg_username = self._input("Username", False)
        self.reg_email    = self._input("Email", False)
        self.reg_company  = self._input("Company/Shop Name", False)
        self.reg_address  = self._input("Company Address", False)
        self.reg_gst      = self._input("GST Number (Optional, e.g. 29ABCDE1234F1Z5)", False)
        self.reg_phone    = self._input("Company Phone (Optional)", False)
        self.reg_password = self._input("Password (min 6 chars)", True)

        # Logo: a path field + Browse button, same pattern as the
        # Settings page -- the person picks a file, we store its path,
        # and the PDF/login-branding code reads that path dynamically.
        # We do NOT ask them to type a path by hand.
        logo_row = QHBoxLayout()
        self.reg_logo_path = ""
        self.reg_logo_preview = QLabel("No logo selected")
        self.reg_logo_preview.setObjectName("CardDescription")
        browse_logo_btn = QPushButton("Browse Logo...")
        browse_logo_btn.setObjectName("SmallButton")
        browse_logo_btn.clicked.connect(self._browse_reg_logo)
        logo_row.addWidget(self.reg_logo_preview, stretch=1)
        logo_row.addWidget(browse_logo_btn)

        self.reg_error = QLabel("")
        self.reg_error.setObjectName("ErrorLabel")
        self.reg_error.setWordWrap(True)
        self.reg_error.hide()

        self.reg_success = QLabel("")
        self.reg_success.setObjectName("SuccessLabel")
        self.reg_success.setWordWrap(True)
        self.reg_success.hide()

        reg_btn = QPushButton("Create Account")
        reg_btn.setObjectName("PrimaryButton")
        reg_btn.setFixedHeight(42)
        reg_btn.setCursor(Qt.PointingHandCursor)
        reg_btn.clicked.connect(self._do_register)

        back_row = QHBoxLayout()
        back_lbl = QLabel("Already have an account?")
        back_lbl.setObjectName("AuthSubtitle")
        back_btn = QPushButton("Sign in")
        back_btn.setFlat(True)
        back_btn.setObjectName("LinkButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        back_row.addStretch()
        back_row.addWidget(back_lbl)
        back_row.addWidget(back_btn)
        back_row.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        
        layout.addWidget(self._label("Full Name"));  layout.addWidget(self.reg_fullname)
        layout.addWidget(self._label("Username"));   layout.addWidget(self.reg_username)
        layout.addWidget(self._label("Email"));      layout.addWidget(self.reg_email)
        layout.addWidget(self._label("Company Name")); layout.addWidget(self.reg_company)
        layout.addWidget(self._label("Address"));      layout.addWidget(self.reg_address)
        layout.addWidget(self._label("GST Number (Optional)")); layout.addWidget(self.reg_gst)
        layout.addWidget(self._label("Company Phone (Optional)")); layout.addWidget(self.reg_phone)
        layout.addWidget(self._label("Company Logo (Optional)")); layout.addLayout(logo_row)
        layout.addWidget(self._label("Password"));   layout.addWidget(self.reg_password)
        
        layout.addWidget(self.reg_error)
        layout.addWidget(self.reg_success)
        layout.addSpacing(5)
        layout.addWidget(reg_btn)
        layout.addLayout(back_row)
        layout.addStretch()
        return page

    # ── Actions ──
    def _do_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()

        if not username or not password:
            self._show_error(self.login_error, "Please fill in all fields.")
            return

        ok, msg, user_data = AuthService.login(
            username, password, self.remember_me.isChecked()
        )
        if ok:
            self.login_error.hide()
            self.login_success.emit(user_data)
        else:
            self._show_error(self.login_error, msg)

    def _browse_reg_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Company Logo", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.reg_logo_path = path
            # Show just the filename, not the full path, to keep the row tidy
            self.reg_logo_preview.setText(os.path.basename(path))

    def _do_register(self):
        full_name = self.reg_fullname.text().strip()
        username  = self.reg_username.text().strip()
        email     = self.reg_email.text().strip()
        company   = self.reg_company.text().strip()
        address   = self.reg_address.text().strip()
        gst       = self.reg_gst.text().strip()
        phone     = self.reg_phone.text().strip()
        logo_path = self.reg_logo_path  # set by _browse_reg_logo, "" if none chosen
        password  = self.reg_password.text()

        if not all([full_name, username, email, company, address, password]):
            self._show_error(self.reg_error, "Please fill in all fields.")
            return

        if "@" not in email:
            self._show_error(self.reg_error, "Enter a valid email address.")
            return

        ok, msg = AuthService.register(
            full_name, username, email, password, company, address,
            company_gst=gst, company_logo_path=logo_path, company_phone=phone,
        )
        if ok:
            self.reg_error.hide()
            self._show_success(self.reg_success, msg + " You can now sign in.")
            from PySide2.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self.stack.setCurrentIndex(0))
        else:
            self._show_error(self.reg_error, msg)

    # ── Helpers ──
    def _input(self, placeholder: str, is_password: bool) -> QLineEdit:
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setFixedHeight(43)
        if is_password:
            field.setEchoMode(QLineEdit.Password)
        return field

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("FieldLabel")
        return lbl

    def _show_error(self, label: QLabel, msg: str):
        label.setText(f"⚠  {msg}")
        label.show()

    def _show_success(self, label: QLabel, msg: str):
        label.setText(f"✓  {msg}")
        label.show()

