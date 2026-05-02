"""Warranty request form dialog - S-BH-03 - Create warranty request.

Features:
- Form fields:
  - ngay_yeu_cau: date picker
  - loai_yeu_cau: dropdown (bao_duong, sua_chua, thay_the)
  - mo_ta_tinh_trang: text area for description
  - phan_loai: auto-suggested based on mo_ta keywords (mien_phi/tinh_phi)
  - chi_phi_du_kien: number input (0 for mien_phi)
  - nhan_vien_id: dropdown of technicians
- Validation: ngay_yeu_cau <= ngay_ket_thuc BH
- Auto-suggest classification based on keywords (BR-BH-04)

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


# Keywords that indicate customer fault (tinh_phi)
CUSTOMER_FAULT_KEYWORDS = [
    "va đập", "va dap", "đập", "dap",
    "ngập nước", "ngap nuoc", "ngập", "ngap",
    "tai nan", "tai nạn",
    "sử dụng sai", "su dung sai",
    "không bảo dưỡng", "khong bao duong",
    "tự sửa", "tu sua",
    "rơi", "roi",
]


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
        self._loai_yeu_cau.addItems([
            ("sua_chua", "Sửa chữa"),
            ("bao_duong", "Bảo dưỡng"),
            ("thay_the", "Thay thế"),
        ])
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
        
        # Mo ta tinh trang
        mo_ta_label = QLabel("Mô tả tình trạng:")
        mo_ta_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(mo_ta_label)
        
        self._mo_ta = QTextEdit()
        self._mo_ta.setPlaceholderText("Mô tả chi tiết vấn đề của xe...")
        self._mo_ta.setMinimumHeight(100)
        self._mo_ta.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 13px;
            }
            QTextEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        self._mo_ta.textChanged.connect(self._on_mo_ta_changed)
        layout.addWidget(self._mo_ta)
        
        # Phan loai (auto-suggest)
        phan_loai_layout = QHBoxLayout()
        phan_loai_layout.addWidget(QLabel("Phân loại (đề xuất):"))
        self._phan_loai_label = QLabel("—")
        self._phan_loai_label.setStyleSheet("font-weight: 600; color: #34c759;")
        phan_loai_layout.addWidget(self._phan_loai_label)
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
            
            # Display warranty info
            ngay_bat_dau = bh.get("ngay_bat_dau", "")[:10] if bh.get("ngay_bat_dau") else "N/A"
            ngay_ket_thuc = bh.get("ngay_ket_thuc", "")[:10] if bh.get("ngay_ket_thuc") else "N/A"
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
    
    def _on_mo_ta_changed(self):
        """Handle description change - auto-suggest classification."""
        mo_ta = self._mo_ta.toPlainText().lower()
        
        is_customer_fault = False
        for keyword in CUSTOMER_FAULT_KEYWORDS:
            if keyword in mo_ta:
                is_customer_fault = True
                break
        
        if is_customer_fault:
            self._phan_loai_label.setText("Tính phí (lỗi khách hàng)")
            self._phan_loai_label.setStyleSheet("font-weight: 600; color: #ff3b30;")
            self._chi_phi.setEnabled(True)
        else:
            self._phan_loai_label.setText("Miễn phí (lỗi nhà sản xuất)")
            self._phan_loai_label.setStyleSheet("font-weight: 600; color: #34c759;")
            self._chi_phi.setEnabled(False)
            self._chi_phi.setValue(0)
    
    def _on_submit(self):
        """Handle submit button."""
        # Validate
        mo_ta = self._mo_ta.toPlainText().strip()
        if not mo_ta:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mô tả tình trạng!")
            return
        
        ngay_yeu_cau = self._ngay_yeu_cau.date().toString("yyyy-MM-dd")
        
        # Check date is within warranty period
        if self._ngay_yeu_cau.date() > self._max_date:
            QMessageBox.warning(
                self, "Lỗi",
                f"Ngày yêu cầu không được sau ngày kết thúc BH ({self._max_date.toString('yyyy-MM-dd')})"
            )
            return
        
        loai_yeu_cau = self._loai_yeu_cau.currentData()
        phan_loai = "tinh_phi" if "Tính phí" in self._phan_loai_label.text() else "mien_phi"
        chi_phi = self._chi_phi.value() if phan_loai == "tinh_phi" else 0
        nhan_vien_id = self._ky_thuat_vien.currentData()
        ghi_chu = self._ghi_chu.toPlainText().strip()
        
        data = BaoHanhYeuCauData(
            ngay_yeu_cau=ngay_yeu_cau,
            loai_yeu_cau=loai_yeu_cau,
            mo_ta_tinh_trang=mo_ta,
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
