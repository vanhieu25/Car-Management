"""Accessory form dialog - S-PK-02 - Add/Edit accessory form.

Features:
- Form fields: ma_pk (auto-generate), ten_pk, phan_loai (dropdown),
  mo_ta, gia_ban, ton_kho
- Validate on save
- Auto-generate ma_pk code
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QFormLayout, QGroupBox,
    QMessageBox, QDoubleSpinBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.application.services.phu_kien_service import (
    PhuKienService,
    PhuKienCreateData,
    PhuKienUpdateData,
    PhuKienNotFoundError,
    ValidationError,
    DuplicateMaPkError,
)
from app.domain.entities import PhuKien


PHAN_LOAI_OPTIONS = [
    ("noi_that", "Nội thất"),
    ("ngoai_that", "Ngoại thất"),
    ("dien_tu", "Điện tử"),
    ("bao_ve", "Bảo vệ"),
    ("trang_tri", "Trang trí"),
]


class AccessoryFormDialog(QDialog):
    """Accessory form dialog - S-PK-02.

    Signals:
        saved: Dialog saved successfully.
    """

    saved = pyqtSignal()

    def __init__(self, db_conn, session, pk_id: int = None, parent=None):
        """Initialize accessory form dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            pk_id: Accessory ID to edit (None for create).
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._pk_service = PhuKienService(db_conn, session)
        self._pk_id = pk_id
        self._is_edit = pk_id is not None

        self._pk: PhuKien = None

        if self._is_edit:
            self._pk = self._pk_service.get_by_id(pk_id)
            if not self._pk:
                raise PhuKienNotFoundError(f"Không tìm thấy phụ kiện với ID {pk_id}")

        self._setup_ui()
        self._populate_form()

    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Thêm phụ kiện" if not self._is_edit else f"Sửa phụ kiện: {self._pk.ten_pk if self._pk else ''}")
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Form group
        form_group = QGroupBox()
        form_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                margin-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 12px;
                font-weight: 600;
                font-size: 15px;
                color: #1d1d1f;
            }
        """)
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Mã PK (auto-generated, read-only)
        self._ma_pk_label = QLabel("PK-00001")
        self._ma_pk_label.setStyleSheet("""
            QLabel {
                padding: 8px 12px;
                background-color: #f5f5f7;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-weight: 600;
                color: #86868b;
            }
        """)
        form_layout.addRow("Mã PK *:", self._ma_pk_label)

        # Tên phụ kiện
        self._ten_pk_input = QLineEdit()
        self._ten_pk_input.setPlaceholderText("Nhập tên phụ kiện (ít nhất 3 ký tự)")
        self._ten_pk_input.setStyleSheet("""
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
        form_layout.addRow("Tên phụ kiện *:", self._ten_pk_input)

        # Phân loại
        self._phan_loai_combo = QComboBox()
        for value, label in PHAN_LOAI_OPTIONS:
            self._phan_loai_combo.addItem(label, value)
        self._phan_loai_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        form_layout.addRow("Phân loại *:", self._phan_loai_combo)

        # Giá bán
        self._gia_ban_input = QSpinBox()
        self._gia_ban_input.setMinimum(0)
        self._gia_ban_input.setMaximum(999999999)
        self._gia_ban_input.setSuffix(" đ")
        self._gia_ban_input.setStyleSheet("""
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
        form_layout.addRow("Giá bán *:", self._gia_ban_input)

        # Tồn kho
        self._ton_kho_input = QSpinBox()
        self._ton_kho_input.setMinimum(0)
        self._ton_kho_input.setMaximum(999999999)
        self._ton_kho_input.setStyleSheet("""
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
        form_layout.addRow("Tồn kho *:", self._ton_kho_input)

        # Mô tả
        self._mo_ta_input = QTextEdit()
        self._mo_ta_input.setPlaceholderText("Nhập mô tả phụ kiện (tùy chọn)")
        self._mo_ta_input.setMaximumHeight(100)
        self._mo_ta_input.setStyleSheet("""
            QTextEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QTextEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        form_layout.addRow("Mô tả:", self._mo_ta_input)

        layout.addWidget(form_group)

        # Note about required fields
        note_label = QLabel("* Trường bắt buộc")
        note_label.setStyleSheet("color: #86868b; font-size: 13px;")
        layout.addWidget(note_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_btn = QPushButton("Hủy")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton("Lưu")
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self._save_btn)

        layout.addLayout(button_layout)

    def _populate_form(self):
        """Populate form with existing data for edit mode."""
        if self._is_edit and self._pk:
            self._ma_pk_label.setText(self._pk.ma_pk)
            self._ten_pk_input.setText(self._pk.ten_pk)

            # Set phan_loai
            for i, (value, label) in enumerate(PHAN_LOAI_OPTIONS):
                if value == self._pk.phan_loai:
                    self._phan_loai_combo.setCurrentIndex(i)
                    break

            self._gia_ban_input.setValue(self._pk.gia_ban)
            self._ton_kho_input.setValue(self._pk.ton_kho)
            self._mo_ta_input.setPlainText(self._pk.mo_ta or "")
        else:
            # Generate new ma_pk for create mode
            ma_pk = self._pk_service._generate_ma_pk()
            self._ma_pk_label.setText(ma_pk)

    def _on_save(self):
        """Handle save button click."""
        # Get values
        ten_pk = self._ten_pk_input.text().strip()
        phan_loai = self._phan_loai_combo.currentData()
        gia_ban = self._gia_ban_input.value()
        ton_kho = self._ton_kho_input.value()
        mo_ta = self._mo_ta_input.toPlainText().strip()

        try:
            if self._is_edit:
                # Update existing
                data = PhuKienUpdateData(
                    ten_pk=ten_pk,
                    phan_loai=phan_loai,
                    gia_ban=gia_ban,
                    ton_kho=ton_kho,
                    mo_ta=mo_ta,
                )
                self._pk_service.update(self._pk_id, data)
            else:
                # Create new
                data = PhuKienCreateData(
                    ten_pk=ten_pk,
                    phan_loai=phan_loai,
                    gia_ban=gia_ban,
                    ton_kho=ton_kho,
                    mo_ta=mo_ta,
                    created_by=self._session.user_id if self._session else None,
                )
                self._pk_service.create(data)

            self.saved.emit()
            self.accept()

        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi validation", str(e))
        except DuplicateMaPkError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")

    def get_pk_id(self):
        """Get the saved pk_id."""
        return self._pk_id if self._is_edit else None
