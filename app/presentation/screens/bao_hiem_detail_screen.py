"""Insurance detail screen - view insurance details.

Shows:
- Insurance info (policy number, type, dates, fee)
- Warranty info it's linked to
- Customer and vehicle info
- Actions: Edit, Renew, Cancel
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QTableWidget, QTableWidgetItem,
    QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.application.services.bao_hiem_service import BaoHiemService
from app.application.services.session import CurrentSession


class BaoHiemDetailScreen(QWidget):
    """Insurance detail screen.

    Signals:
        edit_insurance_clicked(bh_id: int): User wants to edit insurance.
        closed: Screen is being closed.
        action_completed: An action was performed that requires refresh.
    """

    closed = pyqtSignal()
    action_completed = pyqtSignal()
    edit_insurance_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, insurance_id: int, parent=None):
        """Initialize insurance detail screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            insurance_id: Insurance ID to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._insurance_id = insurance_id
        self._service = BaoHiemService(db_conn)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        self._back_btn = QPushButton("← Quay lại")
        self._back_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._back_btn.clicked.connect(self._on_back)
        header_layout.addWidget(self._back_btn)

        header_layout.addStretch()

        self._title = QLabel("Chi tiết bảo hiểm")
        self._title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(self._title)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)

        # Insurance info section
        info_group = QGroupBox("Thông tin bảo hiểm")
        info_group.setObjectName("info_section")
        info_group.setStyleSheet("""
            QGroupBox#info_section {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background-color: white;
            }
            QGroupBox#info_section::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                font-weight: 600;
                font-size: 16px;
                color: #1d1d1f;
            }
        """)

        info_layout = QVBoxLayout(info_group)

        # Row 1: Policy number, Type
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Số Policy:"))
        self._policy_label = QLabel("")
        self._policy_label.setStyleSheet("font-weight: 600;")
        row1.addWidget(self._policy_label)
        row1.addSpacing(40)
        row1.addWidget(QLabel("Loại bảo hiểm:"))
        self._loai_bh_label = QLabel("")
        self._loai_bh_label.setStyleSheet("font-weight: 600;")
        row1.addWidget(self._loai_bh_label)
        row1.addStretch()
        info_layout.addLayout(row1)

        # Row 2: Dates
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Ngày mua:"))
        self._ngay_mua_label = QLabel("")
        row2.addWidget(self._ngay_mua_label)
        row2.addSpacing(40)
        row2.addWidget(QLabel("Ngày hết hạn:"))
        self._ngay_het_han_label = QLabel("")
        row2.addWidget(self._ngay_het_han_label)
        row2.addStretch()
        info_layout.addLayout(row2)

        # Row 3: Fee, Status
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Phí bảo hiểm:"))
        self._phi_bh_label = QLabel("")
        self._phi_bh_label.setStyleSheet("font-weight: 600; color: #34c759;")
        row3.addWidget(self._phi_bh_label)
        row3.addSpacing(40)
        row3.addWidget(QLabel("Trạng thái:"))
        self._trang_thai_label = QLabel("")
        row3.addWidget(self._trang_thai_label)
        row3.addStretch()
        info_layout.addLayout(row3)

        # Row 4: Ngay hieu luc
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Ngày hiệu lực:"))
        self._ngay_hieu_luc_label = QLabel("")
        row4.addWidget(self._ngay_hieu_luc_label)
        row4.addStretch()
        info_layout.addLayout(row4)

        # Row 5: Insurance company
        row5 = QHBoxLayout()
        row5.addWidget(QLabel("Công ty BH:"))
        self._cong_ty_bh_label = QLabel("")
        row5.addWidget(self._cong_ty_bh_label)
        row5.addStretch()
        info_layout.addLayout(row5)

        content_layout.addWidget(info_group)

        # Warranty link section
        warranty_group = QGroupBox("Bảo hành liên kết")
        warranty_group.setObjectName("warranty_section")
        warranty_group.setStyleSheet(info_group.styleSheet().replace("info_section", "warranty_section"))
        warranty_layout = QVBoxLayout(warranty_group)
        self._warranty_info_label = QLabel("")
        warranty_layout.addWidget(self._warranty_info_label)
        content_layout.addWidget(warranty_group)

        # Vehicle info section
        vehicle_group = QGroupBox("Thông tin xe")
        vehicle_group.setObjectName("vehicle_section")
        vehicle_group.setStyleSheet(info_group.styleSheet().replace("info_section", "vehicle_section"))
        vehicle_layout = QVBoxLayout(vehicle_group)
        self._vehicle_info_label = QLabel("")
        vehicle_layout.addWidget(self._vehicle_info_label)
        content_layout.addWidget(vehicle_group)

        # Notes section
        notes_group = QGroupBox("Ghi chú")
        notes_group.setObjectName("notes_section")
        notes_group.setStyleSheet(info_group.styleSheet().replace("info_section", "notes_section"))
        notes_layout = QVBoxLayout(notes_group)
        self._notes_label = QLabel("")
        self._notes_label.setWordWrap(True)
        notes_layout.addWidget(self._notes_label)
        content_layout.addWidget(notes_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll, stretch=1)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self._edit_btn = QPushButton("Sửa")
        self._edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._edit_btn.clicked.connect(self._on_edit)
        action_layout.addWidget(self._edit_btn)

        self._renew_btn = QPushButton("Gia hạn")
        self._renew_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2da44e;
            }
        """)
        self._renew_btn.clicked.connect(self._on_renew)
        action_layout.addWidget(self._renew_btn)

        self._cancel_btn = QPushButton("Hủy BH")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #d63030;
            }
        """)
        self._cancel_btn.clicked.connect(self._on_cancel)
        action_layout.addWidget(self._cancel_btn)

        layout.addLayout(action_layout)

    def _load_data(self):
        """Load insurance data."""
        insurance = self._service.get_by_id(self._insurance_id)
        if not insurance:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy bảo hiểm")
            self._on_back()
            return

        # Policy number
        self._policy_label.setText(insurance.so_policy or "(Chưa có)")

        # Insurance type
        self._loai_bh_label.setText(BaoHiemService.get_loai_bh_label(insurance.loai_bh))

        # Dates
        self._ngay_mua_label.setText(insurance.ngay_mua[:10] if insurance.ngay_mua else "")
        self._ngay_het_han_label.setText(insurance.ngay_het_han[:10] if insurance.ngay_het_han else "")

        # Fee
        phi_bh = insurance.phi_bh or 0
        self._phi_bh_label.setText(f"{phi_bh:,} đ")

        # Status
        trang_thai = insurance.trang_thai
        trang_thai_text = BaoHiemService.get_trang_thai_label(trang_thai)
        self._trang_thai_label.setText(trang_thai_text)

        # Ngay hieu luc
        self._ngay_hieu_luc_label.setText(insurance.ngay_hieu_luc[:10] if insurance.ngay_hieu_luc else "")

        # Insurance company
        if insurance.cong_ty_bh_id:
            cursor = self._db_conn.execute(
                "SELECT ma_cty, ten_cty FROM cong_ty_bh WHERE id = ?",
                (insurance.cong_ty_bh_id,)
            )
            row = cursor.fetchone()
            if row:
                self._cong_ty_bh_label.setText(f"{row[0]} - {row[1]}")
            else:
                self._cong_ty_bh_label.setText("Không rõ")
        else:
            self._cong_ty_bh_label.setText("(Chưa chọn)")

        # Warranty info
        cursor = self._db_conn.execute(
            "SELECT bh.id, kh.ho_ten, kh.so_dien_thoai FROM bao_hanh bh "
            "JOIN khach_hang kh ON bh.khach_hang_id = kh.id "
            "WHERE bh.id = ?",
            (insurance.bao_hanh_id,)
        )
        row = cursor.fetchone()
        if row:
            self._warranty_info_label.setText(
                f"BH-{row[0]} - Khách hàng: {row[1]} (DT: {row[2] or 'N/A'})"
            )
        else:
            self._warranty_info_label.setText("Không tìm thấy thông tin bảo hành")

        # Vehicle info
        cursor = self._db_conn.execute(
            "SELECT x.ma_xe, x.hang, x.dong_xe, bhhh.so_khung, bhhh.so_may, bhhh.is_external "
            "FROM bao_hanh bhhh "
            "LEFT JOIN xe x ON bhhh.xe_id = x.id "
            "WHERE bhhh.id = ?",
            (insurance.bao_hanh_id,)
        )
        row = cursor.fetchone()
        if row:
            ma_xe, hang, dong_xe, so_khung, so_may, is_external = row
            if is_external:
                self._vehicle_info_label.setText("Xe ngoài (không mua tại đại lý)")
            elif ma_xe:
                self._vehicle_info_label.setText(
                    f"Mã xe: {ma_xe} | {hang or ''} {dong_xe or ''} | Khung: {so_khung or 'N/A'} | Máy: {so_may or 'N/A'}"
                )
            else:
                self._vehicle_info_label.setText(
                    f"Khung: {so_khung or 'N/A'} | Máy: {so_may or 'N/A'}"
                )
        else:
            self._vehicle_info_label.setText("Không tìm thấy thông tin xe")

        # Notes
        self._notes_label.setText(insurance.ghi_chu or "Không có ghi chú")

        # Disable actions based on status
        if trang_thai != "con_hieu_luc":
            self._renew_btn.setEnabled(False)
            self._cancel_btn.setEnabled(False)

        self._title.setText(f"Chi tiết bảo hiểm #{self._insurance_id}")

    def _on_back(self):
        """Handle back button."""
        self.closed.emit()

    def _on_edit(self):
        """Handle edit button."""
        self.edit_insurance_clicked.emit(self._insurance_id)

    def _on_renew(self):
        """Handle renew button."""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        from datetime import datetime

        phi_moi, ok = QInputDialog.getInt(self, "Gia hạn bảo hiểm", "Phí bảo hiểm mới (VNĐ):", value=0, min=0, max=999999999)
        if not ok:
            return

        han_moi, ok = QInputDialog.getText(self, "Gia hạn bảo hiểm", "Ngày hết hạn mới (YYYY-MM-DD):", text=datetime.now().strftime("%Y-%m-%d"))
        if not ok or not han_moi:
            return

        try:
            self._service.renew(self._insurance_id, han_moi, phi_moi, self._session.nhan_vien_id)
            QMessageBox.information(self, "Thành công", "Đã gia hạn bảo hiểm thành công!")
            self._load_data()
            self.action_completed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể gia hạn: {str(e)}")

    def _on_cancel(self):
        """Handle cancel button."""
        reply = QMessageBox.question(
            self, "Xác nhận",
            "Bạn có chắc muốn hủy bảo hiểm này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from PyQt6.QtWidgets import QInputDialog
            ly_do, ok = QInputDialog.getText(self, "Lý do hủy", "Nhập lý do hủy bảo hiểm:")
            if ok and ly_do:
                try:
                    self._service.cancel(
                        self._insurance_id,
                        ly_do,
                        self._session.nhan_vien_id
                    )
                    QMessageBox.information(self, "Thành công", "Đã hủy bảo hiểm")
                    self._load_data()
                    self.action_completed.emit()
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Không thể hủy: {str(e)}")