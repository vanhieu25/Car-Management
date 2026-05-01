"""Lead status dialog - Dialog to update lead status.

Features:
- Select new status for lead
- Valid transitions based on BR-MK-02
- Shows current status and allowed transitions

References:
- BR-MK-02: Lead status flow
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.application.services.lead_service import (
    LeadService, ValidationError, LeadNotFoundError
)
from app.application.services.session import CurrentSession


TRANG_THAI_LABELS = {
    "moi": "Mới",
    "dang_cham_soc": "Đang chăm sóc",
    "chuyen_doi": "Chuyển đổi",
    "tu_choi": "Từ chối",
}

STATUS_OPTIONS = [
    ("moi", "Mới"),
    ("dang_cham_soc", "Đang chăm sóc"),
    ("chuyen_doi", "Chuyển đổi"),
    ("tu_choi", "Từ chối"),
]


class LeadStatusDialog(QDialog):
    """Dialog for updating lead status.

    Signals:
        saved: Emitted when status was updated successfully.
    """

    saved = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, lead_id: int, parent=None):
        """Initialize lead status dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            lead_id: ID of the lead to update.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = LeadService(db_conn)
        self._lead_id = lead_id

        self._setup_ui()
        self._load_current_status()

    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Cập nhật trạng thái Lead")
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
        title_label = QLabel("Cập nhật trạng thái Lead")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        main_layout.addWidget(title_label)

        # Current status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Trạng thái hiện tại:"))
        self._current_status_label = QLabel("-")
        self._current_status_label.setStyleSheet("font-weight: 600; color: #1d1d1f;")
        status_layout.addWidget(self._current_status_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # New status
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Chuyển sang:"))
        self._status_combo = QComboBox()
        self._status_combo.addItems([v for k, v in STATUS_OPTIONS])
        form_layout.addWidget(self._status_combo)
        form_layout.addStretch()
        main_layout.addLayout(form_layout)

        # Note about allowed transitions
        self._note_label = QLabel("")
        self._note_label.setStyleSheet("color: #86868b; font-size: 12px;")
        main_layout.addWidget(self._note_label)

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

    def _load_current_status(self):
        """Load current lead status."""
        try:
            lead = self._service.get_by_id(self._lead_id)
            current_status = lead.get('trang_thai', 'moi')
            current_label = TRANG_THAI_LABELS.get(current_status, current_status)
            self._current_status_label.setText(current_label)

            # Show allowed transitions note
            valid_transitions = {
                'moi': ['dang_cham_soc', 'tu_choi'],
                'dang_cham_soc': ['chuyen_doi', 'tu_choi'],
                'chuyen_doi': [],
                'tu_choi': [],
            }
            allowed = valid_transitions.get(current_status, [])
            if allowed:
                allowed_labels = [TRANG_THAI_LABELS.get(s, s) for s in allowed]
                self._note_label.setText(f"Chuyển đổi hợp lệ: {', '.join(allowed_labels)}")
            else:
                self._note_label.setText("Đây là trạng thái cuối, không thể chuyển")

            # Set combo to current status as default
            for i, (k, v) in enumerate(STATUS_OPTIONS):
                if k == current_status:
                    self._status_combo.setCurrentIndex(i)
                    break

        except LeadNotFoundError:
            QMessageBox.warning(self, "Lỗi", "Lead không tồn tại")
            self.reject()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải thông tin: {e}")
            self.reject()

    def _on_save(self):
        """Handle save button click."""
        new_status_display = self._status_combo.currentText()
        new_status = next((k for k, v in STATUS_OPTIONS if v == new_status_display), 'moi')

        try:
            self._service.update_status(self._lead_id, new_status)
            self.saved.emit()
            self.accept()
        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật: {e}")
