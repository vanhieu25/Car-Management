"""Lead assign dialog - Dialog to assign lead to a staff member.

Features:
- Select staff member from dropdown
- Shows current assigned staff

References:
- BR-MK-02: Lead management
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.application.services.lead_service import (
    LeadService, LeadNotFoundError
)
from app.application.services.nhan_vien_service import NhanVienService
from app.application.services.session import CurrentSession


class LeadAssignDialog(QDialog):
    """Dialog for assigning lead to a staff member.

    Signals:
        saved: Emitted when lead was assigned successfully.
    """

    saved = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, lead_id: int, parent=None):
        """Initialize lead assign dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            lead_id: ID of the lead to assign.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = LeadService(db_conn)
        self._nv_service = NhanVienService(db_conn)
        self._lead_id = lead_id

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Gán nhân viên phụ trách")
        self.setMinimumSize(400, 200)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #1d1d1f;
            }
            QComboBox {
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 8px;
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

        # Title
        title_label = QLabel("Gán nhân viên phụ trách")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        main_layout.addWidget(title_label)

        # Current assigned
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("NV hiện tại:"))
        self._current_nv_label = QLabel("-")
        self._current_nv_label.setStyleSheet("font-weight: 600; color: #1d1d1f;")
        current_layout.addWidget(self._current_nv_label)
        current_layout.addStretch()
        main_layout.addLayout(current_layout)

        # Staff dropdown
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Gán cho NV:"))
        self._nv_combo = QComboBox()
        self._nv_combo.setMinimumWidth(200)
        form_layout.addWidget(self._nv_combo)
        form_layout.addStretch()
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

    def _load_data(self):
        """Load staff list and current assignment."""
        try:
            # Get lead
            lead = self._service.get_by_id(self._lead_id)
            current_nv_id = lead.get('nhan_vien_phu_trach_id')
            current_nv_ten = lead.get('nhan_vien_ten', '-') or '-'
            self._current_nv_label.setText(current_nv_ten)

            # Get all active staff
            nhan_viens = self._nv_service.get_all()
            self._nv_combo.clear()
            self._nv_map = {}

            self._nv_combo.addItem("-- Không gán --", None)
            for nv in nhan_viens:
                if nv.get('trang_thai') == 'dang_lam':
                    self._nv_combo.addItem(nv.get('ho_ten', ''), nv.get('id'))
                    self._nv_map[nv.get('id')] = nv.get('ho_ten', '')

            # Set current assignment
            if current_nv_id:
                for i in range(self._nv_combo.count()):
                    if self._nv_combo.itemData(i) == current_nv_id:
                        self._nv_combo.setCurrentIndex(i)
                        break

        except LeadNotFoundError:
            QMessageBox.warning(self, "Lỗi", "Lead không tồn tại")
            self.reject()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {e}")
            self.reject()

    def _on_save(self):
        """Handle save button click."""
        nv_id = self._nv_combo.currentData()

        try:
            if nv_id is None:
                # Just close without saving if "Không gán"
                self.accept()
            else:
                self._service.assign_to_nv(self._lead_id, nv_id)
                self.saved.emit()
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể gán nhân viên: {e}")
