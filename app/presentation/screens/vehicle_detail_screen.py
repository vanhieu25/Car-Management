"""Vehicle detail screen - S-XE-03 - Vehicle details with tabs.

Features:
- Tab 1: Thông tin (Vehicle info)
- Tab 2: Lịch sử nhập (Import history) 
- Tab 3: HĐ đã bán (Sold contracts)
- Tab 4: KM áp dụng (Applied promotions)

References:
- UC-XE-05: Xem chi tiết xe
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QGroupBox,
    QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.application.services.xe_service import XeService
from app.application.services.session import CurrentSession
from app.domain.entities import Xe


class VehicleDetailScreen(QWidget):
    """Vehicle detail screen with tabs - S-XE-03.
    
    Signals:
        edit_clicked: User wants to edit this vehicle.
        close_clicked: User wants to close this detail view.
    """
    
    edit_clicked = pyqtSignal(int)  # xe_id
    close_clicked = pyqtSignal()
    
    def __init__(self, db_conn, session: CurrentSession, xe_id: int, parent=None):
        """Initialize vehicle detail screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            xe_id: Vehicle ID to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._xe_service = XeService(db_conn)
        self._xe_id = xe_id
        self._xe: Optional[Xe] = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with vehicle code and back button
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
        
        self._title_label = QLabel("Chi tiết xe")
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
        
        # Tab 2: Lịch sử nhập kho
        self._import_tab = self._create_import_history_tab()
        self._tabs.addTab(self._import_tab, "📥 Lịch sử nhập kho")
        
        # Tab 3: HĐ đã bán
        self._contract_tab = self._create_contract_tab()
        self._tabs.addTab(self._contract_tab, "📄 Hợp đồng đã bán")
        
        # Tab 4: KM áp dụng
        self._promo_tab = self._create_promotion_tab()
        self._tabs.addTab(self._promo_tab, "🎁 Khuyến mãi áp dụng")
        
        layout.addWidget(self._tabs)
    
    def _create_info_tab(self) -> QWidget:
        """Create the info tab with vehicle details."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Info grid
        self._info_labels = {}
        
        info_items = [
            ("Mã xe", "ma_xe"),
            ("Hãng", "hang"),
            ("Dòng xe", "dong_xe"),
            ("Năm sản xuất", "nam_san_xuat"),
            ("Màu sắc", "mau_sac"),
            ("Giá bán", "gia_ban"),
            ("Số lượng tồn", "so_luong_ton"),
            ("Mức tồn tối thiểu", "muc_toi_thieu"),
            ("Trạng thái", "trang_thai"),
            ("Ngày nhập đầu tiên", "ngay_nhap_dau_tien"),
            ("Mô tả", "mo_ta"),
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
    
    def _create_import_history_tab(self) -> QWidget:
        """Create import history tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self._import_table = QTableWidget()
        self._import_table.setColumnCount(4)
        self._import_table.setHorizontalHeaderLabels(["Ngày", "Số lượng nhập", "Giá nhập", "Ghi chú"])
        self._import_table.setStyleSheet("""
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
        self._import_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._import_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._import_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self._import_table)
        
        return widget
    
    def _create_contract_tab(self) -> QWidget:
        """Create sold contracts tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self._contract_table = QTableWidget()
        self._contract_table.setColumnCount(5)
        self._contract_table.setHorizontalHeaderLabels(["Mã HĐ", "Khách hàng", "Ngày ký", "Giá xe", "Trạng thái"])
        self._contract_table.setStyleSheet("""
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
        self._contract_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._contract_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._contract_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self._contract_table)
        
        return widget
    
    def _create_promotion_tab(self) -> QWidget:
        """Create promotions tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self._promo_table = QTableWidget()
        self._promo_table.setColumnCount(4)
        self._promo_table.setHorizontalHeaderLabels(["Tên KM", "Loại", "Giá trị", "Thời gian áp dụng"])
        self._promo_table.setStyleSheet("""
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
        self._promo_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._promo_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._promo_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self._promo_table)
        
        return widget
    
    def _load_data(self):
        """Load vehicle data from database."""
        self._xe = self._xe_service.get_by_id(self._xe_id)
        
        if not self._xe:
            QMessageBox.warning(self, "Cảnh báo", "Không tìm thấy xe!")
            self._on_back_clicked()
            return
        
        # Update title
        self._title_label.setText(f"Chi tiết xe - {self._xe.ma_xe}")
        
        # Populate info tab
        self._populate_info_tab()
        
        # Load related data for other tabs
        self._load_import_history()
        self._load_contracts()
        self._load_promotions()
    
    def _populate_info_tab(self):
        """Populate the info tab with vehicle data."""
        if not self._xe:
            return
        
        status_text = {
            "con_hang": "Còn hàng",
            "da_ban": "Đã bán",
            "sap_ve": "Sắp về"
        }.get(self._xe.trang_thai, self._xe.trang_thai)
        
        self._info_labels["ma_xe"].setText(self._xe.ma_xe)
        self._info_labels["hang"].setText(self._xe.hang)
        self._info_labels["dong_xe"].setText(self._xe.dong_xe)
        self._info_labels["nam_san_xuat"].setText(str(self._xe.nam_san_xuat))
        self._info_labels["mau_sac"].setText(self._xe.mau_sac or "-")
        self._info_labels["gia_ban"].setText(f"{self._xe.gia_ban:,.0f} đ".replace(",", "."))
        self._info_labels["so_luong_ton"].setText(str(self._xe.so_luong_ton))
        self._info_labels["muc_toi_thieu"].setText(str(self._xe.muc_toi_thieu))
        self._info_labels["trang_thai"].setText(status_text)
        self._info_labels["ngay_nhap_dau_tien"].setText(
            self._xe.ngay_nhap_dau_tien[:10] if self._xe.ngay_nhap_dau_tien else "-"
        )
        self._info_labels["mo_ta"].setText(self._xe.mo_ta or "-")
    
    def _load_import_history(self):
        """Load import history for this vehicle."""
        # For now, show empty - would need NhapKho table/repository
        self._import_table.setRowCount(0)
        
        # Add placeholder row indicating feature not yet implemented
        self._import_table.setRowCount(1)
        self._import_table.setItem(0, 0, QTableWidgetItem("Chưa có dữ liệu"))
        self._import_table.setItem(0, 1, QTableWidgetItem("-"))
        self._import_table.setItem(0, 2, QTableWidgetItem("-"))
        self._import_table.setItem(0, 3, QTableWidgetItem("Tính năng sẽ được cập nhật sau"))
    
    def _load_contracts(self):
        """Load contracts that include this vehicle."""
        cursor = self._db_conn.execute(
            """SELECT hd.ma_hop_dong, kh.ho_ten, hd.ngay_tao, hd.gia_xe, hd.trang_thai
               FROM hop_dong hd
               JOIN khach_hang kh ON hd.khach_hang_id = kh.id
               WHERE hd.xe_id = ?
               ORDER BY hd.ngay_tao DESC""",
            (self._xe_id,)
        )
        
        rows = cursor.fetchall()
        self._contract_table.setRowCount(len(rows))
        
        status_text = {
            "moi_tao": "Mới tạo",
            "da_thanh_toan": "Đã thanh toán",
            "da_giao_xe": "Đã giao xe",
            "huy": "Đã hủy"
        }
        
        for i, row in enumerate(rows):
            self._contract_table.setItem(i, 0, QTableWidgetItem(row[0]))
            self._contract_table.setItem(i, 1, QTableWidgetItem(row[1]))
            self._contract_table.setItem(i, 2, QTableWidgetItem(row[2][:10] if row[2] else "-"))
            self._contract_table.setItem(i, 3, QTableWidgetItem(f"{row[3]:,.0f} đ".replace(",", ".")))
            self._contract_table.setItem(i, 4, QTableWidgetItem(status_text.get(row[4], row[4])))
    
    def _load_promotions(self):
        """Load promotions applicable to this vehicle."""
        # Query promotions that apply to this vehicle's brand/model
        cursor = self._db_conn.execute(
            """SELECT km.ten_km, km.loai_km, km.gia_tri, km.tu_ngay, km.den_ngay
               FROM khuyen_mai km
               LEFT JOIN km_pham_vi kmv ON km.id = kmv.khuyen_mai_id
               WHERE km.trang_thai = 'dang_chay'
               AND (
                   kmv.pham_vi_type = 'hang' AND kmv.gia_tri = ?
                   OR kmv.pham_vi_type = 'dong_xe' AND kmv.gia_tri = ?
                   OR kmv.pham_vi_type = 'xe' AND kmv.gia_tri = ?
                   OR NOT EXISTS (SELECT 1 FROM km_pham_vi WHERE khuyen_mai_id = km.id)
               )
               ORDER BY km.den_ngay DESC""",
            (self._xe.hang, self._xe.dong_xe, self._xe.ma_xe)
        )
        
        rows = cursor.fetchall()
        self._promo_table.setRowCount(len(rows))
        
        for i, row in enumerate(rows):
            self._promo_table.setItem(i, 0, QTableWidgetItem(row[0]))
            self._promo_table.setItem(i, 1, QTableWidgetItem(row[1]))
            gia_tri = f"{row[2]:,.0f} đ" if row[1] == "giam_tien_mat" else f"{row[2]}%"
            self._promo_table.setItem(i, 2, QTableWidgetItem(gia_tri))
            thoi_gian = f"{row[3][:10]} - {row[4][:10]}" if row[3] and row[4] else "-"
            self._promo_table.setItem(i, 3, QTableWidgetItem(thoi_gian))
    
    def _on_back_clicked(self):
        """Handle back button click."""
        self.close_clicked.emit()
    
    def _on_edit_clicked(self):
        """Handle edit button click."""
        if self._xe:
            self.edit_clicked.emit(self._xe.id)
