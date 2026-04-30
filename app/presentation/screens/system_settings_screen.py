"""System settings screen - S-CFG-01 - System configuration.

Features:
- Edit dealer info: name, address, phone, email
- Edit warranty settings: thoi_han_bh_default, muc_toi_thieu_ton_kho
- Edit backup path
- Logo upload (placeholder - stores path only)
- Only admin (A-01) can access

References:
- System configuration settings
- BR-NV-08: Must change password on first login
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
    QLineEdit, QPushButton, QGroupBox, QMessageBox,
    QFileDialog, QCheckBox, QSpinBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.application.services.system_settings_service import SystemSettingsService
from app.application.services.session import CurrentSession
from app.application.services.audit_decorator import audit


class SystemSettingsScreen(QWidget):
    """System settings screen - S-CFG-01.
    
    Allows admin to edit system configuration.
    Only accessible by A-01 (Admin) role.
    """
    
    settings_changed = pyqtSignal()
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize system settings screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._settings_service = SystemSettingsService(db_conn)
        
        self._original_values = {}
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Cài đặt hệ thống")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # User info badge
        if self._session:
            user_label = QLabel(f"👤 {self._session.ho_ten} ({self._session.vai_tro_ma})")
            user_label.setStyleSheet("font-size: 13px; color: #86868b; padding: 4px 8px; background: #f5f5f7; border-radius: 4px;")
            header_layout.addWidget(user_label)
        
        layout.addLayout(header_layout)
        
        # Scroll area container
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left column - Dealer info
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)
        
        # Dealer info group
        dealer_group = QGroupBox("📋 Thông tin đại lý")
        dealer_group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
        """)
        dealer_layout = QFormLayout()
        dealer_layout.setSpacing(12)
        
        self._ten_dai_ly = QLineEdit()
        self._ten_dai_ly.setPlaceholderText("Tên công ty đại lý xe")
        self._ten_dai_ly.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        dealer_layout.addRow("Tên đại lý:", self._ten_dai_ly)
        
        self._dia_chi = QLineEdit()
        self._dia_chi.setPlaceholderText("Địa chỉ đầy đủ")
        self._dia_chi.setStyleSheet(self._ten_dai_ly.styleSheet())
        dealer_layout.addRow("Địa chỉ:", self._dia_chi)
        
        self._so_dien_thoai = QLineEdit()
        self._so_dien_thoai.setPlaceholderText("0123456789")
        self._so_dien_thoai.setStyleSheet(self._ten_dai_ly.styleSheet())
        dealer_layout.addRow("Số điện thoại:", self._so_dien_thoai)
        
        self._email = QLineEdit()
        self._email.setPlaceholderText("contact@dailyxeco.vn")
        self._email.setStyleSheet(self._ten_dai_ly.styleSheet())
        dealer_layout.addRow("Email:", self._email)
        
        dealer_group.setLayout(dealer_layout)
        left_layout.addWidget(dealer_group)
        
        # Logo group
        logo_group = QGroupBox("🖼️ Logo đại lý")
        logo_group.setStyleSheet(dealer_group.styleSheet())
        logo_layout = QHBoxLayout()
        
        self._logo_path = QLineEdit()
        self._logo_path.setPlaceholderText("Đường dẫn file logo...")
        self._logo_path.setReadOnly(True)
        self._logo_path.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: #f5f5f7;
            }
        """)
        logo_layout.addWidget(self._logo_path, stretch=1)
        
        self._browse_logo_btn = QPushButton("📂 Chọn file")
        self._browse_logo_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._browse_logo_btn.clicked.connect(self._on_browse_logo)
        logo_layout.addWidget(self._browse_logo_btn)
        
        logo_group.setLayout(logo_layout)
        left_layout.addWidget(logo_group)
        left_layout.addStretch()
        
        content_layout.addWidget(left_widget, stretch=1)
        
        # Right column - System settings
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)
        
        # Warranty settings group
        warranty_group = QGroupBox("🛡️ Cài đặt bảo hành & kho")
        warranty_group.setStyleSheet(dealer_group.styleSheet())
        warranty_layout = QFormLayout()
        warranty_layout.setSpacing(12)
        
        self._thoi_han_bh = QSpinBox()
        self._thoi_han_bh.setRange(1, 60)
        self._thoi_han_bh.setSuffix(" tháng")
        self._thoi_han_bh.setStyleSheet("""
            QSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QSpinBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        warranty_layout.addRow("Thời hạn BH mặc định:", self._thoi_han_bh)
        
        self._muc_toi_thieu = QSpinBox()
        self._muc_toi_thieu.setRange(0, 100)
        self._muc_toi_thieu.setSuffix(" xe")
        self._muc_toi_thieu.setStyleSheet(self._thoi_han_bh.styleSheet())
        warranty_layout.addRow("Mức tồn kho tối thiểu:", self._muc_toi_thieu)
        
        warranty_group.setLayout(warranty_layout)
        right_layout.addWidget(warranty_group)
        
        # Backup settings group
        backup_group = QGroupBox("💾 Cài đặt sao lưu")
        backup_group.setStyleSheet(dealer_group.styleSheet())
        backup_layout = QFormLayout()
        backup_layout.setSpacing(12)
        
        self._backup_path = QLineEdit()
        self._backup_path.setPlaceholderText("/home/hieu/backup")
        self._backup_path.setStyleSheet(self._ten_dai_ly.styleSheet())
        backup_layout.addRow("Thư mục sao lưu:", self._backup_path)
        
        backup_path_layout = QHBoxLayout()
        backup_path_layout.addWidget(self._backup_path)
        
        self._browse_backup_btn = QPushButton("📂 Chọn thư mục")
        self._browse_backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._browse_backup_btn.clicked.connect(self._on_browse_backup)
        backup_path_layout.addWidget(self._browse_backup_btn)
        
        backup_layout.addRow("", backup_path_layout)
        
        self._auto_backup = QCheckBox("Tự động sao lưu hàng ngày")
        self._auto_backup.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #1d1d1f;
                padding: 4px 0;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #d2d2d7;
            }
            QCheckBox::indicator:checked {
                background-color: #0066cc;
                border-color: #0066cc;
            }
        """)
        backup_layout.addRow("", self._auto_backup)
        
        backup_group.setLayout(backup_layout)
        right_layout.addWidget(backup_group)
        
        # App info group
        app_info_group = QGroupBox("ℹ️ Thông tin ứng dụng")
        app_info_group.setStyleSheet(dealer_group.styleSheet())
        app_info_layout = QFormLayout()
        app_info_layout.setSpacing(12)
        
        self._version_label = QLabel("1.0.0")
        self._version_label.setStyleSheet("font-size: 14px; color: #86868b;")
        app_info_layout.addRow("Phiên bản:", self._version_label)
        
        app_info_group.setLayout(app_info_layout)
        right_layout.addWidget(app_info_group)
        
        right_layout.addStretch()
        
        content_layout.addWidget(right_widget, stretch=1)
        
        layout.addLayout(content_layout, stretch=1)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self._reset_btn = QPushButton("🔄 Khôi phục")
        self._reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._reset_btn.clicked.connect(self._on_reset)
        action_layout.addWidget(self._reset_btn)
        
        self._save_btn = QPushButton("💾 Lưu thay đổi")
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._save_btn.clicked.connect(self._on_save)
        action_layout.addWidget(self._save_btn)
        
        layout.addLayout(action_layout)
    
    def _load_settings(self):
        """Load settings from database."""
        settings = self._settings_service.load_settings()
        
        # Store original values for reset
        self._original_values = {
            "ten_dai_ly": settings.ten_dai_ly,
            "dia_chi_dai_ly": settings.dia_chi_dai_ly,
            "so_dien_thoai_dai_ly": settings.so_dien_thoai_dai_ly,
            "email_dai_ly": settings.email_dai_ly,
            "logo_url": settings.logo_url or "",
            "thoi_han_bh_default": settings.thoi_han_bh_default,
            "muc_toi_thieu_ton_kho": settings.muc_toi_thieu_ton_kho,
        }
        
        # Populate fields
        self._ten_dai_ly.setText(settings.ten_dai_ly)
        self._dia_chi.setText(settings.dia_chi_dai_ly)
        self._so_dien_thoai.setText(settings.so_dien_thoai_dai_ly)
        self._email.setText(settings.email_dai_ly)
        self._logo_path.setText(settings.logo_url or "")
        self._thoi_han_bh.setValue(settings.thoi_han_bh_default)
        self._muc_toi_thieu.setValue(settings.muc_toi_thieu_ton_kho)
        
        # Load backup path from system_settings
        backup_path = self._settings_service.get_setting("backup_path")
        self._backup_path.setText(backup_path or "")
    
    def _on_browse_logo(self):
        """Handle browse logo button."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file logo",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*)"
        )
        
        if file_path:
            self._logo_path.setText(file_path)
    
    def _on_browse_backup(self):
        """Handle browse backup path button."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Chọn thư mục sao lưu",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if dir_path:
            self._backup_path.setText(dir_path)
    
    def _on_reset(self):
        """Reset form to original values."""
        if self._original_values:
            self._ten_dai_ly.setText(self._original_values.get("ten_dai_ly", ""))
            self._dia_chi.setText(self._original_values.get("dia_chi_dai_ly", ""))
            self._so_dien_thoai.setText(self._original_values.get("so_dien_thoai_dai_ly", ""))
            self._email.setText(self._original_values.get("email_dai_ly", ""))
            self._logo_path.setText(self._original_values.get("logo_url", ""))
            self._thoi_han_bh.setValue(self._original_values.get("thoi_han_bh_default", 24))
            self._muc_toi_thieu.setValue(self._original_values.get("muc_toi_thieu_ton_kho", 2))
            self._backup_path.setText(self._settings_service.get_setting("backup_path") or "")
    
    def _on_save(self):
        """Save settings to database."""
        try:
            # Validate inputs
            if not self._ten_dai_ly.text().strip():
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tên đại lý!")
                self._ten_dai_ly.setFocus()
                return
            
            if not self._dia_chi.text().strip():
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập địa chỉ!")
                self._dia_chi.setFocus()
                return
            
            # Get current settings for audit
            current_settings = self._settings_service.load_settings()
            
            # Build changes dict for audit
            changes = {}
            
            # Update settings
            new_values = {
                "ten_dai_ly": self._ten_dai_ly.text().strip(),
                "dia_chi_dai_ly": self._dia_chi.text().strip(),
                "so_dien_thoai_dai_ly": self._so_dien_thoai.text().strip(),
                "email_dai_ly": self._email.text().strip(),
                "logo_url": self._logo_path.text().strip() or None,
                "thoi_han_bh_default": str(self._thoi_han_bh.value()),
                "muc_toi_thieu_ton_kho": str(self._muc_toi_thieu.value()),
            }
            
            # Track changes for audit
            for key, new_value in new_values.items():
                old_value = getattr(current_settings, key, None) or ""
                if str(old_value) != str(new_value):
                    changes[key] = {"from": old_value, "to": new_value}
            
            # Update backup path
            backup_path = self._backup_path.text().strip()
            old_backup = self._settings_service.get_setting("backup_path") or ""
            if backup_path != old_backup:
                changes["backup_path"] = {"from": old_backup, "to": backup_path}
            
            # Save each setting
            for ma_settings, gia_tri in [
                ("ten_dai_ly", new_values["ten_dai_ly"]),
                ("dia_chi_dai_ly", new_values["dia_chi_dai_ly"]),
                ("so_dien_thoai_dai_ly", new_values["so_dien_thoai_dai_ly"]),
                ("email_dai_ly", new_values["email_dai_ly"]),
                ("logo_url", new_values["logo_url"]),
                ("thoi_han_bh_default", new_values["thoi_han_bh_default"]),
                ("muc_toi_thieu_ton_kho", new_values["muc_toi_thieu_ton_kho"]),
                ("backup_path", backup_path),
            ]:
                self._settings_service.update_setting(
                    ma_settings=ma_settings,
                    gia_tri=str(gia_tri) if gia_tri is not None else "",
                    updated_by=self._session.nhan_vien_id if self._session else None,
                )
            
            # Audit log for settings change
            if changes and self._session:
                self._log_settings_change(changes)
            
            # Update stored original values
            self._original_values = new_values.copy()
            self._original_values["backup_path"] = backup_path
            
            QMessageBox.information(
                self,
                "Thành công",
                "Đã lưu cài đặt hệ thống thành công!"
            )
            
            # Emit signal for any dependent UI updates
            self.settings_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể lưu cài đặt: {str(e)}"
            )
    
    def _log_settings_change(self, changes: dict):
        """Log settings changes to audit log.
        
        Args:
            changes: Dict of changed settings.
        """
        try:
            from app.application.services.audit_log_service import AuditLogService
            
            audit_service = AuditLogService(self._db_conn)
            audit_service.log_update(
                action="UPDATE_SYSTEM_SETTINGS",
                nhan_vien_id=self._session.nhan_vien_id if self._session else None,
                table="system_settings",
                record_id=None,
                before={k: v["from"] for k, v in changes.items()},
                after={k: v["to"] for k, v in changes.items()},
                changes={k: {"from": v["from"], "to": v["to"]} for k, v in changes.items()},
            )
        except Exception as e:
            # Don't fail the save if audit logging fails
            print(f"Audit logging failed: {e}")
