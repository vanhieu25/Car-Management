"""Campaign form dialog - S-MK-02 - Create/Edit marketing campaign.

Features:
- Form dialog for creating/editing campaign
- Fields: ten_chien_dich, kenh_tiep_thi, ngay_bat_dau, ngay_ket_thuc,
  ngan_sach, muc_tieu, so_luong_lead_muc_tieu
- Validate: ngay_ket_thuc >= ngay_bat_dau, ngan_sach >= 0
- Buttons: Save, Cancel

References:
- BR-MK-01: Campaign lifecycle management
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QMessageBox,
    QGroupBox, QComboBox, QDateEdit,
    QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from app.application.services.chien_dich_mk_service import (
    ChienDichMkService,
    ChienDichMkCreateData,
    ChienDichMkUpdateData,
    ValidationError,
    ChienDichMkNotFoundError,
)
from app.application.services.session import CurrentSession


KENH_OPTIONS = [
    ("facebook", "Facebook"),
    ("google_ads", "Google Ads"),
    ("youtube", "YouTube"),
    ("truyen_hinh", "Truyền hình"),
    ("bao_chi", "Báo chí"),
    ("truyen_mieng", "Truyền miệng"),
    ("khac", "Khác"),
]

KENH_DISPLAY = {k: v for k, v in KENH_OPTIONS}


class CampaignFormDialog(QDialog):
    """Dialog for adding or editing a marketing campaign.

    Signals:
        saved: Emitted when campaign was saved successfully.
    """

    saved = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, campaign=None, parent=None):
        """Initialize campaign form dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            campaign: Campaign dict to edit, or None for adding new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = ChienDichMkService(db_conn)
        self._campaign = campaign
        self._is_edit = campaign is not None

        self._setup_ui()

        if self._is_edit:
            self._populate_form(campaign)

    def _setup_ui(self):
        """Set up UI components."""
        title = "Thêm chiến dịch mới" if not self._is_edit else f"Sửa chiến dịch - {self._campaign.get('ten_chien_dich', '')}"
        self.setWindowTitle(title)
        self.setMinimumSize(550, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #1d1d1f;
            }
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QTextEdit {
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 8px;
                background-color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 2px solid #0071e3;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton#save_btn {
                background-color: #0071e3;
                color: white;
                border: none;
            }
            QPushButton#save_btn:hover { background-color: #0077ed; }
            QPushButton#cancel_btn {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
            }
            QPushButton#cancel_btn:hover { background-color: #e8e8ed; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        main_layout.addWidget(title_label)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # ten_chien_dich
        self._ten_edit = QLineEdit()
        self._ten_edit.setPlaceholderText("Nhập tên chiến dịch")
        form_layout.addRow("Tên chiến dịch *:", self._ten_edit)

        # kenh_tiep_thi
        self._kenh_combo = QComboBox()
        self._kenh_combo.addItems([v for k, v in KENH_OPTIONS])
        form_layout.addRow("Kênh tiếp thị *:", self._kenh_combo)

        # ngay_bat_dau
        self._ngay_bat_dau = QDateEdit()
        self._ngay_bat_dau.setCalendarPopup(True)
        self._ngay_bat_dau.setDate(QDate.currentDate())
        form_layout.addRow("Ngày bắt đầu *:", self._ngay_bat_dau)

        # ngay_ket_thuc
        self._ngay_ket_thuc = QDateEdit()
        self._ngay_ket_thuc.setCalendarPopup(True)
        self._ngay_ket_thuc.setDate(QDate.currentDate().addMonths(1))
        form_layout.addRow("Ngày kết thúc *:", self._ngay_ket_thuc)

        # ngan_sach
        self._ngan_sach = QSpinBox()
        self._ngan_sach.setRange(0, 999999999)
        self._ngan_sach.setPrefix("")
        self._ngan_sach.setSuffix(" VNĐ")
        self._ngan_sach.setValue(0)
        form_layout.addRow("Ngân sách:", self._ngan_sach)

        # so_luong_lead_muc_tieu
        self._lead_muc_tieu = QSpinBox()
        self._lead_muc_tieu.setRange(0, 99999)
        self._lead_muc_tieu.setValue(0)
        form_layout.addRow("Lead mục tiêu:", self._lead_muc_tieu)

        # muc_tieu
        self._muc_tieu = QTextEdit()
        self._muc_tieu.setPlaceholderText("Mô tả mục tiêu chiến dịch...")
        self._muc_tieu.setMaximumHeight(80)
        form_layout.addRow("Mục tiêu:", self._muc_tieu)

        main_layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._btn_cancel = QPushButton("Hủy")
        self._btn_cancel.setObjectName("cancel_btn")
        self._btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self._btn_cancel)

        self._btn_save = QPushButton("Lưu")
        self._btn_save.setObjectName("save_btn")
        self._btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self._btn_save)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def _populate_form(self, campaign: dict):
        """Populate form with campaign data."""
        self._ten_edit.setText(campaign.get('ten_chien_dich', ''))
        
        # Set kenh
        kenh_val = campaign.get('kenh_tiep_thi', 'facebook')
        for i, (k, v) in enumerate(KENH_OPTIONS):
            if k == kenh_val:
                self._kenh_combo.setCurrentIndex(i)
                break
        
        # Set dates
        if campaign.get('ngay_bat_dau'):
            self._ngay_bat_dau.setDate(QDate.fromString(campaign['ngay_bat_dau'], "yyyy-MM-dd"))
        if campaign.get('ngay_ket_thuc'):
            self._ngay_ket_thuc.setDate(QDate.fromString(campaign['ngay_ket_thuc'], "yyyy-MM-dd"))
        
        self._ngan_sach.setValue(campaign.get('ngan_sach', 0))
        self._lead_muc_tieu.setValue(campaign.get('so_luong_lead_muc_tieu', 0))
        self._muc_tieu.setPlainText(campaign.get('muc_tieu', ''))

    def _on_save(self):
        """Handle save button click."""
        # Get values
        ten = self._ten_edit.text().strip()
        kenh_display = self._kenh_combo.currentText()
        kenh_val = next((k for k, v in KENH_OPTIONS if v == kenh_display), 'facebook')
        ngay_bat_dau = self._ngay_bat_dau.date().toString("yyyy-MM-dd")
        ngay_ket_thuc = self._ngay_ket_thuc.date().toString("yyyy-MM-dd")
        ngan_sach = self._ngan_sach.value()
        lead_muc_tieu = self._lead_muc_tieu.value()
        muc_tieu = self._muc_tieu.toPlainText().strip()

        # Validate
        if not ten:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tên chiến dịch")
            self._ten_edit.setFocus()
            return

        if self._ngay_ket_thuc.date() < self._ngay_bat_dau.date():
            QMessageBox.warning(self, "Cảnh báo", "Ngày kết thúc phải >= ngày bắt đầu")
            return

        try:
            if self._is_edit:
                data = ChienDichMkUpdateData(
                    ten_chien_dich=ten,
                    kenh_tiep_thi=kenh_val,
                    ngay_bat_dau=ngay_bat_dau,
                    ngay_ket_thuc=ngay_ket_thuc,
                    ngan_sach=ngan_sach,
                    muc_tieu=muc_tieu,
                    so_luong_lead_muc_tieu=lead_muc_tieu,
                )
                self._service.update(self._campaign['id'], data)
            else:
                data = ChienDichMkCreateData(
                    ten_chien_dich=ten,
                    kenh_tiep_thi=kenh_val,
                    ngay_bat_dau=ngay_bat_dau,
                    ngay_ket_thuc=ngay_ket_thuc,
                    ngan_sach=ngan_sach,
                    muc_tieu=muc_tieu,
                    so_luong_lead_muc_tieu=lead_muc_tieu,
                    created_by=self._session.user_id,
                )
                self._service.create(data)

            self.saved.emit()
            self.accept()

        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {e}")
