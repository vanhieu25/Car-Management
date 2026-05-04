"""ReportsHubScreen - Central hub for all report types with tabs.

S-BC-HUB: Reports Hub with 5 tabs:
- Tab "Doanh thu" → RevenueReportScreen (existing)
- Tab "Khuyến mãi" → PromotionReportWidget
- Tab "Bảo dưỡng" → MaintenanceReportWidget
- Tab "Nhân viên" → EmployeeKPIReportScreen (existing)
- Tab "Khách hàng mới" → NewCustomersReportWidget

Each tab has its own filter controls and data table.
Follows same styling as RevenueReportScreen.

References:
- BR-BC-01..05: Revenue, vehicle, customer, warranty, employee reports
- RP-01..05: Report types
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QDateEdit, QFileDialog, QTabWidget, QComboBox,
    QGridLayout
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen

from app.application.services.bao_cao_service import BaoCaoService
from app.infrastructure.exporters.excel_exporter import ExcelExporter


class RevenueReportWidget(QWidget):
    """Embedded revenue report widget for the hub tab."""

    def __init__(self, db_conn, session, parent=None):
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bao_cao_service = BaoCaoService(db_conn)
        self._current_data = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filter bar
        filter_group = QGroupBox()
        filter_group.setStyleSheet("""
            QGroupBox {
                background-color: #f5f5f7;
                border-radius: 8px;
                padding: 12px 16px;
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
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(8, 16, 8, 8)

        # Date range
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-3))
        self._date_from.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_from.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self._date_from)

        filter_layout.addWidget(QLabel("Đến ngày:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_to.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self._date_to)

        # Group by
        filter_layout.addWidget(QLabel("Nhóm theo:"))
        self._group_by_combo = QComboBox()
        self._group_by_combo.addItems(["Ngày", "Tháng", "Quý", "Năm"])
        self._group_by_combo.setCurrentText("Tháng")
        self._group_by_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 100px;
                background: white;
            }
        """)
        self._group_by_combo.currentTextChanged.connect(self._load_data)
        filter_layout.addWidget(self._group_by_combo)

        filter_layout.addStretch()

        # Refresh button
        self._refresh_btn = QPushButton("🔄 Làm mới")
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(self._refresh_btn)

        layout.addWidget(filter_group)

        # KPI cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self._kpi_revenue = self._create_kpi_card("Tổng doanh thu", "0 đ", "#34c759")
        self._kpi_contracts = self._create_kpi_card("Tổng HĐ", "0", "#007aff")

        kpi_layout.addWidget(self._kpi_revenue)
        kpi_layout.addWidget(self._kpi_contracts)
        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Kỳ", "Số HĐ", "Doanh thu", "Tỷ trọng (%)"])

        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 10px 8px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #0066cc;
                color: white;
            }
        """)

        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)

        layout.addWidget(self._table)

    def _create_kpi_card(self, title: str, value: str, color: str) -> QGroupBox:
        card = QGroupBox()
        card.setMinimumWidth(160)
        card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px 20px;
                background-color: #fafafa;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 20, 16, 16)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #86868b;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 26px; font-weight: 600; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        return card

    def _update_kpi_value(self, card: QGroupBox, value: str):
        layout = card.layout()
        if layout and layout.count() >= 2:
            widget = layout.itemAt(1).widget()
            if isinstance(widget, QLabel):
                widget.setText(value)

    def _load_data(self):
        from_date = self._date_from.date().toString("yyyy-MM-dd")
        to_date = self._date_to.date().toString("yyyy-MM-dd")

        group_by_map = {"Ngày": "day", "Tháng": "month", "Quý": "quarter", "Năm": "year"}
        group_by = group_by_map.get(self._group_by_combo.currentText(), "month")

        try:
            result = self._bao_cao_service.revenue(
                from_date=from_date, to_date=to_date, group_by=group_by
            )

            breakdown = result.get("breakdown", [])
            total_revenue = result.get("total_revenue", 0)
            total_contracts = result.get("total_contracts", 0)

            self._update_kpi_value(self._kpi_revenue, f"{total_revenue:,} đ".replace(",", "."))
            self._update_kpi_value(self._kpi_contracts, str(total_contracts))

            self._current_data = breakdown
            self._populate_table()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải báo cáo: {str(e)}")

    def _populate_table(self):
        self._table.setRowCount(len(self._current_data))

        for row, item in enumerate(self._current_data):
            period = item.get("period", "")
            so_hd = item.get("so_hop_dong", 0)
            doanh_thu = item.get("doanh_thu", 0)
            ty_le = item.get("ty_le", 0)

            self._table.setItem(row, 0, QTableWidgetItem(period))

            item_hd = QTableWidgetItem(str(so_hd))
            item_hd.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 1, item_hd)

            item_dt = QTableWidgetItem(f"{doanh_thu:,} đ".replace(",", "."))
            item_dt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, item_dt)

            item_tl = QTableWidgetItem(f"{ty_le:.1f}%")
            item_tl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, item_tl)

        self._table.setColumnWidth(1, 80)
        self._table.setColumnWidth(2, 130)
        self._table.setColumnWidth(3, 110)

    def refresh(self):
        self._load_data()


class PromotionReportWidget(QWidget):
    """Promotion effectiveness report widget."""

    def __init__(self, db_conn, session, parent=None):
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bao_cao_service = BaoCaoService(db_conn)
        self._current_data = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filter bar
        filter_group = QGroupBox()
        filter_group.setStyleSheet("""
            QGroupBox {
                background-color: #f5f5f7;
                border-radius: 8px;
                padding: 12px 16px;
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
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(8, 16, 8, 8)

        filter_layout.addWidget(QLabel("Từ ngày:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-3))
        self._date_from.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_from.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self._date_from)

        filter_layout.addWidget(QLabel("Đến ngày:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_to.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self._date_to)

        filter_layout.addStretch()

        self._refresh_btn = QPushButton("🔄 Làm mới")
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(self._refresh_btn)

        layout.addWidget(filter_group)

        # KPI cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self._kpi_applied = self._create_kpi_card("Tổng áp dụng", "0", "#007aff")
        self._kpi_discount = self._create_kpi_card("Tổng giảm giá", "0 đ", "#34c759")

        kpi_layout.addWidget(self._kpi_applied)
        kpi_layout.addWidget(self._kpi_discount)
        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)

        # Table
        table_label = QLabel("Chi tiết khuyến mãi")
        table_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f; margin-top: 8px;")
        layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Tên khuyến mãi", "Loại", "Giá trị", "Số HĐ áp dụng", "Tổng giảm", "Trạng thái"
        ])

        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 10px 8px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #0066cc;
                color: white;
            }
        """)

        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)

        layout.addWidget(self._table)

    def _create_kpi_card(self, title: str, value: str, color: str) -> QGroupBox:
        card = QGroupBox()
        card.setMinimumWidth(160)
        card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px 20px;
                background-color: #fafafa;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 20, 16, 16)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #86868b;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 26px; font-weight: 600; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        return card

    def _update_kpi_value(self, card: QGroupBox, value: str):
        layout = card.layout()
        if layout and layout.count() >= 2:
            widget = layout.itemAt(1).widget()
            if isinstance(widget, QLabel):
                widget.setText(value)

    def _load_data(self):
        from_date = self._date_from.date().toString("yyyy-MM-dd")
        to_date = self._date_to.date().toString("yyyy-MM-dd")

        try:
            result = self._bao_cao_service.promotion_report(from_date=from_date, to_date=to_date)

            promotions = result.get("promotions", [])
            total_applied = result.get("total_applied", 0)
            total_discount = result.get("total_discount", 0)

            self._update_kpi_value(self._kpi_applied, str(total_applied))
            self._update_kpi_value(self._kpi_discount, f"{total_discount:,} đ".replace(",", "."))

            self._current_data = promotions
            self._populate_table()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải báo cáo: {str(e)}")

    def _populate_table(self):
        self._table.setRowCount(len(self._current_data))

        for row, item in enumerate(self._current_data):
            ten_km = item.get("ten_km", "")
            loai_km = item.get("loai_km", "")
            gia_tri = item.get("gia_tri", 0)
            kieu_gia_tri = item.get("kieu_gia_tri", "")
            so_hd = item.get("so_hop_dong", 0)
            tong_giam = item.get("tong_giam", 0)
            trang_thai = item.get("trang_thai", "")

            self._table.setItem(row, 0, QTableWidgetItem(ten_km))
            self._table.setItem(row, 1, QTableWidgetItem(loai_km))

            gia_tri_text = f"{gia_tri:,}%" if kieu_gia_tri == "percent" else f"{gia_tri:,} đ".replace(",", ".")
            item_gia = QTableWidgetItem(gia_tri_text)
            item_gia.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, item_gia)

            item_hd = QTableWidgetItem(str(so_hd))
            item_hd.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, item_hd)

            item_giam = QTableWidgetItem(f"{tong_giam:,} đ".replace(",", "."))
            item_giam.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 4, item_giam)

            # Status label
            trang_thai_label = "Hoạt động" if trang_thai == "active" else ("Hết hạn" if trang_thai == "expired" else trang_thai)
            item_status = QTableWidgetItem(trang_thai_label)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 5, item_status)

        self._table.setColumnWidth(2, 100)
        self._table.setColumnWidth(3, 110)
        self._table.setColumnWidth(4, 130)
        self._table.setColumnWidth(5, 100)

    def refresh(self):
        self._load_data()


class MaintenanceReportWidget(QWidget):
    """Maintenance statistics report widget."""

    def __init__(self, db_conn, session, parent=None):
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bao_cao_service = BaoCaoService(db_conn)
        self._current_data = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filter bar
        filter_group = QGroupBox()
        filter_group.setStyleSheet("""
            QGroupBox {
                background-color: #f5f5f7;
                border-radius: 8px;
                padding: 12px 16px;
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
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(8, 16, 8, 8)

        filter_layout.addWidget(QLabel("Từ ngày:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-3))
        self._date_from.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_from.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self._date_from)

        filter_layout.addWidget(QLabel("Đến ngày:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_to.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self._date_to)

        filter_layout.addWidget(QLabel("Nhóm theo:"))
        self._group_by_combo = QComboBox()
        self._group_by_combo.addItems(["Ngày", "Tháng", "Quý", "Năm"])
        self._group_by_combo.setCurrentText("Tháng")
        self._group_by_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 100px;
                background: white;
            }
        """)
        self._group_by_combo.currentTextChanged.connect(self._load_data)
        filter_layout.addWidget(self._group_by_combo)

        filter_layout.addStretch()

        self._refresh_btn = QPushButton("🔄 Làm mới")
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(self._refresh_btn)

        layout.addWidget(filter_group)

        # KPI cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self._kpi_count = self._create_kpi_card("Tổng lượt bảo dưỡng", "0", "#007aff")
        self._kpi_cost = self._create_kpi_card("Tổng chi phí", "0 đ", "#ff9500")
        self._kpi_completed = self._create_kpi_card("Đã hoàn thành", "0", "#34c759")

        kpi_layout.addWidget(self._kpi_count)
        kpi_layout.addWidget(self._kpi_cost)
        kpi_layout.addWidget(self._kpi_completed)
        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)

        # Table
        table_label = QLabel("Chi tiết bảo dưỡng theo kỳ")
        table_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f; margin-top: 8px;")
        layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Kỳ", "Số lượng", "Chi phí", "Hoàn thành", "Đã hủy"
        ])

        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 10px 8px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #0066cc;
                color: white;
            }
        """)

        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)

        layout.addWidget(self._table)

    def _create_kpi_card(self, title: str, value: str, color: str) -> QGroupBox:
        card = QGroupBox()
        card.setMinimumWidth(160)
        card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px 20px;
                background-color: #fafafa;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 20, 16, 16)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #86868b;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 26px; font-weight: 600; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        return card

    def _update_kpi_value(self, card: QGroupBox, value: str):
        layout = card.layout()
        if layout and layout.count() >= 2:
            widget = layout.itemAt(1).widget()
            if isinstance(widget, QLabel):
                widget.setText(value)

    def _load_data(self):
        from_date = self._date_from.date().toString("yyyy-MM-dd")
        to_date = self._date_to.date().toString("yyyy-MM-dd")

        group_by_map = {"Ngày": "day", "Tháng": "month", "Quý": "quarter", "Năm": "year"}
        group_by = group_by_map.get(self._group_by_combo.currentText(), "month")

        try:
            result = self._bao_cao_service.maintenance_report(
                from_date=from_date, to_date=to_date, group_by=group_by
            )

            breakdown = result.get("breakdown", [])
            total_count = result.get("total_count", 0)
            total_cost = result.get("total_cost", 0)
            completed = result.get("completed", 0)

            self._update_kpi_value(self._kpi_count, str(total_count))
            self._update_kpi_value(self._kpi_cost, f"{total_cost:,} đ".replace(",", "."))
            self._update_kpi_value(self._kpi_completed, str(completed))

            self._current_data = breakdown
            self._populate_table()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải báo cáo: {str(e)}")

    def _populate_table(self):
        self._table.setRowCount(len(self._current_data))

        for row, item in enumerate(self._current_data):
            period = item.get("period", "")
            so_luong = item.get("so_luong", 0)
            chi_phi = item.get("tong_chi_phi", 0)
            da_hoan_thanh = item.get("da_hoan_thanh", 0)
            da_huy = item.get("da_huy", 0)

            self._table.setItem(row, 0, QTableWidgetItem(period))

            item_sl = QTableWidgetItem(str(so_luong))
            item_sl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 1, item_sl)

            item_cp = QTableWidgetItem(f"{chi_phi:,} đ".replace(",", "."))
            item_cp.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, item_cp)

            item_ht = QTableWidgetItem(str(da_hoan_thanh))
            item_ht.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, item_ht)

            item_huy = QTableWidgetItem(str(da_huy))
            item_huy.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 4, item_huy)

        self._table.setColumnWidth(1, 100)
        self._table.setColumnWidth(2, 130)
        self._table.setColumnWidth(3, 110)
        self._table.setColumnWidth(4, 100)

    def refresh(self):
        self._load_data()


class NewCustomersReportWidget(QWidget):
    """New customer acquisition report widget."""

    def __init__(self, db_conn, session, parent=None):
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bao_cao_service = BaoCaoService(db_conn)
        self._current_data = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filter bar
        filter_group = QGroupBox()
        filter_group.setStyleSheet("""
            QGroupBox {
                background-color: #f5f5f7;
                border-radius: 8px;
                padding: 12px 16px;
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
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(8, 16, 8, 8)

        filter_layout.addWidget(QLabel("Từ ngày:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-3))
        self._date_from.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_from.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self._date_from)

        filter_layout.addWidget(QLabel("Đến ngày:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_to.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self._date_to)

        filter_layout.addStretch()

        self._refresh_btn = QPushButton("🔄 Làm mới")
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(self._refresh_btn)

        layout.addWidget(filter_group)

        # KPI cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self._kpi_new = self._create_kpi_card("Tổng khách hàng mới", "0", "#34c759")

        kpi_layout.addWidget(self._kpi_new)
        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)

        # Table
        table_label = QLabel("Danh sách khách hàng mới")
        table_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f; margin-top: 8px;")
        layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "ID", "Họ tên", "Số điện thoại", "Email", "Ngày tạo"
        ])

        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 10px 8px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #0066cc;
                color: white;
            }
        """)

        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)

        layout.addWidget(self._table)

    def _create_kpi_card(self, title: str, value: str, color: str) -> QGroupBox:
        card = QGroupBox()
        card.setMinimumWidth(160)
        card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px 20px;
                background-color: #fafafa;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 20, 16, 16)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #86868b;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 26px; font-weight: 600; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        return card

    def _update_kpi_value(self, card: QGroupBox, value: str):
        layout = card.layout()
        if layout and layout.count() >= 2:
            widget = layout.itemAt(1).widget()
            if isinstance(widget, QLabel):
                widget.setText(value)

    def _load_data(self):
        from_date = self._date_from.date().toString("yyyy-MM-dd")
        to_date = self._date_to.date().toString("yyyy-MM-dd")

        try:
            result = self._bao_cao_service.new_customers(from_date=from_date, to_date=to_date)

            customers = result.get("customers", [])
            total_new = result.get("total_new", 0)

            self._update_kpi_value(self._kpi_new, str(total_new))

            self._current_data = customers
            self._populate_table()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải báo cáo: {str(e)}")

    def _populate_table(self):
        self._table.setRowCount(len(self._current_data))

        for row, item in enumerate(self._current_data):
            customer_id = item.get("id", "")
            ho_ten = item.get("ho_ten", "")
            sdt = item.get("so_dien_thoai", "")
            email = item.get("email", "") or "—"
            created_at = item.get("created_at", "")

            item_id = QTableWidgetItem(str(customer_id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, item_id)

            self._table.setItem(row, 1, QTableWidgetItem(ho_ten))

            item_sdt = QTableWidgetItem(sdt)
            item_sdt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 2, item_sdt)

            item_email = QTableWidgetItem(email)
            item_email.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, item_email)

            item_date = QTableWidgetItem(str(created_at))
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 4, item_date)

        self._table.setColumnWidth(0, 60)
        self._table.setColumnWidth(2, 120)
        self._table.setColumnWidth(3, 180)
        self._table.setColumnWidth(4, 120)

    def refresh(self):
        self._load_data()


class ReportsHubScreen(QWidget):
    """Reports Hub - tabbed interface for all report types.

    S-BC-HUB: Central hub for:
    - Revenue Report (Doanh thu)
    - Promotion Report (Khuyến mãi)
    - Maintenance Report (Bảo dưỡng)
    - Employee KPI Report (Nhân viên)
    - New Customers Report (Khách hàng mới)
    """

    def __init__(self, db_conn, session, parent=None):
        """Initialize ReportsHubScreen.

        Args:
            db_conn: sqlite3 database connection.
            session: CurrentSession instance.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI with tabbed interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Báo cáo")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
                color: #86868b;
                background-color: #f5f5f7;
                border: 1px solid #d2d2d7;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                color: #1d1d1f;
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e5e5ea;
            }
        """)
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setMovable(True)

        # Tab 1: Doanh thu (Revenue)
        from app.presentation.screens.revenue_report_screen import RevenueReportScreen
        self._revenue_tab = RevenueReportScreen(self._db_conn, self._session)
        self._tab_widget.addTab(self._revenue_tab, "📊 Doanh thu")

        # Tab 2: Khuyến mãi (Promotion)
        self._promotion_tab = PromotionReportWidget(self._db_conn, self._session)
        self._tab_widget.addTab(self._promotion_tab, "🎁 Khuyến mãi")

        # Tab 3: Bảo dưỡng (Maintenance)
        self._maintenance_tab = MaintenanceReportWidget(self._db_conn, self._session)
        self._tab_widget.addTab(self._maintenance_tab, "🔧 Bảo dưỡng")

        # Tab 4: Nhân viên (Employee KPI)
        from app.presentation.screens.employee_kpi_report_screen import EmployeeKPIReportScreen
        self._employee_tab = EmployeeKPIReportScreen(self._db_conn, self._session)
        self._tab_widget.addTab(self._employee_tab, "👥 Nhân viên")

        # Tab 5: Khách hàng mới (New Customers)
        self._new_customers_tab = NewCustomersReportWidget(self._db_conn, self._session)
        self._tab_widget.addTab(self._new_customers_tab, "🆕 Khách hàng mới")

        layout.addWidget(self._tab_widget)

        self.setLayout(layout)

    def refresh(self):
        """Refresh the currently active tab."""
        current_widget = self._tab_widget.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()