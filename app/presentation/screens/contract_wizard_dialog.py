"""Contract wizard dialog - S-HD-02 - Multi-step contract creation wizard.

Wizard Steps:
- B1: Select/Create Customer
- B2: Select Vehicle and Accessories
- B3: Select Promotion
- B4: Review and Confirm

Features:
- Step indicator at top (B1 → B2 → B3 → B4)
- Each step validates before allowing Next
- Running total displayed throughout
- BR-CALC-01: gia_xe + tong_pk - tien_giam_km = tong_tien

References:
- BR-HD-01..12: Contract lifecycle
- BR-KM-04: Promotion applicability
- BR-CALC-01: Total calculation
"""

from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QWidget, QScrollArea, QCheckBox,
    QSpinBox, QTextEdit, QStackedWidget, QFrame, QGraphicsOpacityEffect,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from app.application.services.hop_dong_service import (
    HopDongService, HopDongCreateData, TotalBreakdown,
    HopDongServiceError, ValidationError
)
from app.application.services.khach_hang_service import KhachHangService
from app.domain.entities import KhachHang


class ContractWizardDialog(QDialog):
    """Multi-step contract creation wizard dialog.
    
    Signals:
        saved: Emitted when contract was created successfully.
    """
    
    saved = pyqtSignal()
    
    # Wizard steps
    STEP_CUSTOMER = 0
    STEP_VEHICLE = 1
    STEP_PROMOTION = 2
    STEP_CONFIRM = 3
    
    def __init__(self, db_conn, session, parent=None):
        """Initialize contract wizard dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._hd_service = HopDongService(db_conn)
        self._kh_service = KhachHangService(db_conn)
        
        # Wizard state
        self._current_step = self.STEP_CUSTOMER
        self._selected_customer: Optional[KhachHang] = None
        self._selected_xe_id: Optional[int] = None
        self._selected_xe_info: Optional[Dict] = None
        self._selected_pk_list: List[Dict] = []
        self._selected_km_id: Optional[int] = None
        self._selected_km_info: Optional[Dict] = None
        self._notes: str = ""
        
        # Cached data
        self._xe_list: List[Dict] = []
        self._pk_list: List[Dict] = []
        self._km_list: List[Dict] = []
        
        self._setup_ui()
        self._load_wizard_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Tạo hợp đồng mới")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Step indicator
        self._step_indicator = self._create_step_indicator()
        main_layout.addWidget(self._step_indicator)
        
        # Step content area
        self._step_stack = QStackedWidget()
        main_layout.addWidget(self._step_stack, 1)
        
        # Create step pages
        self._step_customer = self._create_step_customer()
        self._step_vehicle = self._create_step_vehicle()
        self._step_promotion = self._create_step_promotion()
        self._step_confirm = self._create_step_confirm()
        
        self._step_stack.addWidget(self._step_customer)
        self._step_stack.addWidget(self._step_vehicle)
        self._step_stack.addWidget(self._step_promotion)
        self._step_stack.addWidget(self._step_confirm)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        
        self._back_btn = QPushButton("◀ Quay lại")
        self._back_btn.setStyleSheet("""
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
        self._back_btn.clicked.connect(self._on_back)
        self._back_btn.setVisible(False)
        nav_layout.addWidget(self._back_btn)
        
        self._next_btn = QPushButton("Tiếp tục ▶")
        self._next_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._next_btn.clicked.connect(self._on_next)
        nav_layout.addWidget(self._next_btn)
        
        self._cancel_btn = QPushButton("Hủy")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #86868b;
                border: none;
                padding: 12px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #1d1d1f;
            }
        """)
        self._cancel_btn.clicked.connect(self.reject)
        nav_layout.addWidget(self._cancel_btn)
        
        main_layout.addLayout(nav_layout)
        
        self._update_step_ui()
    
    def _create_step_indicator(self) -> QWidget:
        """Create the step indicator widget."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._step_labels: List[QLabel] = []
        step_names = ["B1 (Khách hàng)", "B2 (Xe & Phụ kiện)", "B3 (Khuyến mãi)", "B4 (Xác nhận)"]
        
        for i, name in enumerate(step_names):
            step_widget = QWidget()
            step_layout = QVBoxLayout(step_widget)
            step_layout.setSpacing(4)
            
            circle = QLabel("●" if i == 0 else "○")
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            circle.setStyleSheet(f"""
                font-size: 20px;
                color: #0066cc;
            """)
            step_layout.addWidget(circle)
            
            label = QLabel(name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                font-size: 12px;
                color: #0066cc;
                font-weight: {'600' if i == 0 else '400'};
            """)
            step_layout.addWidget(label)
            
            self._step_labels.append(label)
            
            layout.addWidget(step_widget)
            
            if i < len(step_names) - 1:
                arrow = QLabel("→")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                arrow.setStyleSheet("font-size: 20px; color: #d2d2d7;")
                layout.addWidget(arrow)
        
        layout.addStretch()
        return container
    
    def _create_step_customer(self) -> QWidget:
        """Create Step 1: Customer selection."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Bước 1: Chọn khách hàng")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(title)
        
        # Search group
        search_group = QGroupBox("Tìm kiếm khách hàng")
        search_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 16px;
                background-color: #fafafa;
            }
        """)
        search_layout = QVBoxLayout(search_group)
        
        search_row = QHBoxLayout()
        self._kh_search_input = QLineEdit()
        self._kh_search_input.setPlaceholderText("Nhập tên, SĐT hoặc email khách hàng...")
        self._kh_search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        self._kh_search_input.returnPressed.connect(self._on_search_customer)
        search_row.addWidget(self._kh_search_input, 1)
        
        self._kh_search_btn = QPushButton("🔍 Tìm kiếm")
        self._kh_search_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._kh_search_btn.clicked.connect(self._on_search_customer)
        search_row.addWidget(self._kh_search_btn)
        search_layout.addLayout(search_row)
        
        # Search results table
        self._kh_result_table = QTableWidget()
        self._kh_result_table.setColumnCount(4)
        self._kh_result_table.setHorizontalHeaderLabels(["ID", "Họ tên", "SĐT", "Email"])
        self._kh_result_table.setMaximumHeight(200)
        self._kh_result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._kh_result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._kh_result_table.cellClicked.connect(self._on_kh_result_clicked)
        self._kh_result_table.setStyleSheet("""
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
        search_layout.addWidget(self._kh_result_table)
        
        # Create new customer button
        self._create_kh_btn = QPushButton("➕ Tạo khách hàng mới")
        self._create_kh_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._create_kh_btn.clicked.connect(self._on_create_kh_clicked)
        search_layout.addWidget(self._create_kh_btn)
        
        layout.addWidget(search_group)
        
        # Selected customer card
        self._kh_card = QGroupBox("Khách hàng đã chọn")
        self._kh_card.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #34c759;
                border: 2px solid #34c759;
                border-radius: 8px;
                margin-top: 8px;
                padding: 16px;
                background-color: #f0fff4;
            }
        """)
        self._kh_card_layout = QVBoxLayout(self._kh_card)
        self._kh_card_info = QLabel("Chưa chọn khách hàng")
        self._kh_card_info.setStyleSheet("font-size: 14px; color: #86868b;")
        self._kh_card_layout.addWidget(self._kh_card_info)
        self._kh_card.setVisible(False)
        layout.addWidget(self._kh_card)
        
        layout.addStretch()
        return page
    
    def _create_step_vehicle(self) -> QWidget:
        """Create Step 2: Vehicle and Accessories selection."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Bước 2: Chọn xe và phụ kiện")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(title)
        
        # Vehicle selection
        vehicle_group = QGroupBox("Chọn xe")
        vehicle_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 16px;
                background-color: #fafafa;
            }
        """)
        vehicle_layout = QVBoxLayout(vehicle_group)
        
        vehicle_row = QHBoxLayout()
        vehicle_row.addWidget(QLabel("Xe (còn hàng):"))
        
        self._xe_combo = QComboBox()
        self._xe_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 400px;
            }
        """)
        self._xe_combo.currentIndexChanged.connect(self._on_xe_changed)
        vehicle_row.addWidget(self._xe_combo, 1)
        vehicle_layout.addLayout(vehicle_row)
        
        # Vehicle info card
        self._xe_card = QGroupBox("Thông tin xe")
        self._xe_card.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                margin-top: 8px;
                padding: 12px;
                background-color: white;
            }
        """)
        self._xe_card_layout = QVBoxLayout(self._xe_card)
        self._xe_info_label = QLabel("Chưa chọn xe")
        self._xe_info_label.setStyleSheet("font-size: 13px; color: #86868b;")
        self._xe_card_layout.addWidget(self._xe_info_label)
        vehicle_layout.addWidget(self._xe_card)
        
        layout.addWidget(vehicle_group)
        
        # Accessories selection
        pk_group = QGroupBox("Chọn phụ kiện đi kèm")
        pk_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 16px;
                background-color: #fafafa;
            }
        """)
        pk_layout = QVBoxLayout(pk_group)
        
        # PK table
        self._pk_table = QTableWidget()
        self._pk_table.setColumnCount(5)
        self._pk_table.setHorizontalHeaderLabels(["Chọn", "Tên phụ kiện", "Phân loại", "Giá bán", "Tồn kho"])
        self._pk_table.setMaximumHeight(200)
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
        pk_layout.addWidget(self._pk_table)
        
        # Selected accessories display
        self._selected_pk_label = QLabel("Phụ kiện đã chọn: (chưa chọn)")
        self._selected_pk_label.setStyleSheet("font-size: 13px; color: #1d1d1f; margin-top: 8px;")
        pk_layout.addWidget(self._selected_pk_label)
        
        layout.addWidget(pk_group)
        
        # Running subtotal
        self._subtotal_label = QLabel("Tạm tính: 0 đ")
        self._subtotal_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1d1d1f;
            padding: 12px;
            background-color: #f5f5f7;
            border-radius: 6px;
        """)
        layout.addWidget(self._subtotal_label)
        
        return page
    
    def _create_step_promotion(self) -> QWidget:
        """Create Step 3: Promotion selection."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Bước 3: Chọn khuyến mãi")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(title)
        
        # Promotion selection
        km_group = QGroupBox("Chương trình khuyến mãi")
        km_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 16px;
                background-color: #fafafa;
            }
        """)
        km_layout = QVBoxLayout(km_group)
        
        km_row = QHBoxLayout()
        km_row.addWidget(QLabel("Khuyến mãi:"))
        
        self._km_combo = QComboBox()
        self._km_combo.addItem("Không áp dụng khuyến mãi", None)
        self._km_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 400px;
            }
        """)
        self._km_combo.currentIndexChanged.connect(self._on_km_changed)
        km_row.addWidget(self._km_combo, 1)
        km_layout.addLayout(km_row)
        
        # Promotion info card
        self._km_card = QGroupBox("Thông tin khuyến mãi")
        self._km_card.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                margin-top: 8px;
                padding: 12px;
                background-color: white;
            }
        """)
        self._km_card_layout = QVBoxLayout(self._km_card)
        self._km_info_label = QLabel("Chưa chọn khuyến mãi")
        self._km_info_label.setStyleSheet("font-size: 13px; color: #86868b;")
        self._km_card_layout.addWidget(self._km_info_label)
        km_layout.addWidget(self._km_card)
        
        layout.addWidget(km_group)
        
        # Preview calculation
        self._calc_preview_label = QLabel("Xem trước tính tiền:")
        self._calc_preview_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(self._calc_preview_label)
        
        self._calc_preview_card = QGroupBox()
        self._calc_preview_card.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 12px;
                background-color: white;
            }
        """)
        calc_layout = QVBoxLayout(self._calc_preview_card)
        calc_layout.setSpacing(8)
        
        self._calc_gia_xe = QLabel("Giá xe: 0 đ")
        calc_layout.addWidget(self._calc_gia_xe)
        
        self._calc_pk = QLabel("Phụ kiện: 0 đ")
        calc_layout.addWidget(self._calc_pk)
        
        self._calc_km = QLabel("Giảm giá KM: 0 đ")
        self._calc_km.setStyleSheet("color: #34c759;")
        calc_layout.addWidget(self._calc_km)
        
        self._calc_tong = QLabel("TỔNG CỘNG: 0 đ")
        self._calc_tong.setStyleSheet("font-weight: 700; font-size: 15px; color: #1d1d1f;")
        calc_layout.addWidget(self._calc_tong)
        
        layout.addWidget(self._calc_preview_card)
        
        layout.addStretch()
        return page
    
    def _create_step_confirm(self) -> QWidget:
        """Create Step 4: Review and Confirm."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Bước 4: Xác nhận tạo hợp đồng")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        
        # Customer section
        kh_section = QGroupBox("Thông tin khách hàng")
        kh_section.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background-color: white;
            }
        """)
        kh_section_layout = QVBoxLayout(kh_section)
        self._confirm_kh_label = QLabel("...")
        self._confirm_kh_label.setStyleSheet("font-size: 13px; color: #3c3c43; font-weight: 400;")
        kh_section_layout.addWidget(self._confirm_kh_label)
        scroll_layout.addWidget(kh_section)
        
        # Vehicle section
        xe_section = QGroupBox("Thông tin xe")
        xe_section.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background-color: white;
            }
        """)
        xe_section_layout = QVBoxLayout(xe_section)
        self._confirm_xe_label = QLabel("...")
        self._confirm_xe_label.setStyleSheet("font-size: 13px; color: #3c3c43; font-weight: 400;")
        xe_section_layout.addWidget(self._confirm_xe_label)
        scroll_layout.addWidget(xe_section)
        
        # Accessories section
        pk_section = QGroupBox("Phụ kiện đi kèm")
        pk_section.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background-color: white;
            }
        """)
        pk_section_layout = QVBoxLayout(pk_section)
        self._confirm_pk_label = QLabel("Không có")
        self._confirm_pk_label.setStyleSheet("font-size: 13px; color: #3c3c43; font-weight: 400;")
        pk_section_layout.addWidget(self._confirm_pk_label)
        scroll_layout.addWidget(pk_section)
        
        # Promotion section
        km_section = QGroupBox("Khuyến mãi")
        km_section.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background-color: white;
            }
        """)
        km_section_layout = QVBoxLayout(km_section)
        self._confirm_km_label = QLabel("Không áp dụng")
        self._confirm_km_label.setStyleSheet("font-size: 13px; color: #3c3c43; font-weight: 400;")
        km_section_layout.addWidget(self._confirm_km_label)
        scroll_layout.addWidget(km_section)
        
        # Total breakdown
        total_section = QGroupBox("Tổng hợp thanh toán")
        total_section.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #0066cc;
                border-radius: 8px;
                padding: 16px;
                background-color: #f0f7ff;
            }
        """)
        total_section_layout = QVBoxLayout(total_section)
        total_section_layout.setSpacing(8)
        
        self._confirm_gia_xe = QLabel("Giá xe: 0 đ")
        total_section_layout.addWidget(self._confirm_gia_xe)
        
        self._confirm_pk_total = QLabel("Phụ kiện: 0 đ")
        total_section_layout.addWidget(self._confirm_pk_total)
        
        self._confirm_km_discount = QLabel("Giảm giá KM: 0 đ")
        self._confirm_km_discount.setStyleSheet("color: #34c759;")
        total_section_layout.addWidget(self._confirm_km_discount)
        
        self._confirm_tong = QLabel("TỔNG CỘNG: 0 đ")
        confirm_tong_font = QFont()
        confirm_tong_font.setPointSize(16)
        confirm_tong_font.setBold(True)
        self._confirm_tong.setFont(confirm_tong_font)
        self._confirm_tong.setStyleSheet("color: #0066cc;")
        total_section_layout.addWidget(self._confirm_tong)
        
        scroll_layout.addWidget(total_section)
        
        # Notes
        notes_section = QGroupBox("Ghi chú (tùy chọn)")
        notes_section.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background-color: white;
            }
        """)
        notes_layout = QVBoxLayout(notes_section)
        self._notes_input = QTextEdit()
        self._notes_input.setPlaceholderText("Nhập ghi chú nếu có...")
        self._notes_input.setMaximumHeight(80)
        self._notes_input.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 13px;
                background: white;
            }
        """)
        notes_layout.addWidget(self._notes_input)
        scroll_layout.addWidget(notes_section)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        
        return page
    
    def _load_wizard_data(self):
        """Load data needed for wizard steps."""
        # Load vehicles with stock > 0
        try:
            cursor = self._db_conn.execute(
                """SELECT id, ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton
                   FROM xe WHERE so_luong_ton > 0 AND trang_thai = 'con_hang'
                   ORDER BY hang, dong_xe"""
            )
            self._xe_list = [dict(row) for row in cursor.fetchall()]
            
            self._xe_combo.clear()
            for xe in self._xe_list:
                display = f"{xe['hang']} {xe['dong_xe']} {xe['nam_san_xuat']} - {xe['mau_sac']} ({xe['so_luong_ton']} xe) - {xe['gia_ban']:,} đ".replace(",", ".")
                self._xe_combo.addItem(display, xe['id'])
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải danh sách xe: {str(e)}")
        
        # Load accessories with stock > 0
        try:
            cursor = self._db_conn.execute(
                """SELECT id, ma_pk, ten_pk, phan_loai, gia_ban, ton_kho
                   FROM phu_kien WHERE ton_kho > 0
                   ORDER BY ten_pk"""
            )
            self._pk_list = [dict(row) for row in cursor.fetchall()]
            
            self._pk_table.setRowCount(len(self._pk_list))
            for i, pk in enumerate(self._pk_list):
                checkbox = QCheckBox()
                checkbox.stateChanged.connect(lambda state, row=i: self._on_pk_toggled(row, state))
                self._pk_table.setCellWidget(i, 0, checkbox)
                
                self._pk_table.setItem(i, 1, QTableWidgetItem(pk['ten_pk']))
                self._pk_table.setItem(i, 2, QTableWidgetItem(pk['phan_loai']))
                
                gia_item = QTableWidgetItem(f"{pk['gia_ban']:,} đ".replace(",", "."))
                gia_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self._pk_table.setItem(i, 3, gia_item)
                
                self._pk_table.setItem(i, 4, QTableWidgetItem(str(pk['ton_kho'])))
            
            self._pk_table.setColumnWidth(1, 200)
            self._pk_table.setColumnWidth(2, 100)
            self._pk_table.setColumnWidth(3, 100)
            self._pk_table.setColumnWidth(4, 80)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải danh sách phụ kiện: {str(e)}")
        
        # Load promotions
        self._load_promotions()
    
    def _load_promotions(self):
        """Load available promotions for current vehicle."""
        if not self._selected_xe_id:
            self._km_combo.clear()
            self._km_combo.addItem("Không áp dụng khuyến mãi", None)
            return
        
        try:
            cursor = self._db_conn.execute(
                """SELECT id, ten_km, loai_km, gia_tri, kieu_gia_tri, mo_ta
                   FROM khuyen_mai
                   WHERE trang_thai = 'dang_chay'
                   AND den_ngay >= date('now')
                   ORDER BY ten_km"""
            )
            self._km_list = [dict(row) for row in cursor.fetchall()]
            
            self._km_combo.clear()
            self._km_combo.addItem("Không áp dụng khuyến mãi", None)
            for km in self._km_list:
                display = f"{km['ten_km']} ({km['loai_km']})"
                self._km_combo.addItem(display, km['id'])
        except Exception as e:
            pass
    
    def _update_step_ui(self):
        """Update UI based on current step."""
        # Update step indicator
        for i, label in enumerate(self._step_labels):
            if i < self._current_step:
                label.setStyleSheet("font-size: 12px; color: #34c759; font-weight: 600;")
            elif i == self._current_step:
                label.setStyleSheet("font-size: 12px; color: #0066cc; font-weight: 700;")
            else:
                label.setStyleSheet("font-size: 12px; color: #86868b; font-weight: 400;")
        
        # Switch step content
        self._step_stack.setCurrentIndex(self._current_step)
        
        # Update navigation buttons
        self._back_btn.setVisible(self._current_step > 0)
        
        if self._current_step == self.STEP_CONFIRM:
            self._next_btn.setText("💾 Xác nhận lưu")
            self._next_btn.setStyleSheet("""
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
            self._update_confirm_summary()
        else:
            self._next_btn.setText("Tiếp tục ▶")
            self._next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0066cc;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #0055aa;
                }
            """)
    
    def _validate_step(self, step: int) -> bool:
        """Validate current step before proceeding.
        
        Args:
            step: Step index to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        if step == self.STEP_CUSTOMER:
            if not self._selected_customer:
                QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn khách hàng trước khi tiếp tục.")
                return False
            return True
        
        elif step == self.STEP_VEHICLE:
            if not self._selected_xe_id:
                QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn xe trước khi tiếp tục.")
                return False
            return True
        
        elif step == self.STEP_PROMOTION:
            return True
        
        return True
    
    def _on_back(self):
        """Handle back button."""
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step_ui()
    
    def _on_next(self):
        """Handle next button."""
        if self._current_step == self.STEP_CONFIRM:
            self._on_submit()
            return
        
        if self._validate_step(self._current_step):
            self._current_step += 1
            self._update_step_ui()
    
    def _on_search_customer(self):
        """Search for customers."""
        keyword = self._kh_search_input.text().strip()
        if not keyword:
            return
        
        try:
            result = self._kh_service.search(keyword=keyword, page=1, page_size=50)
            
            self._kh_result_table.setRowCount(len(result.items))
            for i, kh in enumerate(result.items):
                self._kh_result_table.setItem(i, 0, QTableWidgetItem(str(kh.id)))
                self._kh_result_table.setItem(i, 1, QTableWidgetItem(kh.ho_ten))
                self._kh_result_table.setItem(i, 2, QTableWidgetItem(kh.so_dien_thoai))
                self._kh_result_table.setItem(i, 3, QTableWidgetItem(kh.email or "-"))
                self._kh_result_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, kh.id)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tìm kiếm: {str(e)}")
    
    def _on_kh_result_clicked(self, row: int, col: int):
        """Handle customer selection from search results."""
        item = self._kh_result_table.item(row, 0)
        if not item:
            return
        
        kh_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            kh = self._kh_service.get_by_id(kh_id)
            if kh:
                self._selected_customer = kh
                self._show_kh_card(kh)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể chọn khách hàng: {str(e)}")
    
    def _show_kh_card(self, kh: KhachHang):
        """Show selected customer card."""
        self._kh_card.setVisible(True)
        self._kh_card_info.setText(
            f"<b>{kh.ho_ten}</b><br>"
            f"SĐT: {kh.so_dien_thoai}<br>"
            f"Email: {kh.email or 'N/A'}<br>"
            f"Phân loại: {kh.phan_loai}"
        )
    
    def _on_create_kh_clicked(self):
        """Handle create new customer button."""
        # Open inline customer form
        from app.presentation.screens.customer_form_dialog import CustomerFormDialog
        
        dialog = CustomerFormDialog(self._db_conn, self._session, parent=self)
        dialog.saved.connect(self._on_kh_created)
        dialog.exec()
    
    def _on_kh_created(self):
        """Handle customer created event."""
        QMessageBox.information(self, "Thành công", "Đã tạo khách hàng mới. Vui lòng tìm kiếm để chọn.")
    
    def _on_xe_changed(self, index: int):
        """Handle vehicle selection change."""
        if index < 0:
            return
        
        xe_id = self._xe_combo.currentData()
        if not xe_id:
            self._selected_xe_id = None
            self._selected_xe_info = None
            self._xe_info_label.setText("Chưa chọn xe")
            return
        
        # Find xe info
        xe = next((x for x in self._xe_list if x['id'] == xe_id), None)
        if xe:
            self._selected_xe_id = xe_id
            self._selected_xe_info = xe
            self._xe_info_label.setText(
                f"<b>{xe['hang']} {xe['dong_xe']}</b><br>"
                f"Mã xe: {xe['ma_xe']}<br>"
                f"Năm SX: {xe['nam_san_xuat']} | Màu: {xe['mau_sac']}<br>"
                f"<span style='color:#0066cc;'>Giá bán: {xe['gia_ban']:,} đ</span> "
                f"<span style='color:#86868b; font-size:11px;'>(Giá này sẽ cố định trên HĐ)</span>"
            )
            self._update_subtotal()
            self._load_promotions()
    
    def _on_pk_toggled(self, row: int, state: int):
        """Handle accessory checkbox toggle."""
        pk = self._pk_list[row]
        
        if state == Qt.CheckState.Checked.value:
            # Add to selected list if not already there
            if not any(p['phu_kien_id'] == pk['id'] for p in self._selected_pk_list):
                self._selected_pk_list.append({
                    'phu_kien_id': pk['id'],
                    'ten_pk': pk['ten_pk'],
                    'gia_ban': pk['gia_ban'],
                    'so_luong': 1
                })
        else:
            # Remove from selected list
            self._selected_pk_list = [
                p for p in self._selected_pk_list if p['phu_kien_id'] != pk['id']
            ]
        
        self._update_pk_display()
        self._update_subtotal()
    
    def _update_pk_display(self):
        """Update selected accessories display."""
        if not self._selected_pk_list:
            self._selected_pk_label.setText("Phụ kiện đã chọn: (chưa chọn)")
        else:
            pk_texts = [f"{p['ten_pk']} - {p['gia_ban']:,} đ".replace(",", ".") for p in self._selected_pk_list]
            self._selected_pk_label.setText(f"Phụ kiện đã chọn: {', '.join(pk_texts)}")
    
    def _update_subtotal(self):
        """Update running subtotal."""
        if not self._selected_xe_info:
            self._subtotal_label.setText("Tạm tính: 0 đ")
            return
        
        xe_price = self._selected_xe_info.get('gia_ban', 0)
        pk_total = sum(p['gia_ban'] * p['so_luong'] for p in self._selected_pk_list)
        
        subtotal = xe_price + pk_total
        self._subtotal_label.setText(f"Tạm tính: {subtotal:,} đ".replace(",", "."))
    
    def _on_km_changed(self, index: int):
        """Handle promotion selection change."""
        km_id = self._km_combo.currentData()
        
        if km_id is None:
            self._selected_km_id = None
            self._selected_km_info = None
            self._km_info_label.setText("Không áp dụng khuyến mãi")
        else:
            km = next((k for k in self._km_list if k['id'] == km_id), None)
            if km:
                self._selected_km_id = km_id
                self._selected_km_info = km
                self._km_info_label.setText(
                    f"<b>{km['ten_km']}</b><br>"
                    f"Loại: {km['loai_km']}<br>"
                    f"Giá trị: {km['gia_tri']:,} đ".replace(",", ".")
                )
        
        self._update_calc_preview()
    
    def _update_calc_preview(self):
        """Update calculation preview on promotion step."""
        if not self._selected_xe_info:
            return
        
        xe_price = self._selected_xe_info.get('gia_ban', 0)
        pk_total = sum(p['gia_ban'] * p['so_luong'] for p in self._selected_pk_list)
        
        self._calc_gia_xe.setText(f"Giá xe: {xe_price:,} đ".replace(",", "."))
        self._calc_pk.setText(f"Phụ kiện: {pk_total:,} đ".replace(",", "."))
        
        # Calculate discount
        km_discount = 0
        if self._selected_km_info:
            km = self._selected_km_info
            loai_km = km['loai_km']
            gia_tri = km['gia_tri']
            kieu = km.get('kieu_gia_tri', 'tien')
            
            if loai_km == 'giam_tien_mat':
                km_discount = gia_tri
            elif loai_km == 'giam_phan_tram':
                if kieu == 'phan_tram':
                    km_discount = int((xe_price + pk_total) * gia_tri / 100)
                else:
                    km_discount = gia_tri
            elif loai_km == 'combo':
                km_discount = int((xe_price + pk_total) * (1 - gia_tri))
            # tang_phu_kien: no discount
        
        tong = max(0, xe_price + pk_total - km_discount)
        
        self._calc_km.setText(f"Giảm giá KM: -{km_discount:,} đ".replace(",", "."))
        self._calc_tong.setText(f"TỔNG CỘNG: {tong:,} đ".replace(",", "."))
    
    def _update_confirm_summary(self):
        """Update confirmation step summary."""
        # Customer
        if self._selected_customer:
            self._confirm_kh_label.setText(
                f"<b>{self._selected_customer.ho_ten}</b><br>"
                f"SĐT: {self._selected_customer.so_dien_thoai} | Email: {self._selected_customer.email or 'N/A'}"
            )
        
        # Vehicle
        if self._selected_xe_info:
            self._confirm_xe_label.setText(
                f"<b>{self._selected_xe_info['hang']} {self._selected_xe_info['dong_xe']}</b><br>"
                f"Mã xe: {self._selected_xe_info['ma_xe']} | "
                f"Năm SX: {self._selected_xe_info['nam_san_xuat']} | Màu: {self._selected_xe_info['mau_sac']}<br>"
                f"<span style='color:#0066cc;'>Giá cố định: {self._selected_xe_info['gia_ban']:,} đ</span>".replace(",", ".")
            )
        
        # Accessories
        if self._selected_pk_list:
            pk_texts = []
            for p in self._selected_pk_list:
                pk_texts.append(f"- {p['ten_pk']}: {p['gia_ban']:,} đ × {p['so_luong']}".replace(",", "."))
            self._confirm_pk_label.setText("<br>".join(pk_texts))
        else:
            self._confirm_pk_label.setText("Không có phụ kiện đi kèm")
        
        # Promotion
        if self._selected_km_info:
            self._confirm_km_label.setText(
                f"<b>{self._selected_km_info['ten_km']}</b><br>"
                f"Loại: {self._selected_km_info['loai_km']} | "
                f"Giá trị: {self._selected_km_info['gia_tri']:,} đ".replace(",", ".")
            )
        else:
            self._confirm_km_label.setText("Không áp dụng khuyến mãi")
        
        # Calculate totals
        xe_price = self._selected_xe_info.get('gia_ban', 0) if self._selected_xe_info else 0
        pk_total = sum(p['gia_ban'] * p['so_luong'] for p in self._selected_pk_list)
        
        km_discount = 0
        if self._selected_km_info:
            km = self._selected_km_info
            loai_km = km['loai_km']
            gia_tri = km['gia_tri']
            kieu = km.get('kieu_gia_tri', 'tien')
            
            if loai_km == 'giam_tien_mat':
                km_discount = gia_tri
            elif loai_km == 'giam_phan_tram':
                if kieu == 'phan_tram':
                    km_discount = int((xe_price + pk_total) * gia_tri / 100)
                else:
                    km_discount = gia_tri
            elif loai_km == 'combo':
                km_discount = int((xe_price + pk_total) * (1 - gia_tri))
        
        tong = max(0, xe_price + pk_total - km_discount)
        
        self._confirm_gia_xe.setText(f"Giá xe: {xe_price:,} đ".replace(",", "."))
        self._confirm_pk_total.setText(f"Phụ kiện: {pk_total:,} đ".replace(",", "."))
        self._confirm_km_discount.setText(f"Giảm giá KM: -{km_discount:,} đ".replace(",", "."))
        self._confirm_tong.setText(f"TỔNG CỘNG: {tong:,} đ".replace(",", "."))
    
    def _on_submit(self):
        """Handle form submission."""
        if not self._selected_customer or not self._selected_xe_id:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng hoàn thành tất cả các bước.")
            return
        
        try:
            data = HopDongCreateData(
                khach_hang_id=self._selected_customer.id,
                xe_id=self._selected_xe_id,
                nhan_vien_id=self._session.nhan_vien_id if self._session else None,
                khuyen_mai_id=self._selected_km_id,
                ghi_chu=self._notes_input.toPlainText().strip(),
                created_by=self._session.nhan_vien_id if self._session else None,
            )
            
            phu_kien_list = [
                {"phu_kien_id": p['phu_kien_id'], "so_luong": p['so_luong']}
                for p in self._selected_pk_list
            ]
            
            self._hd_service.create(
                data,
                phu_kien_list=phu_kien_list,
                nhan_vien_id=self._session.nhan_vien_id if self._session else None,
            )
            
            QMessageBox.information(self, "Thành công", "Đã tạo hợp đồng mới thành công!")
            self.saved.emit()
            self.accept()
            
        except HopDongServiceError as e:
            QMessageBox.critical(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo hợp đồng: {str(e)}")
