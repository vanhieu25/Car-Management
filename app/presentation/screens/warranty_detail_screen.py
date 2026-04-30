"""Warranty detail screen - S-BH-02 - Full warranty display with request list.

Features:
- Header: Warranty ID, contract link, status
- Warranty info section: period, scope
- Vehicle section (link to S-XE-03)
- Customer section (link to S-KH-03)
- Warranty requests table with status badges
- Action buttons:
  - "Tạo yêu cầu BH" → opens request form
  - "In phiếu BH" → opens print dialog

References:
- BR-BH-01..10: Warranty management
- BR-BH-05: Request status transitions
- BR-BH-07: Warranty slip content
"""

from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QGroupBox,
    QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.application.services.bao_hanh_service import BaoHanhService
from app.application.services.session import CurrentSession


class WarrantyDetailScreen(QWidget):
    """Warranty detail screen - S-BH-02.
    
    Signals:
        view_customer_clicked(khach_hang_id: int): User wants to view customer details.
        view_vehicle_clicked(xe_id: int): User wants to view vehicle details.
        create_request_clicked(bh_id: int): User wants to create a warranty request.
        print_warranty_clicked(bh_id: int): User wants to print warranty.
        closed: Screen was closed.
        action_completed: An action was performed.
    """
    
    view_customer_clicked = pyqtSignal(int)
    view_vehicle_clicked = pyqtSignal(int)
    create_request_clicked = pyqtSignal(int)
    print_warranty_clicked = pyqtSignal(int)
    closed = pyqtSignal()
    action_completed = pyqtSignal()
    
    def __init__(self, db_conn, session: CurrentSession, bh_id: int, parent=None):
        """Initialize warranty detail screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            bh_id: Warranty ID to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bh_service = BaoHanhService(db_conn)
        self._bh_id = bh_id
        self._warranty_data: Optional[Dict] = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        self._title_label = QLabel("Chi tiết bảo hành")
        self._title_label.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(self._title_label)
        
        header_layout.addStretch()
        
        # Back button
        self._back_btn = QPushButton("← Quay lại")
        self._back_btn.setStyleSheet("""
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
        self._back_btn.clicked.connect(self._on_back)
        header_layout.addWidget(self._back_btn)
        
        layout.addLayout(header_layout)
        
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        
        # Status badge and warranty ID
        self._status_card = QGroupBox()
        self._status_card.setStyleSheet("""
            QGroupBox {
                border: none;
                padding: 0;
                margin: 0;
            }
        """)
        status_layout = QHBoxLayout(self._status_card)
        
        self._bh_id_label = QLabel()
        self._bh_id_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #1d1d1f;")
        status_layout.addWidget(self._bh_id_label)
        
        self._status_badge = QLabel()
        status_layout.addWidget(self._status_badge)
        
        status_layout.addStretch()
        
        self._contract_label = QLabel()
        self._contract_label.setStyleSheet("font-size: 13px; color: #86868b;")
        status_layout.addWidget(self._contract_label)
        
        scroll_layout.addWidget(self._status_card)
        
        # Warranty period highlight
        self._period_group = self._create_section_group("Thời hạn bảo hành", "period_group")
        period_layout = QVBoxLayout(self._period_group)
        
        self._period_dates_label = QLabel()
        self._period_dates_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #0066cc;")
        period_layout.addWidget(self._period_dates_label)
        
        self._period_duration_label = QLabel()
        self._period_duration_label.setStyleSheet("font-size: 13px; color: #86868b;")
        period_layout.addWidget(self._period_duration_label)
        
        scroll_layout.addWidget(self._period_group)
        
        # Customer section
        self._kh_section = self._create_section_group("Khách hàng", "kh_section")
        self._kh_content = QLabel()
        self._kh_content.setStyleSheet("font-size: 14px; color: #3c3c43;")
        self._kh_section_layout = QVBoxLayout(self._kh_section)
        self._kh_section_layout.addWidget(self._kh_content)
        scroll_layout.addWidget(self._kh_section)
        
        # Vehicle section
        self._xe_section = self._create_section_group("Xe", "xe_section")
        self._xe_content = QLabel()
        self._xe_content.setStyleSheet("font-size: 14px; color: #3c3c43;")
        self._xe_section_layout = QVBoxLayout(self._xe_section)
        self._xe_section_layout.addWidget(self._xe_content)
        scroll_layout.addWidget(self._xe_section)
        
        # Warranty scope
        self._scope_section = self._create_section_group("Phạm vi bảo hành", "scope_section")
        self._scope_content = QLabel()
        self._scope_content.setStyleSheet("font-size: 14px; color: #3c3c43;")
        self._scope_section_layout = QVBoxLayout(self._scope_section)
        self._scope_section_layout.addWidget(self._scope_content)
        scroll_layout.addWidget(self._scope_section)
        
        # Warranty requests section
        self._requests_section = self._create_section_group("Yêu cầu bảo hành", "requests_section")
        self._requests_layout = QVBoxLayout(self._requests_section)
        
        self._requests_table = QTableWidget()
        self._requests_table.setColumnCount(6)
        self._requests_table.setHorizontalHeaderLabels([
            "ID", "Ngày yêu cầu", "Loại", "Mô tả", "Kỹ thuật phụ trách", "Trạng thái"
        ])
        self._requests_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._requests_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 8px;
                font-weight: 600;
                font-size: 13px;
            }
        """)
        self._requests_layout.addWidget(self._requests_table)
        scroll_layout.addWidget(self._requests_section)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        
        # Action buttons
        self._action_layout = QHBoxLayout()
        self._action_layout.addStretch()
        
        self._request_btn = QPushButton("📝 Tạo yêu cầu BH")
        self._request_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._request_btn.clicked.connect(self._on_create_request)
        self._action_layout.addWidget(self._request_btn)
        
        self._print_btn = QPushButton("🖨️ In phiếu BH")
        self._print_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._print_btn.clicked.connect(self._on_print)
        self._action_layout.addWidget(self._print_btn)
        
        layout.addLayout(self._action_layout)
    
    def _create_section_group(self, title: str, obj_name: str) -> QGroupBox:
        """Create a styled section group box."""
        group = QGroupBox(title)
        group.setObjectName(obj_name)
        group.setStyleSheet(f"""
            QGroupBox#{obj_name} {{
                font-size: 15px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 16px;
                background-color: white;
            }}
            QGroupBox#{obj_name}::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }}
        """)
        return group
    
    def _load_data(self):
        """Load warranty data."""
        try:
            data = self._bh_service.get_by_id(self._bh_id)
            if not data:
                QMessageBox.critical(self, "Lỗi", "Không tìm thấy bảo hành!")
                self._on_back()
                return
            
            self._warranty_data = data
            self._populate_ui(data)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
            self._on_back()
    
    def _populate_ui(self, data: Dict):
        """Populate UI with warranty data."""
        bh = data
        kh = data.get("khach_hang", {})
        xe = data.get("xe", {})
        hd = data.get("hop_dong", {})
        yeu_cau_list = data.get("yeu_cau_list", [])
        
        # Header
        self._title_label.setText(f"Chi tiết bảo hành - BH{bh.get('id', '')}")
        self._bh_id_label.setText(f"BH{bh.get('id', '')}")
        
        # Status badge
        trang_thai = bh.get("trang_thai", "con_hieu_luc")
        status_labels = {
            "con_hieu_luc": ("Còn hiệu lực", "#34c759"),
            "het_han": ("Hết hạn", "#ff3b30"),
        }
        label, color = status_labels.get(trang_thai, ("N/A", "#8e8e93"))
        self._status_badge.setText(
            f"<span style='background:{color}; color:white; padding:4px 12px; border-radius:12px; font-size:13px; font-weight:600;'>{label}</span>"
        )
        
        # Contract
        self._contract_label.setText(f"Hợp đồng: {hd.get('ma_hop_dong', 'N/A')}")
        
        # Period
        ngay_bat_dau = bh.get("ngay_bat_dau", "")[:10] if bh.get("ngay_bat_dau") else "N/A"
        ngay_ket_thuc = bh.get("ngay_ket_thuc", "")[:10] if bh.get("ngay_ket_thuc") else "N/A"
        thoi_han = bh.get("thoi_han_bh", 24)
        self._period_dates_label.setText(f"{ngay_bat_dau} — {ngay_ket_thuc}")
        self._period_duration_label.setText(f"Thời hạn: {thoi_han} tháng")
        
        # Customer
        if kh:
            self._kh_content.setText(
                f"<b>{kh.get('ho_ten', 'N/A')}</b><br>"
                f"SĐT: {kh.get('so_dien_thoai', 'N/A')} | Email: {kh.get('email', 'N/A')}<br>"
                f"Địa chỉ: {kh.get('dia_chi', 'N/A')}"
            )
        
        # Vehicle
        if xe:
            self._xe_content.setText(
                f"<b>{xe.get('hang', 'N/A')} {xe.get('dong_xe', 'N/A')}</b><br>"
                f"Mã xe: {xe.get('ma_xe', 'N/A')} | Màu: {xe.get('mau_sac', 'N/A')}<br>"
                f"Năm SX: {xe.get('nam_san_xuat', 'N/A')}"
            )
        
        # Scope
        pham_vi = bh.get("pham_vi", "Bảo hành toàn diện theo điều khoản chuẩn của nhà sản xuất")
        self._scope_content.setText(pham_vi)
        
        # Requests table
        self._requests_table.setRowCount(len(yeu_cau_list))
        if not yeu_cau_list:
            self._requests_table.setRowCount(1)
            self._requests_table.setItem(0, 0, QTableWidgetItem("Chưa có yêu cầu bảo hành nào"))
            for col in range(1, 6):
                self._requests_table.setItem(0, col, QTableWidgetItem("-"))
        else:
            for i, yc in enumerate(yeu_cau_list):
                self._requests_table.setItem(i, 0, QTableWidgetItem(str(yc.get("id", ""))))
                self._requests_table.setItem(i, 1, QTableWidgetItem(yc.get("ngay_yeu_cau", "")[:10] if yc.get("ngay_yeu_cau") else ""))
                
                loai_map = {"bao_duong": "Bảo dưỡng", "sua_chua": "Sửa chữa", "thay_the": "Thay thế"}
                self._requests_table.setItem(i, 2, QTableWidgetItem(loai_map.get(yc.get("loai_yeu_cau", ""), yc.get("loai_yeu_cau", ""))))
                
                self._requests_table.setItem(i, 3, QTableWidgetItem(yc.get("mo_ta_tinh_trang", "")))
                self._requests_table.setItem(i, 4, QTableWidgetItem(yc.get("nv_ho_ten", "N/A")))
                
                # Status badge
                trang_thai_yc = yc.get("trang_thai", "")
                status_map = {
                    "moi": ("Mới", "#007aff"),
                    "dang_xu_ly": ("Đang xử lý", "#ff9500"),
                    "da_hoan_thanh": ("Hoàn thành", "#34c759"),
                    "da_dong": ("Đóng", "#8e8e93"),
                }
                st_label, st_color = status_map.get(trang_thai_yc, (trang_thai_yc, "#8e8e93"))
                st_item = QTableWidgetItem(st_label)
                st_item.setBackground(QColor(st_color))
                st_item.setForeground(QColor(255, 255, 255))
                self._requests_table.setItem(i, 5, st_item)
        
        self._requests_table.setColumnWidth(0, 50)
        self._requests_table.setColumnWidth(1, 100)
        self._requests_table.setColumnWidth(2, 100)
        self._requests_table.setColumnWidth(3, 200)
        self._requests_table.setColumnWidth(4, 140)
        self._requests_table.setColumnWidth(5, 100)
    
    def _on_back(self):
        """Handle back button."""
        self.closed.emit()
    
    def _on_create_request(self):
        """Handle create request button."""
        self.create_request_clicked.emit(self._bh_id)
    
    def _on_print(self):
        """Handle print button."""
        self.print_warranty_clicked.emit(self._bh_id)
    
    def refresh(self):
        """Refresh warranty data."""
        self._load_data()
