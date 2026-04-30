"""Customer detail screen - S-KH-03 - Customer details with tabs.

Features:
- KpiCard with tong_gia_tri_mua, so_xe_da_mua, phan_loai
- Tab 1: Thông tin (Customer info)
- Tab 2: Lịch sử giao dịch (Purchase history - BR-KH-04)
- Tab 3: Bảo hành (Warranties)
- Tab 4: Khiếu nại (Complaints)
- Tooltip explaining classification calculation (BR-CALC-03)

References:
- UC-KH-03: Xem chi tiết khách hàng
- BR-KH-04: Purchase history includes all contracts including cancelled
- BR-CALC-03: Customer classification thresholds
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QGroupBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.application.services.khach_hang_service import KhachHangService
from app.application.services.session import CurrentSession
from app.domain.entities import KhachHang


class CustomerDetailScreen(QWidget):
    """Customer detail screen with tabs - S-KH-03.
    
    Signals:
        edit_clicked: User wants to edit this customer.
        close_clicked: User wants to close this detail view.
    """
    
    edit_clicked = pyqtSignal(int)  # khach_hang_id
    close_clicked = pyqtSignal()
    
    def __init__(self, db_conn, session: CurrentSession, khach_hang_id: int, parent=None):
        """Initialize customer detail screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            khach_hang_id: Customer ID to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._kh_service = KhachHangService(db_conn)
        self._khach_hang_id = khach_hang_id
        self._khach_hang: Optional[KhachHang] = None
        
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
        self._back_btn.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(self._back_btn)
        
        header_layout.addStretch()
        
        self._title_label = QLabel("Chi tiết khách hàng")
        self._title_label.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(self._title_label)
        
        header_layout.addStretch()
        
        # Edit button (only for A-01, A-02)
        if self._session and self._session.vai_tro_ma in ("A-01", "A-02"):
            self._edit_btn = QPushButton("✏️ Sửa")
            self._edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007aff;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #0055b3;
                }
            """)
            self._edit_btn.clicked.connect(self._on_edit_clicked)
            header_layout.addWidget(self._edit_btn)
        
        layout.addLayout(header_layout)
        
        # KPI Cards
        kpi_group = QGroupBox()
        kpi_group.setStyleSheet("""
            QGroupBox {
                background-color: #f5f5f7;
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                font-weight: 600;
                color: #1d1d1f;
            }
        """)
        kpi_layout = QHBoxLayout(kpi_group)
        kpi_layout.setSpacing(24)
        
        # Tong gia tri mua
        self._kpi_gia_tri = self._create_kpi_card(
            "Tổng giá trị mua",
            "0 đ",
            "#34c759"
        )
        kpi_layout.addWidget(self._kpi_gia_tri)
        
        # So xe da mua
        self._kpi_so_xe = self._create_kpi_card(
            "Số xe đã mua",
            "0",
            "#007aff"
        )
        kpi_layout.addWidget(self._kpi_so_xe)
        
        # Phan loai
        self._kpi_phan_loai = self._create_kpi_card(
            "Phân loại",
            "Thường",
            "#8e8e93"
        )
        kpi_layout.addWidget(self._kpi_phan_loai)
        
        layout.addWidget(kpi_group)
        
        # Classification tooltip (BR-CALC-03)
        classification_info = QLabel(
            "💡 <i>Phân loại khách hàng theo tổng giá trị mua: Thường < 500 triệu | Thân thiết ≥ 500 triệu và < 1.5 tỷ | VIP ≥ 1.5 tỷ</i>"
        )
        classification_info.setStyleSheet("""
            color: #86868b;
            font-size: 12px;
            background: #fff9e6;
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #ffcc00;
        """)
        classification_info.setWordWrap(True)
        layout.addWidget(classification_info)
        
        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: -1px;
                background: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                font-size: 14px;
                color: #86868b;
                background: #f5f5f7;
                border: 1px solid #d2d2d7;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                color: #0066cc;
                background: white;
                font-weight: 500;
            }
            QTabBar::tab:hover:!selected {
                background: #e5e5ea;
            }
        """)
        
        # Tab 1: Thông tin
        self._info_tab = self._create_info_tab()
        self._tabs.addTab(self._info_tab, "📋 Thông tin")
        
        # Tab 2: Lịch sử giao dịch
        self._history_tab = self._create_history_tab()
        self._tabs.addTab(self._history_tab, "📄 Lịch sử giao dịch")
        
        # Tab 3: Bảo hành
        self._warranty_tab = self._create_warranty_tab()
        self._tabs.addTab(self._warranty_tab, "🛡️ Bảo hành")
        
        # Tab 4: Khiếu nại
        self._complaint_tab = self._create_complaint_tab()
        self._tabs.addTab(self._complaint_tab, "⚠️ Khiếu nại")
        
        layout.addWidget(self._tabs)
    
    def _create_kpi_card(self, title: str, value: str, color: str) -> QWidget:
        """Create a KPI card widget.
        
        Args:
            title: KPI title.
            value: KPI value.
            color: Hex color for value text.
            
        Returns:
            QGroupBox with KPI card styling.
        """
        card = QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 16px;
                min-width: 150px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                font-size: 12px;
                font-weight: 500;
                color: #86868b;
            }
        """)
        card.setTitle(title)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 20, 8, 8)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {color};
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        return card
    
    def _create_info_tab(self) -> QWidget:
        """Create the info tab with customer details."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        self._info_labels = {}
        
        info_items = [
            ("ID", "id"),
            ("Họ tên", "ho_ten"),
            ("Số điện thoại", "so_dien_thoai"),
            ("Email", "email"),
            ("Địa chỉ", "dia_chi"),
            ("Ngày sinh", "ngay_sinh"),
            ("Phân loại", "phan_loai"),
            ("Tổng giá trị mua", "tong_gia_tri_mua"),
            ("Số xe đã mua", "so_xe_da_mua"),
        ]
        
        for label_text, key in info_items:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(12)
            
            label = QLabel(f"{label_text}:")
            label.setStyleSheet("font-weight: 500; color: #86868b; min-width: 150px;")
            row_layout.addWidget(label)
            
            value_label = QLabel("-")
            value_label.setStyleSheet("color: #1d1d1f; font-size: 14px;")
            row_layout.addWidget(value_label, stretch=1)
            
            layout.addLayout(row_layout)
            self._info_labels[key] = value_label
        
        layout.addStretch()
        
        return widget
    
    def _create_history_tab(self) -> QWidget:
        """Create purchase history tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(5)
        self._history_table.setHorizontalHeaderLabels([
            "Mã HĐ", "Xe", "Ngày tạo", "Tổng tiền", "Trạng thái"
        ])
        self._history_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background: white;
            }
            QHeaderView::section {
                background: #f5f5f7;
                padding: 8px;
                font-weight: 600;
            }
        """)
        self._history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self._history_table)
        
        return widget
    
    def _create_warranty_tab(self) -> QWidget:
        """Create warranty tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self._warranty_table = QTableWidget()
        self._warranty_table.setColumnCount(5)
        self._warranty_table.setHorizontalHeaderLabels([
            "Mã xe", "Ngày bắt đầu", "Ngày kết thúc", "Thời hạn", "Trạng thái"
        ])
        self._warranty_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background: white;
            }
            QHeaderView::section {
                background: #f5f5f7;
                padding: 8px;
                font-weight: 600;
            }
        """)
        self._warranty_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._warranty_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._warranty_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self._warranty_table)
        
        return widget
    
    def _create_complaint_tab(self) -> QWidget:
        """Create complaint tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self._complaint_table = QTableWidget()
        self._complaint_table.setColumnCount(4)
        self._complaint_table.setHorizontalHeaderLabels([
            "Ngày", "Tiêu đề", "Mức độ", "Trạng thái"
        ])
        self._complaint_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background: white;
            }
            QHeaderView::section {
                background: #f5f5f7;
                padding: 8px;
                font-weight: 600;
            }
        """)
        self._complaint_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._complaint_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._complaint_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self._complaint_table)
        
        return widget
    
    def _load_data(self):
        """Load customer data from database."""
        self._khach_hang = self._kh_service.get_by_id(self._khach_hang_id)
        
        if not self._khach_hang:
            QMessageBox.warning(self, "Cảnh báo", "Không tìm thấy khách hàng!")
            self._on_back_clicked()
            return
        
        # Update title
        self._title_label.setText(f"Chi tiết khách hàng - {self._khach_hang.ho_ten}")
        
        # Update KPI cards
        self._update_kpi_cards()
        
        # Populate info tab
        self._populate_info_tab()
        
        # Load purchase history
        self._load_purchase_history()
    
    def _update_kpi_cards(self):
        """Update KPI cards with customer data."""
        if not self._khach_hang:
            return
        
        # Update value labels in KPI cards
        phan_loai_labels = {
            "Thuong": ("Thường", "#8e8e93"),
            "Than_thiet": ("Thân thiết", "#007aff"),
            "VIP": ("VIP", "#ffcc00"),
        }
        
        pl_text, pl_color = phan_loai_labels.get(
            self._khach_hang.phan_loai, 
            (self._khach_hang.phan_loai, "#8e8e93")
        )
        
        # Find and update the KPI value labels
        for card in [self._kpi_gia_tri, self._kpi_so_xe, self._kpi_phan_loai]:
            card_layout = card.layout()
            if card_layout and card_layout.count() > 0:
                value_widget = card_layout.itemAt(0).widget()
                if value_widget:
                    if card == self._kpi_gia_tri:
                        value_widget.setText(f"{self._khach_hang.tong_gia_tri_mua:,.0f} đ".replace(",", "."))
                    elif card == self._kpi_so_xe:
                        value_widget.setText(str(self._khach_hang.so_xe_da_mua))
                    elif card == self._kpi_phan_loai:
                        value_widget.setText(pl_text)
                        value_widget.setStyleSheet(f"""
                            font-size: 24px;
                            font-weight: 700;
                            color: {pl_color};
                        """)
    
    def _populate_info_tab(self):
        """Populate the info tab with customer data."""
        if not self._khach_hang:
            return
        
        phan_loai_labels = {
            "Thuong": "Thường",
            "Than_thiet": "Thân thiết",
            "VIP": "VIP",
        }
        
        self._info_labels["id"].setText(str(self._khach_hang.id))
        self._info_labels["ho_ten"].setText(self._khach_hang.ho_ten)
        self._info_labels["so_dien_thoai"].setText(self._khach_hang.so_dien_thoai)
        self._info_labels["email"].setText(self._khach_hang.email or "-")
        self._info_labels["dia_chi"].setText(self._khach_hang.dia_chi or "-")
        self._info_labels["ngay_sinh"].setText(
            self._khach_hang.ngay_sinh[:10] if self._khach_hang.ngay_sinh else "-"
        )
        self._info_labels["phan_loai"].setText(phan_loai_labels.get(self._khach_hang.phan_loai, self._khach_hang.phan_loai))
        self._info_labels["tong_gia_tri_mua"].setText(f"{self._khach_hang.tong_gia_tri_mua:,.0f} đ".replace(",", "."))
        self._info_labels["so_xe_da_mua"].setText(str(self._khach_hang.so_xe_da_mua))
    
    def _load_purchase_history(self):
        """Load purchase history for this customer."""
        history = self._kh_service.get_purchase_history(self._khach_hang_id)
        
        # Populate contracts
        contracts = history.get("contracts", [])
        self._history_table.setRowCount(len(contracts))
        
        status_labels = {
            "moi_tao": "Mới tạo",
            "da_thanh_toan": "Đã thanh toán",
            "da_giao_xe": "Đã giao xe",
            "huy": "Đã hủy"
        }
        
        for i, contract in enumerate(contracts):
            self._history_table.setItem(i, 0, QTableWidgetItem(contract.get("ma_hop_dong", "")))
            
            xe_info = f"{contract.get('hang', '')} {contract.get('dong_xe', '')}"
            self._history_table.setItem(i, 1, QTableWidgetItem(xe_info))
            
            self._history_table.setItem(i, 2, QTableWidgetItem(
                contract.get("ngay_tao", "")[:10] if contract.get("ngay_tao") else "-"
            ))
            
            self._history_table.setItem(i, 3, QTableWidgetItem(
                f"{contract.get('gia_xe', 0):,.0f} đ".replace(",", ".")
            ))
            
            status_text = status_labels.get(contract.get("trang_thai", ""), contract.get("trang_thai", ""))
            self._history_table.setItem(i, 4, QTableWidgetItem(status_text))
        
        # Populate warranties
        warranties = history.get("warranties", [])
        self._warranty_table.setRowCount(len(warranties))
        
        for i, warranty in enumerate(warranties):
            self._warranty_table.setItem(i, 0, QTableWidgetItem(warranty.get("ma_xe", "")))
            self._warranty_table.setItem(i, 1, QTableWidgetItem(
                warranty.get("ngay_bat_dau", "")[:10] if warranty.get("ngay_bat_dau") else "-"
            ))
            self._warranty_table.setItem(i, 2, QTableWidgetItem(
                warranty.get("ngay_ket_thuc", "")[:10] if warranty.get("ngay_ket_thuc") else "-"
            ))
            self._warranty_table.setItem(i, 3, QTableWidgetItem(f"{warranty.get('thoi_han_bh', 0)} tháng"))
            self._warranty_table.setItem(i, 4, QTableWidgetItem(warranty.get("trang_thai", "")))
        
        # Populate complaints
        complaints = history.get("complaints", [])
        self._complaint_table.setRowCount(len(complaints))
        
        muc_do_labels = {
            "thap": "Thấp",
            "trung_binh": "Trung bình",
            "cao": "Cao",
        }
        
        for i, complaint in enumerate(complaints):
            self._complaint_table.setItem(i, 0, QTableWidgetItem(
                complaint.get("ngay_tao", "")[:10] if complaint.get("ngay_tao") else "-"
            ))
            self._complaint_table.setItem(i, 1, QTableWidgetItem(complaint.get("tieu_de", "")))
            self._complaint_table.setItem(i, 2, QTableWidgetItem(
                muc_do_labels.get(complaint.get("muc_do", ""), complaint.get("muc_do", ""))
            ))
            self._complaint_table.setItem(i, 3, QTableWidgetItem(complaint.get("trang_thai", "")))
    
    def _on_back_clicked(self):
        """Handle back button click."""
        self.close_clicked.emit()
    
    def _on_edit_clicked(self):
        """Handle edit button click."""
        if self._khach_hang:
            self.edit_clicked.emit(self._khach_hang.id)
