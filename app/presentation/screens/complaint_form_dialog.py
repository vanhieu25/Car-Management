"""Complaint form dialog - S-KN-01 part - Create complaint.

Features:
- Form: khach_hang, hop_dong (optional), tieu_de, noi_dung, muc_do, nguon_goc
- Validate: khach_hang_id required, muc_do in ['thap', 'trung_binh', 'cao']

References:
- BR-KN-01: Complaint creation
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QMessageBox,
    QGroupBox, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.application.services.khieu_nai_service import (
    KhieuNaiService, KhieuNaiCreateData,
    ValidationError, KhieuNaiNotFoundError
)
from app.application.services.khach_hang_service import KhachHangService
from app.application.services.hop_dong_service import HopDongService
from app.application.services.session import CurrentSession


MUC_DO_OPTIONS = [
    ("thap", "Thấp"),
    ("trung_binh", "Trung bình"),
    ("cao", "Cao"),
]
MUC_DO_DISPLAY = {k: v for k, v in MUC_DO_OPTIONS}

NGUON_GOC_OPTIONS = [
    ("chat_luong_xe", "Chất lượng xe"),
    ("dich_vu", "Dịch vụ"),
    ("bao_hanh", "Bảo hành"),
    ("khac", "Khác"),
]
NGUON_GOC_DISPLAY = {k: v for k, v in NGUON_GOC_OPTIONS}


class ComplaintFormDialog(QDialog):
    """Dialog for creating a complaint.

    Signals:
        saved: Emitted when complaint was created successfully.
    """

    saved = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize complaint form dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = KhieuNaiService(db_conn)
        self._kh_service = KhachHangService(db_conn)
        self._hd_service = HopDongService(db_conn)

        self._setup_ui()
        self._load_options()

    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Tạo khiếu nại mới")
        self.setMinimumSize(550, 550)
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
        title_label = QLabel("Tạo khiếu nại mới")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        main_layout.addWidget(title_label)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Customer
        self._kh_combo = QComboBox()
        self._kh_combo.setMinimumWidth(300)
        form_layout.addRow("Khách hàng *:", self._kh_combo)

        # Contract (optional)
        self._hd_combo = QComboBox()
        self._hd_combo.setMinimumWidth(300)
        form_layout.addRow("Hợp đồng:", self._hd_combo)

        # Title
        self._tieu_de = QLineEdit()
        self._tieu_de.setPlaceholderText("Nhập tiêu đề khiếu nại")
        form_layout.addRow("Tiêu đề *:", self._tieu_de)

        # Priority
        self._muc_do_combo = QComboBox()
        self._muc_do_combo.addItems([v for k, v in MUC_DO_OPTIONS])
        form_layout.addRow("Mức độ *:", self._muc_do_combo)

        # Source
        self._nguon_goc_combo = QComboBox()
        self._nguon_goc_combo.addItems([v for k, v in NGUON_GOC_OPTIONS])
        form_layout.addRow("Nguồn gốc:", self._nguon_goc_combo)

        # Content
        form_layout.addRow("Nội dung *:", None)
        self._noi_dung = QTextEdit()
        self._noi_dung.setPlaceholderText("Mô tả chi tiết khiếu nại...")
        self._noi_dung.setMaximumHeight(120)
        form_layout.addRow("", self._noi_dung)

        main_layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._btn_cancel = QPushButton("Hủy")
        self._btn_cancel.setObjectName("cancel_btn")
        self._btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self._btn_cancel)

        self._btn_save = QPushButton("Tạo khiếu nại")
        self._btn_save.setObjectName("save_btn")
        self._btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self._btn_save)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def _load_options(self):
        """Load customer and contract options."""
        # Load customers
        customers = self._kh_service.get_all(limit=100)
        self._kh_combo.clear()
        self._kh_combo.addItem("-- Chọn khách hàng --", None)
        self._kh_map = {}
        for kh in customers:
            self._kh_combo.addItem(
                f"{kh.ho_ten or ''} - {kh.so_dien_thoai or ''}",
                kh.id
            )
            self._kh_map[kh.id] = kh

        # Load contracts (all)
        contracts = self._hd_service.get_all(limit=200)
        self._hd_combo.clear()
        self._hd_combo.addItem("-- Không có HĐ --", None)
        self._hd_map = {}
        for hd in contracts:
            if hd.trang_thai not in ('da_huy', 'tu_choi'):
                display = f"{hd.ma_hop_dong or ''} - {hd.khach_hang_id or ''}"
                self._hd_combo.addItem(display, hd.id)
                self._hd_map[hd.id] = hd

    def _on_save(self):
        """Handle save button click."""
        kh_id = self._kh_combo.currentData()
        hd_id = self._hd_combo.currentData()
        tieu_de = self._tieu_de.text().strip()
        noi_dung = self._noi_dung.toPlainText().strip()

        # Get muc_do
        muc_do_display = self._muc_do_combo.currentText()
        muc_do = next((k for k, v in MUC_DO_OPTIONS if v == muc_do_display), 'trung_binh')

        # Get nguon_goc
        nguon_display = self._nguon_goc_combo.currentText()
        nguon_goc = next((k for k, v in NGUON_GOC_OPTIONS if v == nguon_display), None)

        # Validate
        if not kh_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn khách hàng")
            return

        if not tieu_de:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tiêu đề khiếu nại")
            self._tieu_de.setFocus()
            return

        if not noi_dung:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập nội dung khiếu nại")
            return

        try:
            data = KhieuNaiCreateData(
                khach_hang_id=kh_id,
                hop_dong_id=hd_id,
                tieu_de=tieu_de,
                noi_dung=noi_dung,
                muc_do=muc_do,
                nguon_goc=nguon_goc,
                created_by=self._session.user_id,
            )
            self._service.create(data)

            self.saved.emit()
            self.accept()

        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo: {e}")
