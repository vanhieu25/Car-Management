"""Contract detail screen - S-HD-03 - Full contract display with actions.

Features:
- Header: Mã HĐ, Ngày tạo, NV phụ trách
- Customer section (link to S-KH-03)
- Vehicle section (link to S-XE-03)
- Accessories table with snapshot prices
- Promotion section
- Total breakdown (BR-CALC-01)
- Action buttons based on state machine (BR-FLOW):
  - moi_tao: "Thanh toán" (primary), "Hủy" (danger)
  - da_thanh_toan: "Giao xe" (primary), "Hủy" (danger) — only A-01
  - da_giao_xe: No actions (final state)
- Notes/tracking section

References:
- BR-HD-01..12: Contract lifecycle
- BR-FLOW: State machine transitions
- BR-CALC-01: Total calculation
"""

from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QGroupBox,
    QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.application.services.hop_dong_service import (
    HopDongService, HopDongServiceError,
    InvalidStateTransitionError, InsufficientStockError, NotAuthorizedError
)
from app.application.services.session import CurrentSession


class ContractDetailScreen(QWidget):
    """Contract detail screen - S-HD-03.
    
    Signals:
        view_customer_clicked(khach_hang_id: int): User wants to view customer details.
        view_vehicle_clicked(xe_id: int): User wants to view vehicle details.
        closed: Screen was closed.
        action_completed: An action was performed (payment, delivery, etc.)
    """
    
    view_customer_clicked = pyqtSignal(int)
    view_vehicle_clicked = pyqtSignal(int)
    closed = pyqtSignal()
    action_completed = pyqtSignal()
    
    def __init__(self, db_conn, session: CurrentSession, hop_dong_id: int, parent=None):
        """Initialize contract detail screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            hop_dong_id: Contract ID to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._hd_service = HopDongService(db_conn)
        self._hop_dong_id = hop_dong_id
        self._contract_data: Optional[Dict] = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        self._title_label = QLabel("Chi tiết hợp đồng")
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
        
        # Status badge and contract code
        self._status_card = QGroupBox()
        self._status_card.setStyleSheet("""
            QGroupBox {
                border: none;
                padding: 0;
                margin: 0;
            }
        """)
        status_layout = QHBoxLayout(self._status_card)
        
        self._ma_hd_label = QLabel()
        self._ma_hd_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #1d1d1f;")
        status_layout.addWidget(self._ma_hd_label)
        
        self._status_badge = QLabel()
        status_layout.addWidget(self._status_badge)
        
        status_layout.addStretch()
        
        self._ngay_tao_label = QLabel()
        self._ngay_tao_label.setStyleSheet("font-size: 13px; color: #86868b;")
        status_layout.addWidget(self._ngay_tao_label)
        
        scroll_layout.addWidget(self._status_card)
        
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
        
        # Accessories section
        self._pk_section = self._create_section_group("Phụ kiện đi kèm", "pk_section")
        self._pk_table = QTableWidget()
        self._pk_table.setColumnCount(4)
        self._pk_table.setHorizontalHeaderLabels(["Tên phụ kiện", "Phân loại", "Số lượng", "Giá snapshot"])
        self._pk_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._pk_table.setStyleSheet("""
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
        self._xe_section_layout = QVBoxLayout(self._pk_section)
        self._xe_section_layout.addWidget(self._pk_table)
        scroll_layout.addWidget(self._pk_section)
        
        # Promotion section
        self._km_section = self._create_section_group("Khuyến mãi", "km_section")
        self._km_content = QLabel("Không có")
        self._km_content.setStyleSheet("font-size: 14px; color: #86868b;")
        self._km_section_layout = QVBoxLayout(self._km_section)
        self._km_section_layout.addWidget(self._km_content)
        scroll_layout.addWidget(self._km_section)
        
        # Total breakdown
        self._total_section = QGroupBox("Tổng hợp thanh toán")
        self._total_section.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: 600;
                color: #1d1d1f;
                border: 2px solid #0066cc;
                border-radius: 8px;
                padding: 16px;
                background-color: #f0f7ff;
            }
        """)
        total_layout = QVBoxLayout(self._total_section)
        total_layout.setSpacing(10)
        
        self._gia_xe_label = QLabel("Giá xe: 0 đ")
        total_layout.addWidget(self._gia_xe_label)
        
        self._pk_total_label = QLabel("Phụ kiện: 0 đ")
        total_layout.addWidget(self._pk_total_label)
        
        self._km_discount_label = QLabel("Giảm giá KM: 0 đ")
        self._km_discount_label.setStyleSheet("color: #34c759;")
        total_layout.addWidget(self._km_discount_label)
        
        self._tong_label = QLabel("TỔNG CỘNG: 0 đ")
        tong_font = QFont()
        tong_font.setPointSize(16)
        tong_font.setBold(True)
        self._tong_label.setFont(tong_font)
        self._tong_label.setStyleSheet("color: #0066cc;")
        total_layout.addWidget(self._tong_label)
        
        scroll_layout.addWidget(self._total_section)
        
        # Status timeline
        self._timeline_section = self._create_section_group("Timeline trạng thái", "timeline_section")
        self._timeline_content = QLabel()
        self._timeline_content.setStyleSheet("font-size: 13px; color: #3c3c43;")
        self._timeline_section_layout = QVBoxLayout(self._timeline_section)
        self._timeline_section_layout.addWidget(self._timeline_content)
        scroll_layout.addWidget(self._timeline_section)
        
        # Notes section
        self._notes_section = self._create_section_group("Ghi chú", "notes_section")
        self._notes_content = QLabel("Không có ghi chú")
        self._notes_content.setStyleSheet("font-size: 14px; color: #86868b; font-style: italic;")
        self._notes_content.setWordWrap(True)
        self._notes_section_layout = QVBoxLayout(self._notes_section)
        self._notes_section_layout.addWidget(self._notes_content)
        scroll_layout.addWidget(self._notes_section)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        
        # Action buttons
        self._action_layout = QHBoxLayout()
        self._action_layout.addStretch()
        
        self._cancel_btn = QPushButton("🗑️ Hủy hợp đồng")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._action_layout.addWidget(self._cancel_btn)
        
        self._payment_btn = QPushButton("💳 Thanh toán")
        self._payment_btn.setStyleSheet("""
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
        self._payment_btn.clicked.connect(self._on_payment)
        self._action_layout.addWidget(self._payment_btn)
        
        self._delivery_btn = QPushButton("🚗 Giao xe")
        self._delivery_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
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
        self._delivery_btn.clicked.connect(self._on_delivery)
        self._action_layout.addWidget(self._delivery_btn)
        
        self._print_btn = QPushButton("📄 In / Xuất PDF")
        self._print_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._print_btn.clicked.connect(self._on_print_pdf)
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
        """Load contract data."""
        try:
            data = self._hd_service.get_full_contract(self._hop_dong_id)
            if not data:
                QMessageBox.critical(self, "Lỗi", "Không tìm thấy hợp đồng!")
                self._on_back()
                return
            
            self._contract_data = data
            self._populate_ui(data)
            self._update_action_buttons(data.get('hop_dong', {}).get('trang_thai', 'moi_tao'))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
            self._on_back()
    
    def _populate_ui(self, data: Dict):
        """Populate UI with contract data."""
        hd = data.get('hop_dong', {})
        kh = data.get('khach_hang', {})
        xe = data.get('xe', {})
        nv = data.get('nhan_vien', {})
        pk_list = data.get('phu_kien_list', [])
        km = data.get('khuyen_mai', {})
        
        # Header
        self._title_label.setText(f"Chi tiết hợp đồng - {hd.get('ma_hop_dong', 'N/A')}")
        self._ma_hd_label.setText(hd.get('ma_hop_dong', 'N/A'))
        
        # Status badge
        status = hd.get('trang_thai', 'moi_tao')
        status_labels = {
            'moi_tao': ('Mới tạo', '#8e8e93'),
            'da_thanh_toan': ('Đã thanh toán', '#007aff'),
            'da_giao_xe': ('Đã giao xe', '#34c759'),
            'huy': ('Đã hủy', '#ff3b30'),
        }
        label, color = status_labels.get(status, ('N/A', '#8e8e93'))
        self._status_badge.setText(f"<span style='background:{color}; color:white; padding:4px 12px; border-radius:12px; font-size:13px; font-weight:600;'>{label}</span>")
        
        # Dates
        ngay_tao = hd.get('ngay_tao', '')[:19] if hd.get('ngay_tao') else 'N/A'
        self._ngay_tao_label.setText(f"Tạo lúc: {ngay_tao} | NV: {nv.get('ho_ten', 'N/A')}")
        
        # Customer
        kh_id = kh.get('id')
        if kh_id:
            kh_link = f"""<a href='#khach_hang' style='color: #0066cc; text-decoration: none;'>{kh.get('ho_ten', 'N/A')}</a>"""
            self._kh_content.setText(
                f"<b>{kh.get('ho_ten', 'N/A')}</b><br>"
                f"SĐT: {kh.get('so_dien_thoai', 'N/A')} | Email: {kh.get('email', 'N/A')}<br>"
                f"Địa chỉ: {kh.get('dia_chi', 'N/A')}<br>"
                f"Phân loại: {kh.get('phan_loai', 'N/A')} | "
                f"Đã mua: {kh.get('so_xe_da_mua', 0)} xe | "
                f"Tổng giá trị: {kh.get('tong_gia_tri_mua', 0):,.0f} đ".replace(",", ".").replace(" ", "&nbsp;")
            )
            # Make the name clickable
            self._kh_content.setTextFormat(Qt.TextFormat.RichText)
        
        # Vehicle
        if xe:
            self._xe_content.setText(
                f"<b>{xe.get('hang', 'N/A')} {xe.get('dong_xe', 'N/A')}</b><br>"
                f"Mã xe: {xe.get('ma_xe', 'N/A')} | Màu: {xe.get('mau_sac', 'N/A')}<br>"
                f"Năm SX: {xe.get('nam_san_xuat', 'N/A')} | "
                f"Giá bán: {xe.get('gia_ban', 0):,.0f} đ".replace(",", ".")
            )
        
        # Accessories table
        self._pk_table.setRowCount(len(pk_list))
        if not pk_list:
            self._pk_table.setRowCount(1)
            self._pk_table.setItem(0, 0, QTableWidgetItem("Không có phụ kiện"))
            for col in range(1, 4):
                self._pk_table.setItem(0, col, QTableWidgetItem("-"))
        else:
            for i, pk in enumerate(pk_list):
                self._pk_table.setItem(i, 0, QTableWidgetItem(pk.get('ten_pk', 'N/A')))
                self._pk_table.setItem(i, 1, QTableWidgetItem(pk.get('phan_loai', 'N/A')))
                
                so_luong_item = QTableWidgetItem(str(pk.get('so_luong_mua', 1)))
                so_luong_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._pk_table.setItem(i, 2, so_luong_item)
                
                gia_snapshot = pk.get('gia_ban_snapshot', 0)
                gia_item = QTableWidgetItem(f"{gia_snapshot:,} đ".replace(",", "."))
                gia_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self._pk_table.setItem(i, 3, gia_item)
        
        self._pk_table.setColumnWidth(0, 200)
        self._pk_table.setColumnWidth(1, 120)
        self._pk_table.setColumnWidth(2, 80)
        self._pk_table.setColumnWidth(3, 120)
        
        # Promotion
        if km:
            self._km_content.setText(
                f"<b>{km.get('ten_km', 'N/A')}</b><br>"
                f"Loại: {km.get('loai_km', 'N/A')} | "
                f"Giá trị: {km.get('gia_tri', 0):,} đ ({km.get('kieu_gia_tri', 'tien')})".replace(",", ".")
            )
            self._km_content.setStyleSheet("font-size: 14px; color: #34c759;")
        else:
            self._km_content.setText("Không có khuyến mãi áp dụng")
            self._km_content.setStyleSheet("font-size: 14px; color: #86868b;")
        
        # Total breakdown
        gia_xe = hd.get('gia_xe', 0)
        tong_pk = hd.get('tong_gia_phu_kien', 0)
        tien_km = hd.get('tien_giam_km', 0)
        tong_tien = hd.get('tong_tien', 0)
        
        self._gia_xe_label.setText(f"Giá xe: {gia_xe:,} đ".replace(",", "."))
        self._pk_total_label.setText(f"Phụ kiện: {tong_pk:,} đ".replace(",", "."))
        self._km_discount_label.setText(f"Giảm giá KM: -{tien_km:,} đ".replace(",", "."))
        self._tong_label.setText(f"TỔNG CỘNG: {tong_tien:,} đ".replace(",", "."))
        
        # Timeline
        timeline_parts = []
        
        # Created
        ngay_tao_disp = hd.get('ngay_tao', '')[:19] if hd.get('ngay_tao') else 'N/A'
        timeline_parts.append(f"✅ <b>Tạo</b> — {ngay_tao_disp} bởi {nv.get('ho_ten', 'N/A')}")
        
        # Paid
        if hd.get('ngay_thanh_toan'):
            timeline_parts.append(f"✅ <b>Thanh toán</b> — {hd.get('ngay_thanh_toan', '')[:19]}")
        
        # Delivered
        if hd.get('ngay_giao_xe'):
            timeline_parts.append(f"✅ <b>Giao xe</b> — {hd.get('ngay_giao_xe', '')[:19]}")
        
        # Cancelled
        if status == 'huy':
            timeline_parts.append(f"❌ <b>Hủy</b> — Lý do: {hd.get('ly_do_huy', 'N/A')}")
        
        self._timeline_content.setText("<br>".join(timeline_parts) if timeline_parts else "Không có thông tin timeline")
        
        # Notes
        ghi_chu = hd.get('ghi_chu', '')
        if ghi_chu:
            self._notes_content.setText(ghi_chu)
            self._notes_content.setStyleSheet("font-size: 14px; color: #3c3c43;")
        else:
            self._notes_content.setText("Không có ghi chú")
            self._notes_content.setStyleSheet("font-size: 14px; color: #86868b; font-style: italic;")
    
    def _update_action_buttons(self, status: str):
        """Update action buttons based on contract status and user role.
        
        BR-FLOW state machine:
        - moi_tao: "Thanh toán" (primary), "Hủy" (danger)
        - da_thanh_toan: "Giao xe" (primary), "Hủy" (danger) — only A-01
        - da_giao_xe: No actions (final state)
        """
        is_admin = self._session and self._session.vai_tro_ma == "A-01"
        
        # Hide all by default
        self._payment_btn.setVisible(False)
        self._delivery_btn.setVisible(False)
        self._cancel_btn.setVisible(False)
        
        if status == 'moi_tao':
            # Show payment and cancel for admin/sales
            if self._session and self._session.vai_tro_ma in ("A-01", "A-02"):
                self._payment_btn.setVisible(True)
                self._cancel_btn.setVisible(True)
        
        elif status == 'da_thanh_toan':
            # Only admin can cancel or deliver
            if is_admin:
                self._delivery_btn.setVisible(True)
                self._cancel_btn.setVisible(True)
        
        elif status == 'da_giao_xe':
            # Final state - no actions
            pass
        
        elif status == 'huy':
            # Cancelled - no actions
            pass
    
    def _on_back(self):
        """Handle back button."""
        self.closed.emit()
    
    def _on_payment(self):
        """Handle payment button - mark contract as paid."""
        reply = QMessageBox.question(
            self,
            "Xác nhận thanh toán",
            "Bạn có chắc chắn muốn xác nhận thanh toán cho hợp đồng này?\n"
            "Hệ thống sẽ:\n"
            "• Trừ 1 xe từ kho\n"
            "• Trừ số lượng phụ kiện đã mua\n"
            "• Cập nhật trạng thái hợp đồng sang 'Đã thanh toán'",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self._hd_service.set_paid(
                self._hop_dong_id,
                nhan_vien_id=self._session.nhan_vien_id if self._session else None,
            )
            QMessageBox.information(self, "Thành công", "Đã xác nhận thanh toán thành công!")
            self.action_completed.emit()
            self._load_data()
        except InsufficientStockError as e:
            QMessageBox.critical(self, "Lỗi kho", str(e))
        except HopDongServiceError as e:
            QMessageBox.critical(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xử lý: {str(e)}")
    
    def _on_delivery(self):
        """Handle delivery button - mark contract as delivered."""
        reply = QMessageBox.question(
            self,
            "Xác nhận giao xe",
            "Bạn có chắc chắn muốn xác nhận giao xe?\n"
            "Hệ thống sẽ:\n"
            "• Tạo bảo hành tự động\n"
            "• Cập nhật trạng thái KH (phân loại, tổng mua)\n"
            "• Cập nhật KPI nhân viên",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self._hd_service.set_delivered(
                self._hop_dong_id,
                nhan_vien_id=self._session.nhan_vien_id if self._session else None,
            )
            QMessageBox.information(self, "Thành công", "Đã xác nhận giao xe thành công!")
            self.action_completed.emit()
            self._load_data()
        except HopDongServiceError as e:
            QMessageBox.critical(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xử lý: {str(e)}")
    
    def _on_cancel(self):
        """Handle cancel button - show cancel confirmation dialog."""
        from app.presentation.widgets.dialogs import ConfirmDialog
        
        # Show cancel dialog with reason input
        dialog = CancelContractDialog(self._db_conn, self._session, self._hop_dong_id, parent=self)
        dialog.cancelled.connect(self._on_contract_cancelled)
        dialog.exec()
    
    def _on_contract_cancelled(self):
        """Handle contract cancelled event."""
        QMessageBox.information(self, "Thành công", "Đã hủy hợp đồng thành công!")
        self.action_completed.emit()
        self._load_data()
    
    def _on_print_pdf(self):
        """Handle print/PDF button."""
        from app.presentation.screens.pdf_preview_dialog import PdfPreviewDialog
        
        dialog = PdfPreviewDialog(self._db_conn, self._hop_dong_id, parent=self)
        dialog.exec()
    
    def refresh(self):
        """Refresh contract data."""
        self._load_data()


class CancelContractDialog(QDialog):
    """Cancel contract confirmation dialog.
    
    Dialog title: "Xác nhận hủy hợp đồng"
    Warning text explaining consequences (stock returned, BH deleted)
    Text field for reason (required, ≥ 10 characters per BR-UI-04)
    Confirm button (disabled until reason meets requirement)
    Cancel button
    On confirm → calls HopDongService.cancel()
    
    Signals:
        cancelled: Emitted when contract was cancelled successfully.
    """
    
    cancelled = pyqtSignal()
    
    def __init__(self, db_conn, session, hop_dong_id: int, parent=None):
        """Initialize cancel dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            hop_dong_id: Contract ID to cancel.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._hop_dong_id = hop_dong_id
        self._hd_service = HopDongService(db_conn)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Xác nhận hủy hợp đồng")
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Warning icon and title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("Xác nhận hủy hợp đồng")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #ff3b30;")
        header_layout.addWidget(title_label, 1)
        
        layout.addLayout(header_layout)
        
        # Warning message
        warning_label = QLabel(
            "Hủy hợp đồng sẽ gây ra các thay đổi sau:\n"
            "• Xe sẽ được hoàn trả vào kho\n"
            "• Phụ kiện đã mua sẽ được hoàn trả\n"
            "• Bảo hành liên quan sẽ bị xóa\n"
            "• Hợp đồng sẽ chuyển sang trạng thái 'Đã hủy'"
        )
        warning_label.setStyleSheet("""
            font-size: 13px;
            color: #3c3c43;
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 6px;
            padding: 12px;
        """)
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # Reason input
        reason_label = QLabel("Lý do hủy * (tối thiểu 10 ký tự):")
        reason_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(reason_label)
        
        self._reason_input = QTextEdit()
        self._reason_input.setPlaceholderText("Nhập lý do hủy hợp đồng...")
        self._reason_input.setMinimumHeight(100)
        self._reason_input.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 13px;
                background: white;
            }
            QTextEdit:focus {
                border: 2px solid #ff3b30;
            }
        """)
        self._reason_input.textChanged.connect(self._on_reason_changed)
        layout.addWidget(self._reason_input)
        
        self._char_count = QLabel("0/10 ký tự")
        self._char_count.setStyleSheet("font-size: 12px; color: #86868b;")
        self._char_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._char_count)
        
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
        
        self._confirm_btn = QPushButton("Xác nhận hủy")
        self._confirm_btn.setStyleSheet("""
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
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self._confirm_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_reason_changed(self):
        """Handle reason text change."""
        text = self._reason_input.toPlainText().strip()
        length = len(text)
        
        self._char_count.setText(f"{length}/10 ký tự")
        
        if length >= 10:
            self._char_count.setStyleSheet("font-size: 12px; color: #34c759;")
            self._confirm_btn.setEnabled(True)
        else:
            self._char_count.setStyleSheet("font-size: 12px; color: #ff3b30;")
            self._confirm_btn.setEnabled(False)
    
    def _on_confirm(self):
        """Handle confirm button."""
        reason = self._reason_input.toPlainText().strip()
        
        if len(reason) < 10:
            QMessageBox.warning(self, "Lỗi", "Lý do hủy phải có ít nhất 10 ký tự.")
            return
        
        try:
            self._hd_service.cancel(
                self._hop_dong_id,
                ly_do=reason,
                nhan_vien_id=self._session.nhan_vien_id if self._session else None,
                nhan_vien_vai_tro=self._session.vai_tro_ma if self._session else None,
            )
            self.cancelled.emit()
            self.accept()
        except NotAuthorizedError:
            QMessageBox.critical(self, "Không có quyền", "Chỉ admin (A-01) mới được hủy hợp đồng.")
        except InvalidStateTransitionError as e:
            QMessageBox.critical(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể hủy hợp đồng: {str(e)}")


# Need to import QDialog for CancelContractDialog
from PyQt6.QtWidgets import QDialog
