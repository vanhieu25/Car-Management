"""Lead form dialog - S-MK-03 part - Create/Edit lead.

Features:
- Form dialog for creating/editing lead
- Fields: ho_ten, so_dien_thoai, email, nguon, nhu_cau, chien_dich_id, nhan_vien_phu_trach_id
- Validate: ho_ten and so_dien_thoai required

References:
- BR-MK-02: Lead creation
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QMessageBox,
    QGroupBox, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.application.services.lead_service import (
    LeadService, LeadCreateData, LeadUpdateData,
    ValidationError, LeadNotFoundError
)
from app.application.services.chien_dich_mk_service import ChienDichMkService
from app.application.services.nhan_vien_service import NhanVienService
from app.application.services.session import CurrentSession


class LeadFormDialog(QDialog):
    """Dialog for adding or editing a lead.

    Signals:
        saved: Emitted when lead was saved successfully.
    """

    saved = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, lead=None, parent=None):
        """Initialize lead form dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            lead: Lead dict to edit, or None for adding new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = LeadService(db_conn)
        self._campaign_service = ChienDichMkService(db_conn)
        self._nv_service = NhanVienService(db_conn)
        self._lead = lead
        self._is_edit = lead is not None

        self._setup_ui()
        self._load_options()
        if self._is_edit:
            self._populate_form(lead)

    def _setup_ui(self):
        """Set up UI components."""
        title = "Thêm Lead mới" if not self._is_edit else f"Sửa Lead - {self._lead.get('ho_ten', '')}"
        self.setWindowTitle(title)
        self.setMinimumSize(550, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #1d1d1f;
            }
            QLineEdit, QComboBox, QTextEdit {
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 8px;
                background-color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus {
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

        # ho_ten
        self._ho_ten = QLineEdit()
        self._ho_ten.setPlaceholderText("Nhập họ tên")
        form_layout.addRow("Họ tên *:", self._ho_ten)

        # so_dien_thoai
        self._so_dt = QLineEdit()
        self._so_dt.setPlaceholderText("Nhập số điện thoại")
        form_layout.addRow("SĐT *:", self._so_dt)

        # email
        self._email = QLineEdit()
        self._email.setPlaceholderText("Nhập email (tùy chọn)")
        form_layout.addRow("Email:", self._email)

        # nguon
        self._nguon = QLineEdit()
        self._nguon.setPlaceholderText("Nguồn lead (VD: Facebook, Google)")
        form_layout.addRow("Nguồn:", self._nguon)

        # nhu_cau
        self._nhu_cau = QTextEdit()
        self._nhu_cau.setPlaceholderText("Mô tả nhu cầu...")
        self._nhu_cau.setMaximumHeight(60)
        form_layout.addRow("Nhu cầu:", self._nhu_cau)

        # chien_dich_id
        self._campaign_combo = QComboBox()
        form_layout.addRow("Chiến dịch:", self._campaign_combo)

        # nhan_vien_phu_trach_id
        self._nv_combo = QComboBox()
        form_layout.addRow("NV phụ trách:", self._nv_combo)

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

    def _load_options(self):
        """Load campaign and staff options."""
        # Load campaigns
        campaigns = self._campaign_service.get_all(limit=100)
        self._campaign_combo.clear()
        self._campaign_combo.addItem("-- Không chọn --", None)
        self._campaign_map = {}
        for c in campaigns:
            self._campaign_combo.addItem(c.get('ten_chien_dich', ''), c.get('id'))
            self._campaign_map[c.get('id')] = c.get('ten_chien_dich', '')

        # Load staff
        nhan_viens = self._nv_service.get_all()
        self._nv_combo.clear()
        self._nv_combo.addItem("-- Không gán --", None)
        self._nv_map = {}
        for nv in nhan_viens:
            if nv.get('trang_thai') == 'dang_lam':
                self._nv_combo.addItem(nv.get('ho_ten', ''), nv.get('id'))
                self._nv_map[nv.get('id')] = nv.get('ho_ten', '')

    def _populate_form(self, lead: dict):
        """Populate form with lead data."""
        self._ho_ten.setText(lead.get('ho_ten', ''))
        self._so_dt.setText(lead.get('so_dien_thoai', ''))
        self._email.setText(lead.get('email', ''))
        self._nguon.setText(lead.get('nguon', ''))
        self._nhu_cau.setPlainText(lead.get('nhu_cau', ''))

        # Set campaign
        cd_id = lead.get('chien_dich_id')
        if cd_id:
            for i in range(self._campaign_combo.count()):
                if self._campaign_combo.itemData(i) == cd_id:
                    self._campaign_combo.setCurrentIndex(i)
                    break

        # Set NV
        nv_id = lead.get('nhan_vien_phu_trach_id')
        if nv_id:
            for i in range(self._nv_combo.count()):
                if self._nv_combo.itemData(i) == nv_id:
                    self._nv_combo.setCurrentIndex(i)
                    break

    def _on_save(self):
        """Handle save button click."""
        ho_ten = self._ho_ten.text().strip()
        so_dt = self._so_dt.text().strip()
        email = self._email.text().strip()
        nguon = self._nguon.text().strip()
        nhu_cau = self._nhu_cau.toPlainText().strip()
        campaign_id = self._campaign_combo.currentData()
        nv_id = self._nv_combo.currentData()

        # Validate
        if not ho_ten:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập họ tên")
            self._ho_ten.setFocus()
            return

        if not so_dt:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập số điện thoại")
            self._so_dt.setFocus()
            return

        try:
            if self._is_edit:
                data = LeadUpdateData(
                    ho_ten=ho_ten,
                    so_dien_thoai=so_dt,
                    email=email,
                    nguon=nguon,
                    nhu_cau=nhu_cau,
                    nhan_vien_phu_trach_id=nv_id,
                    trang_thai=None,
                )
                self._service.update(self._lead['id'], data)
            else:
                data = LeadCreateData(
                    ho_ten=ho_ten,
                    so_dien_thoai=so_dt,
                    email=email,
                    nguon=nguon,
                    nhu_cau=nhu_cau,
                    chien_dich_id=campaign_id,
                    nhan_vien_phu_trach_id=nv_id,
                    created_by=self._session.user_id,
                )
                self._service.create(data)

            self.saved.emit()
            self.accept()

        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {e}")
