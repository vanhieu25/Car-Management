"""Warranty request form dialog - S-BH-03 - Create warranty request.

Features:
  - ngay_yeu_cau: date picker
  - loai_yeu_cau: dropdown (bao_duong, sua_chua, thay_the)
  - phan_loai: mien_phi/tinh_phi
  - chi_phi_du_kien: number input (0 for mien_phi)
  - nhan_vien_id: dropdown of technicians
- Validation: ngay_yeu_cau <= ngay_ket_thuc BH

References:
- BR-BH-04: Classification (mien_phi/tinh_phi)
- BR-BH-05: Request status starts as 'dang_xu_ly'
- BR-BH-06: chi_phi = 0 for mien_phi
"""

from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox, QDialog, QComboBox,
    QDateEdit, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from app.application.services.bao_hanh_service import BaoHanhService, BaoHanhYeuCauData
from app.application.services.session import CurrentSession
from app.presentation.widgets.inputs import InlineNumericEdit


class WarrantyRequestFormDialog(QDialog):
    """Dialog for creating/editing warranty request - S-BH-03.
    
    Signals:
        request_created: Emitted when request was created successfully.
    """
    
    request_created = pyqtSignal()
    
    def __init__(self, db_conn, session: CurrentSession, bh_id: int, parent=None):
        """Initialize warranty request form dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            bh_id: Warranty ID.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bh_service = BaoHanhService(db_conn)
        self._bh_id = bh_id
        self._max_date = None

        self._setup_ui()
        self._load_warranty_info()
    
    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Tạo yêu cầu bảo hành")
        self.setMinimumWidth(600)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title_label = QLabel("Tạo yêu cầu bảo hành mới")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(title_label)
        
        # Warranty info
        self._bh_info_label = QLabel()
        self._bh_info_label.setStyleSheet("font-size: 13px; color: #86868b; padding: 8px; background: #f5f5f7; border-radius: 6px;")
        layout.addWidget(self._bh_info_label)
        
        # Form fields
        # Ngay yeu cau
        ngay_layout = QHBoxLayout()
        ngay_layout.addWidget(QLabel("Ngày yêu cầu:"))
        self._ngay_yeu_cau = QDateEdit()
        self._ngay_yeu_cau.setDate(QDate.currentDate())
        self._ngay_yeu_cau.setCalendarPopup(True)
        self._ngay_yeu_cau.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        ngay_layout.addWidget(self._ngay_yeu_cau)
        ngay_layout.addStretch()
        layout.addLayout(ngay_layout)
        
        # Loai yeu cau
        loai_layout = QHBoxLayout()
        loai_layout.addWidget(QLabel("Loại yêu cầu:"))
        self._loai_yeu_cau = QComboBox()
        self._loai_yeu_cau.addItem("Sửa chữa", "sua_chua")
        self._loai_yeu_cau.addItem("Bảo dưỡng", "bao_duong")
        self._loai_yeu_cau.addItem("Thay thế", "thay_the")
        self._loai_yeu_cau.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                min-width: 150px;
            }
        """)
        loai_layout.addWidget(self._loai_yeu_cau)
        loai_layout.addStretch()
        layout.addLayout(loai_layout)

        # Phan loai (selectable)
        phan_loai_layout = QHBoxLayout()
        phan_loai_layout.addWidget(QLabel("Phân loại:"))
        self._phan_loai = QComboBox()
        self._phan_loai.addItem("Miễn phí (lỗi nhà sản xuất)", "mien_phi")
        self._phan_loai.addItem("Tính phí (lỗi khách hàng)", "tinh_phi")
        self._phan_loai.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                min-width: 250px;
            }
        """)
        phan_loai_layout.addWidget(self._phan_loai)
        phan_loai_layout.addStretch()
        layout.addLayout(phan_loai_layout)
        
        # Chi phi
        chi_phi_layout = QHBoxLayout()
        chi_phi_layout.addWidget(QLabel("Chi phí dự kiến (VNĐ):"))
        self._chi_phi = InlineNumericEdit(
            value=0,
            minimum=0,
            maximum=999999999,
            step=100000,
            suffix="VNĐ",
            is_float=False,
        )
        self._chi_phi_layout = chi_phi_layout
        chi_phi_layout.addWidget(self._chi_phi)
        chi_phi_layout.addStretch()
        layout.addLayout(chi_phi_layout)
        
        # Ky thuat vien
        kt_layout = QHBoxLayout()
        kt_layout.addWidget(QLabel("Kỹ thuật phụ trách:"))
        self._ky_thuat_vien = QComboBox()
        self._ky_thuat_vien.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                min-width: 200px;
            }
        """)
        kt_layout.addWidget(self._ky_thuat_vien)
        kt_layout.addStretch()
        layout.addLayout(kt_layout)
        
        # Ghi chu
        ghi_chu_label = QLabel("Ghi chú (tùy chọn):")
        ghi_chu_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(ghi_chu_label)
        
        self._ghi_chu = QTextEdit()
        self._ghi_chu.setPlaceholderText("Ghi chú thêm...")
        self._ghi_chu.setMaximumHeight(60)
        self._ghi_chu.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self._ghi_chu)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy bỏ")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self._submit_btn = QPushButton("Tạo yêu cầu")
        self._submit_btn.setStyleSheet("""
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
                background-color: #2db14e;
            }
        """)
        self._submit_btn.clicked.connect(self._on_submit)
        btn_layout.addWidget(self._submit_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_warranty_info(self):
        """Load warranty info for display and validation."""
        try:
            data = self._bh_service.get_by_id(self._bh_id)
            if not data:
                QMessageBox.critical(self, "Lỗi", "Không tìm thấy bảo hành!")
                self.reject()
                return
            
            bh = data
            kh = data.get("khach_hang", {})
            xe = data.get("xe", {})
            is_external = bh.get("is_external", 0) == 1

            # Display warranty info
            ngay_bat_dau = bh.get("ngay_bat_dau", "")[:10] if bh.get("ngay_bat_dau") else "N/A"
            ngay_ket_thuc = bh.get("ngay_ket_thuc", "")[:10] if bh.get("ngay_ket_thuc") else "N/A"

            if is_external:
                hang = bh.get("hang_xe", "") or ""
                dong = bh.get("dong_xe", "") or ""
                xe_text = f"{hang} {dong}".strip() if hang or dong else "Xe ngoài"
                self._bh_info_label.setText(
                    f"BH{bh.get('id', '')} — {xe_text} — "
                    f"KH: {kh.get('ho_ten', '')} — Hạn: {ngay_bat_dau} đến {ngay_ket_thuc}"
                )
            else:
                self._bh_info_label.setText(
                    f"BH{bh.get('id', '')} — {xe.get('hang', '')} {xe.get('dong_xe', '')} — "
                    f"KH: {kh.get('ho_ten', '')} — Hạn: {ngay_bat_dau} đến {ngay_ket_thuc}"
                )
            
            # Load technicians
            cursor = self._db_conn.execute(
                """SELECT id, ho_ten FROM nhan_vien WHERE trang_thai = 'active' ORDER BY ho_ten"""
            )
            for row in cursor.fetchall():
                self._ky_thuat_vien.addItem(row[1], row[0])
            
            # Set max date for ngay_yeu_cau
            self._max_date = QDate.fromString(ngay_ket_thuc, "yyyy-MM-dd")
            self._ngay_yeu_cau.setMaximumDate(self._max_date)
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải thông tin: {str(e)}")
            self.reject()

    def _on_submit(self):
        """Handle submit button."""
        ngay_yeu_cau = self._ngay_yeu_cau.date().toString("yyyy-MM-dd")
        
        # Check date is within warranty period
        if self._max_date and self._ngay_yeu_cau.date() > self._max_date:
            QMessageBox.warning(
                self, "Lỗi",
                f"Ngày yêu cầu không được sau ngày kết thúc BH ({self._max_date.toString('yyyy-MM-dd')})"
            )
            return
        
        loai_yeu_cau = self._loai_yeu_cau.currentData()
        phan_loai = self._phan_loai.currentData()
        chi_phi = self._chi_phi.value() if phan_loai == "tinh_phi" else 0
        nhan_vien_id = self._ky_thuat_vien.currentData()
        ghi_chu = self._ghi_chu.toPlainText().strip()
        
        data = BaoHanhYeuCauData(
            ngay_yeu_cau=ngay_yeu_cau,
            loai_yeu_cau=loai_yeu_cau,
            mo_ta_tinh_trang="",
            phan_loai=phan_loai,
            chi_phi=chi_phi,
            nhan_vien_id=nhan_vien_id,
            ghi_chu=ghi_chu,
        )
        
        try:
            self._bh_service.create_request(
                bh_id=self._bh_id,
                data=data,
                nhan_vien_id=self._session.nhan_vien_id if self._session else None,
            )
            
            QMessageBox.information(self, "Thành công", "Đã tạo yêu cầu bảo hành thành công!")
            self.request_created.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo yêu cầu: {str(e)}")
