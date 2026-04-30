"""Combo manager screen - S-PK-03 - Combo listing and creation wizard.

Features:
- Combo list table: ten_combo, so_luong_pk, he_so_giam, gia_goc, gia_combo, tien_tiet_kiem
- "Tạo combo mới" button → wizard dialog:
  - Step 1: Select PK items (multi-select from phu_kien list)
  - Step 2: Set he_so_giam (slider 0.5-1.0)
  - Step 3: Preview calculated price with breakdown
  - Confirm button
- Combo card display: "Giá thường: X — Giá combo: Y — Tiết kiệm: Z"
- Format money with VND suffix
"""

from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QDialog, QListWidget, QListWidgetItem, QSlider,
    QDoubleSpinBox, QTextEdit, QCheckBox, QScrollArea, QFrame,
    QStackedWidget, QWizard, QWizardPage, QWizardStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

from app.application.services.combo_service import (
    ComboService, ComboDetail, ComboCreateData, ComboItemData,
    ValidationError, ComboNotFoundError
)
from app.application.services.phu_kien_service import PhuKienService
from app.application.services.session import CurrentSession
from app.domain.entities import PhuKien


PAGE_SIZE = 50


def format_money(amount: int) -> str:
    """Format money with VND suffix."""
    return f"{amount:,} đ".replace(",", ".")


class ComboCardWidget(QFrame):
    """A card widget displaying combo information with price breakdown."""

    def __init__(self, combo: ComboDetail, parent=None):
        """Initialize combo card.

        Args:
            combo: ComboDetail entity.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._combo = combo
        self._setup_ui()

    def _setup_ui(self):
        """Set up UI components."""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame:hover {
                border: 2px solid #0066cc;
            }
        """)
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header: name and discount badge
        header_layout = QHBoxLayout()

        name_label = QLabel(self._combo.ten_combo)
        name_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(name_label)

        header_layout.addStretch()

        badge_text = f"-{int((1 - self._combo.he_so_giam) * 100)}%"
        badge_label = QLabel(badge_text)
        badge_label.setStyleSheet("""
            background-color: #ff3b30;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 13px;
        """)
        header_layout.addWidget(badge_label)

        layout.addLayout(header_layout)

        # Price breakdown: "Giá thường: X — Giá combo: Y — Tiết kiệm: Z"
        price_text = (
            f"<span style='color: #86868b;'>Giá thường:</span> "
            f"<span style='text-decoration: line-through; color: #86868b;'>{format_money(self._combo.gia_goc)}</span> "
            f"<span style='color: #1d1d1f; font-weight: 600;'>— Giá combo:</span> "
            f"<span style='color: #34c759; font-weight: 600; font-size: 16px;'>{format_money(self._combo.gia_combo)}</span> "
            f"<span style='color: #ff3b30;'>— Tiết kiệm: {format_money(self._combo.tien_tiet_kiem)}</span>"
        )
        price_label = QLabel(price_text)
        price_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(price_label)

        # Items count
        items_text = f"{len(self._combo.items)} phụ kiện"
        items_label = QLabel(items_text)
        items_label.setStyleSheet("color: #86868b; font-size: 13px;")
        layout.addWidget(items_label)


class ComboWizard(QWizard):
    """Wizard dialog for creating a new combo.

    Step 1: Select PK items (multi-select)
    Step 2: Set he_so_giam (slider)
    Step 3: Preview calculated price
    """

    def __init__(self, db_conn, session, parent=None):
        """Initialize combo wizard.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._pk_service = PhuKienService(db_conn, session)
        self._combo_service = ComboService(db_conn, session)

        self._selected_items: List[tuple] = []  # (phu_kien_id, so_luong)
        self._ten_combo = ""
        self._he_so_giam = 0.9

        self.setWindowTitle("Tạo combo phụ kiện mới")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setStyleSheet("""
            QWizard {
                background-color: #f5f5f7;
            }
            QWizardPage {
                background-color: white;
                padding: 20px;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
            }
        """)

        # Add pages
        self._step1_page = self._create_step1()
        self._step2_page = self._create_step2()
        self._step3_page = self._create_step3()

        self.setPage(1, self._step1_page)
        self.setPage(2, self._step2_page)
        self.setPage(3, self._step3_page)

        # Custom styling
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

    def _create_step1(self) -> QWizardPage:
        """Create step 1: Select PK items."""
        page = QWizardPage()
        page.setTitle("Bước 1: Chọn phụ kiện")
        page.setSubTitle("Chọn ít nhất 2 phụ kiện cho combo")

        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        # Name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Tên combo:"))
        self._ten_combo_input = QLineEdit()
        self._ten_combo_input.setPlaceholderText("Nhập tên combo...")
        self._ten_combo_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        name_layout.addWidget(self._ten_combo_input, stretch=1)
        layout.addLayout(name_layout)

        # Available accessories list
        layout.addWidget(QLabel("Danh sách phụ kiện có sẵn:"))

        self._accessory_list = QListWidget()
        self._accessory_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self._accessory_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f5f5f7;
            }
            QListWidget::item:selected {
                background-color: #0066cc;
                color: white;
            }
        """)

        # Populate with available accessories
        accessories = self._pk_service.get_available()
        for pk in accessories:
            item = QListWidgetItem(f"{pk.ten_pk} - {format_money(pk.gia_ban)} (Còn: {pk.ton_kho})")
            item.setData(Qt.ItemDataRole.UserRole, pk.id)
            self._accessory_list.addItem(item)

        layout.addWidget(self._accessory_list)

        # Selected count
        self._selected_count_label = QLabel("Đã chọn: 0 phụ kiện")
        self._selected_count_label.setStyleSheet("color: #86868b; font-size: 13px;")
        layout.addWidget(self._selected_count_label)

        # Connect selection change
        self._accessory_list.itemSelectionChanged.connect(self._on_selection_changed)

        return page

    def _create_step2(self) -> QWizardPage:
        """Create step 2: Set he_so_giam."""
        page = QWizardPage()
        page.setTitle("Bước 2: Thiết lập hệ số giảm giá")
        page.setSubTitle("Chọn hệ số giảm giá cho combo (50% - 100%)")

        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        layout.addStretch()

        # Current discount display
        self._discount_label = QLabel("Giảm 10%")
        self._discount_label.setStyleSheet("""
            font-size: 48px;
            font-weight: 700;
            color: #ff3b30;
        """)
        self._discount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._discount_label)

        # Slider
        self._he_so_slider = QSlider(Qt.Orientation.Horizontal)
        self._he_so_slider.setMinimum(50)
        self._he_so_slider.setMaximum(100)
        self._he_so_slider.setValue(90)
        self._he_so_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._he_so_slider.setTickInterval(5)
        self._he_so_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #e5e5ea;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 20px;
                background: #0066cc;
                border-radius: 10px;
                margin: -6px 0;
            }
            QSlider::sub-page:horizontal {
                background: #0066cc;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self._he_so_slider)

        # Min/Max labels
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("50%"))
        slider_layout.addStretch()
        slider_layout.addWidget(QLabel("100%"))
        layout.addLayout(slider_layout)

        # Preview price
        self._preview_label = QLabel("Giá combo dự kiến: 0 đ")
        self._preview_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._preview_label)

        layout.addStretch()

        # Connect slider change
        self._he_so_slider.valueChanged.connect(self._on_slider_changed)

        return page

    def _create_step3(self) -> QWizardPage:
        """Create step 3: Preview and confirm."""
        page = QWizardPage()
        page.setTitle("Bước 3: Xác nhận tạo combo")
        page.setSubTitle("Kiểm tra thông tin combo trước khi tạo")

        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        # Combo summary
        summary_group = QGroupBox("Thông tin combo")
        summary_group.setStyleSheet("""
            QGroupBox {
                background-color: #f5f5f7;
                border-radius: 8px;
                padding: 16px;
                font-weight: 600;
            }
        """)
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setSpacing(8)

        self._summary_name = QLabel("Tên combo: ")
        summary_layout.addWidget(self._summary_name)

        self._summary_items = QLabel("Phụ kiện: ")
        summary_layout.addWidget(self._summary_items)

        self._summary_discount = QLabel("Hệ số giảm: ")
        summary_layout.addWidget(self._summary_discount)

        layout.addWidget(summary_group)

        # Price breakdown
        price_group = QGroupBox("Chi tiết giá")
        price_group.setStyleSheet("""
            QGroupBox {
                background-color: #f5f5f7;
                border-radius: 8px;
                padding: 16px;
                font-weight: 600;
            }
        """)
        price_layout = QVBoxLayout(price_group)
        price_layout.setSpacing(8)

        self._price_gia_goc = QLabel("Giá gốc: ")
        price_layout.addWidget(self._price_gia_goc)

        self._price_gia_combo = QLabel("Giá combo: ")
        self._price_gia_combo.setStyleSheet("color: #34c759;")
        price_layout.addWidget(self._price_gia_combo)

        self._price_tiet_kiem = QLabel("Tiết kiệm: ")
        self._price_tiet_kiem.setStyleSheet("color: #ff3b30;")
        price_layout.addWidget(self._price_tiet_kiem)

        layout.addWidget(price_group)

        layout.addStretch()

        return page

    def _on_selection_changed(self):
        """Handle accessory selection change."""
        selected = self._accessory_list.selectedItems()
        count = len(selected)
        self._selected_count_label.setText(f"Đã chọn: {count} phụ kiện (cần ít nhất 2)")

        # Validate
        if count < 2:
            self._selected_count_label.setStyleSheet("color: #ff3b30; font-size: 13px;")
        else:
            self._selected_count_label.setStyleSheet("color: #34c759; font-size: 13px;")

    def _on_slider_changed(self, value: int):
        """Handle slider value change."""
        self._he_so_giam = value / 100.0
        discount_pct = int((1 - self._he_so_giam) * 100)
        self._discount_label.setText(f"Giảm {discount_pct}%")
        self._update_preview()

    def _update_preview(self):
        """Update price preview on step 2."""
        selected = self._accessory_list.selectedItems()
        total = 0
        for item in selected:
            pk_id = item.data(Qt.ItemDataRole.UserRole)
            pk = self._pk_service.get_by_id(pk_id)
            if pk:
                total += pk.gia_ban

        gia_combo = int(total * self._he_so_giam)
        self._preview_label.setText(f"Giá combo dự kiến: {format_money(gia_combo)}")

    def validateCurrentPage(self) -> bool:
        """Validate current page before proceeding."""
        if self.currentId() == 1:
            # Step 1: Validate name and selection
            ten_combo = self._ten_combo_input.text().strip()
            if len(ten_combo) < 2:
                QMessageBox.warning(self, "Lỗi", "Tên combo phải có ít nhất 2 ký tự")
                return False

            selected = self._accessory_list.selectedItems()
            if len(selected) < 2:
                QMessageBox.warning(self, "Lỗi", "Phải chọn ít nhất 2 phụ kiện")
                return False

            self._ten_combo = ten_combo
            self._selected_items = []
            for item in selected:
                pk_id = item.data(Qt.ItemDataRole.UserRole)
                self._selected_items.append((pk_id, 1))  # Default quantity 1

        elif self.currentId() == 2:
            # Step 2: Update step 3 summary
            self._update_summary()

        return True

    def _update_summary(self):
        """Update step 3 summary."""
        self._summary_name.setText(f"Tên combo: {self._ten_combo}")
        self._summary_items.setText(f"Phụ kiện: {len(self._selected_items)} sản phẩm")
        self._summary_discount.setText(f"Hệ số giảm: {int(self._he_so_giam * 100)}%")

        # Calculate prices
        gia_goc = 0
        items_text = []
        for pk_id, so_luong in self._selected_items:
            pk = self._pk_service.get_by_id(pk_id)
            if pk:
                gia_goc += pk.gia_ban * so_luong
                items_text.append(f"- {pk.ten_pk} x{so_luong}: {format_money(pk.gia_ban * so_luong)}")

        gia_combo = int(gia_goc * self._he_so_giam)
        tien_tiet_kiem = gia_goc - gia_combo

        self._price_gia_goc.setText(f"Giá gốc: {format_money(gia_goc)}")
        self._price_gia_combo.setText(f"Giá combo: {format_money(gia_combo)}")
        self._price_tiet_kiem.setText(f"Tiết kiệm: {format_money(tien_tiet_kiem)}")
        self._summary_items.setText(f"Phụ kiện ({len(self._selected_items)}):\n" + "\n".join(items_text))

    def get_combo_data(self) -> ComboCreateData:
        """Get the combo data from wizard."""
        items = [ComboItemData(phu_kien_id=pk_id, so_luong=so_luong) for pk_id, so_luong in self._selected_items]
        return ComboCreateData(
            ten_combo=self._ten_combo,
            items=items,
            he_so_giam=self._he_so_giam,
            created_by=self._session.user_id if self._session else None,
        )


class ComboManagerScreen(QWidget):
    """Combo manager screen - S-PK-03.

    Signals:
        combo_created: New combo was created.
    """

    combo_created = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize combo manager screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._combo_service = ComboService(db_conn, session)

        self._current_page = 1
        self._total_pages = 1

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Quản lý combo phụ kiện")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Create combo button
        self._create_btn = QPushButton("🎁 Tạo combo mới")
        self._create_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e63329;
            }
        """)
        self._create_btn.clicked.connect(self._on_create_combo)
        header_layout.addWidget(self._create_btn)

        layout.addLayout(header_layout)

        # Search bar
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Tìm kiếm combo...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        self._search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self._search_input, stretch=1)

        self._search_btn = QPushButton("Tìm kiếm")
        self._search_btn.setStyleSheet("""
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
        self._search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(self._search_btn)

        layout.addLayout(search_layout)

        # Combo list (using scroll area with cards)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                background-color: white;
            }
        """)

        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setSpacing(12)
        self._cards_layout.addStretch()

        self._scroll_area.setWidget(self._cards_widget)
        layout.addWidget(self._scroll_area)

        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()

        self._prev_btn = QPushButton("◀ Trước")
        self._prev_btn.setStyleSheet("""
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
        self._prev_btn.clicked.connect(self._on_prev_page)
        pagination_layout.addWidget(self._prev_btn)

        self._page_label = QLabel("Trang 1 / 1")
        self._page_label.setStyleSheet("font-size: 14px; color: #86868b; padding: 0 16px;")
        pagination_layout.addWidget(self._page_label)

        self._next_btn = QPushButton("Sau ▶")
        self._next_btn.setStyleSheet(self._prev_btn.styleSheet())
        self._next_btn.clicked.connect(self._on_next_page)
        pagination_layout.addWidget(self._next_btn)

        self._total_label = QLabel("Tổng: 0 combo")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)

        layout.addLayout(pagination_layout)

    def _load_data(self):
        """Load combo data."""
        keyword = self._search_input.text().strip() if self._search_input.text().strip() else None

        try:
            result = self._combo_service.search(
                keyword=keyword,
                page=self._current_page,
                page_size=PAGE_SIZE,
            )

            self._total_pages = result.total_pages

            self._populate_cards(result.items)

            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {result.total} combo")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_cards(self, items: List[ComboDetail]):
        """Populate combo cards.

        Args:
            items: List of ComboDetail entities.
        """
        # Clear existing cards (keep the stretch)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not items:
            empty_label = QLabel("Chưa có combo nào")
            empty_label.setStyleSheet("color: #86868b; font-size: 14px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._cards_layout.insertWidget(0, empty_label)
            return

        for combo in items:
            card = ComboCardWidget(combo)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

    def _on_search(self):
        """Handle search button click."""
        self._current_page = 1
        self._load_data()

    def _on_prev_page(self):
        """Go to previous page."""
        if self._current_page > 1:
            self._current_page -= 1
            self._load_data()

    def _on_next_page(self):
        """Go to next page."""
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._load_data()

    def _on_create_combo(self):
        """Handle create combo button click."""
        wizard = ComboWizard(self._db_conn, self._session, self)
        if wizard.exec() == QDialog.DialogCode.Accepted:
            try:
                combo_data = wizard.get_combo_data()
                self._combo_service.create(combo_data)
                QMessageBox.information(self, "Thành công", "Đã tạo combo mới!")
                self._load_data()
                self.combo_created.emit()
            except ValidationError as e:
                QMessageBox.warning(self, "Lỗi validation", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể tạo combo: {str(e)}")

    def refresh(self):
        """Refresh the data."""
        self._load_data()
