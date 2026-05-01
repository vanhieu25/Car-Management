"""Revenue report screen - S-BC-01 - Revenue report with period grouping.

Features:
- Date range filter (from_date, to_date)
- Group by: Ngày / Tháng / Quý / Năm
- Employee filter (nhan_vien_id)
- Vehicle line filter (dong_xe)
- Column chart showing revenue by period
- Table: Period, Số HĐ, Doanh thu, % growth
- Export to Excel

References:
- BR-BC-01: Revenue report by period
- RP-01: Revenue report
"""

from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QDateEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen

from app.application.services.bao_cao_service import BaoCaoService
from app.application.services.nhan_vien_service import NhanVienService
from app.application.services.session import CurrentSession
from app.infrastructure.exporters.excel_exporter import ExcelExporter


class ColumnChartWidget(QWidget):
    """Simple column chart widget for revenue by period."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # List of (period_label, value)
        self.setMinimumHeight(250)

    def set_data(self, data):
        """Set chart data.

        Args:
            data: List of (period_label, value) tuples.
        """
        self._data = data
        self.update()

    def paintEvent(self, event):
        """Paint the column chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._data:
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Không có dữ liệu")
            return

        # Chart area with margins
        margin_left = 60
        margin_right = 20
        margin_top = 20
        margin_bottom = 50
        chart_rect = self.rect().adjusted(margin_left, margin_top, -margin_right, -margin_bottom)

        # Find max value for scaling
        values = [v for _, v in self._data]
        max_val = max(values) if values else 1
        if max_val == 0:
            max_val = 1

        min_val = 0
        range_val = max_val - min_val
        if range_val == 0:
            range_val = 1

        # Draw axes
        painter.setPen(QPen(QColor("#d2d2d7"), 1))
        painter.drawLine(chart_rect.left(), chart_rect.top(), chart_rect.left(), chart_rect.bottom())
        painter.drawLine(chart_rect.left(), chart_rect.bottom(), chart_rect.right(), chart_rect.bottom())

        # Draw horizontal grid lines and Y-axis labels
        grid_count = 4
        painter.setPen(QPen(QColor("#e5e5ea"), 1))
        for i in range(grid_count + 1):
            y_ratio = i / grid_count
            y = chart_rect.bottom() - int(chart_rect.height() * y_ratio)

            # Grid line
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)

            # Y-axis label
            val = int(min_val + range_val * y_ratio)
            label = f"{val // 1000000}M" if val >= 1000000 else f"{val // 1000}K" if val >= 1000 else str(val)
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(chart_rect.left() - 55, y + 5, label)
            painter.setPen(QPen(QColor("#e5e5ea"), 1))

        # Draw columns
        bar_count = len(self._data)
        if bar_count == 0:
            return

        bar_width = max(20, min(60, (chart_rect.width() - 20) // bar_count - 10))
        total_width = bar_count * (bar_width + 6) - 6
        start_x = chart_rect.left() + max(0, (chart_rect.width() - total_width) // 2)

        for i, (label, value) in enumerate(self._data):
            x = start_x + i * (bar_width + 6)
            bar_height = int(chart_rect.height() * (value - min_val) / range_val)
            if bar_height < 2:
                bar_height = 2

            # Draw bar
            painter.fillRect(
                x,
                chart_rect.bottom() - bar_height,
                bar_width,
                bar_height,
                QColor("#0066cc")
            )

            # X-axis label (show rotated if many)
            if bar_count <= 12:
                painter.setPen(QPen(QColor("#86868b")))
                painter.drawText(
                    x + bar_width // 2 - 15,
                    chart_rect.bottom() + 18,
                    label
                )


class RevenueReportScreen(QWidget):
    """Revenue report screen - S-BC-01.

    Signals:
        view_contract_clicked(contract_id: int): User wants to view a contract.
    """

    view_contract_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize revenue report screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bao_cao_service = BaoCaoService(db_conn)
        self._nhan_vien_service = NhanVienService(db_conn)

        self._current_data = []  # Store current breakdown data
        self._previous_data = []  # Store previous period for growth calc

        self._setup_ui()
        self._load_filter_options()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Báo cáo doanh thu")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button
        self._refresh_btn = QPushButton("🔄 Làm mới")
        self._refresh_btn.setStyleSheet("""
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
        self._refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(self._refresh_btn)

        # Export button
        self._export_btn = QPushButton("📥 Xuất Excel")
        self._export_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._export_btn.clicked.connect(self._export_to_excel)
        header_layout.addWidget(self._export_btn)

        layout.addLayout(header_layout)

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

        # Date range - from
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
        self._date_from.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._date_from)

        # Date range - to
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
        self._date_to.dateChanged.connect(self._on_filter_changed)
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
        self._group_by_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._group_by_combo)

        # Employee filter
        filter_layout.addWidget(QLabel("Nhân viên:"))
        self._employee_combo = QComboBox()
        self._employee_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 150px;
                background: white;
            }
        """)
        self._employee_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._employee_combo)

        # Vehicle line filter
        filter_layout.addWidget(QLabel("Dòng xe:"))
        self._dong_xe_combo = QComboBox()
        self._dong_xe_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 120px;
                background: white;
            }
        """)
        self._dong_xe_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._dong_xe_combo)

        filter_layout.addStretch()

        layout.addWidget(filter_group)

        # Summary KPIs row
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self._kpi_revenue = self._create_kpi_card("Tổng doanh thu", "0 đ", "#34c759")
        self._kpi_contracts = self._create_kpi_card("Tổng HĐ", "0", "#007aff")
        self._kpi_growth = self._create_kpi_card("Tăng trưởng", "—", "#5856d6")

        kpi_layout.addWidget(self._kpi_revenue)
        kpi_layout.addWidget(self._kpi_contracts)
        kpi_layout.addWidget(self._kpi_growth)
        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)

        # Chart
        chart_group = QGroupBox("Doanh thu theo kỳ")
        chart_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #d2d2d7;
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
        chart_layout = QVBoxLayout(chart_group)

        self._chart = ColumnChartWidget()
        chart_layout.addWidget(self._chart)

        layout.addWidget(chart_group)

        # Data table
        table_label = QLabel("Chi tiết theo kỳ")
        table_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Kỳ", "Số HĐ", "Doanh thu", "Tỷ trọng (%)", "Tăng trưởng (%)"
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

        self.setLayout(layout)

    def _create_kpi_card(self, title: str, value: str, color: str) -> QGroupBox:
        """Create a KPI card widget."""
        card = QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 12px 16px;
                background-color: #fafafa;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 16, 12, 12)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; color: #86868b;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: 600; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        return card

    def _load_filter_options(self):
        """Load employee and vehicle line filter options."""
        # Load employees
        self._employee_combo.addItem("Tất cả", None)
        try:
            nvs = self._nhan_vien_service.get_all()
            for nv in nvs:
                self._employee_combo.addItem(nv.ho_ten, nv.id)
        except Exception:
            pass

        # Load vehicle lines
        self._dong_xe_combo.addItem("Tất cả", None)
        try:
            cursor = self._db_conn.execute(
                "SELECT DISTINCT dong_xe FROM xe WHERE dong_xe IS NOT NULL ORDER BY dong_xe"
            )
            for row in cursor.fetchall():
                self._dong_xe_combo.addItem(row[0], row[0])
        except Exception:
            pass

    def _on_filter_changed(self):
        """Handle filter change."""
        self._load_data()

    def _get_filter_params(self) -> dict:
        """Get current filter parameters."""
        params = {}

        params["from_date"] = self._date_from.date().toString("yyyy-MM-dd")
        params["to_date"] = self._date_to.date().toString("yyyy-MM-dd")

        group_by_map = {
            "Ngày": "day",
            "Tháng": "month",
            "Quý": "quarter",
            "Năm": "year",
        }
        params["group_by"] = group_by_map.get(self._group_by_combo.currentText(), "month")

        params["nhan_vien_id"] = self._employee_combo.currentData()

        params["dong_xe"] = self._dong_xe_combo.currentData()

        return params

    def _load_data(self):
        """Load revenue report data."""
        params = self._get_filter_params()

        try:
            result = self._bao_cao_service.revenue(
                from_date=params["from_date"],
                to_date=params["to_date"],
                group_by=params["group_by"],
                nhan_vien_id=params.get("nhan_vien_id"),
                dong_xe=params.get("dong_xe"),
            )

            breakdown = result.get("breakdown", [])
            total_revenue = result.get("total_revenue", 0)
            total_contracts = result.get("total_contracts", 0)

            # Calculate growth (compare first and last period)
            growth = None
            if len(breakdown) >= 2:
                first = breakdown[0]["doanh_thu"]
                last = breakdown[-1]["doanh_thu"]
                if first > 0:
                    growth = (last - first) / first * 100

            # Update KPI cards
            self._update_kpi_value(self._kpi_revenue, f"{total_revenue:,} đ".replace(",", "."))
            self._update_kpi_value(self._kpi_contracts, str(total_contracts))

            if growth is not None:
                growth_str = f"{growth:+.1f}%"
                self._update_kpi_value(self._kpi_growth, growth_str)
            else:
                self._update_kpi_value(self._kpi_growth, "—")

            # Update chart
            chart_data = [(item["period"], item["doanh_thu"]) for item in breakdown]
            self._chart.set_data(chart_data)

            # Calculate growth per row
            self._current_data = breakdown
            self._calculate_growth()

            # Update table
            self._populate_table()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải báo cáo: {str(e)}")

    def _calculate_growth(self):
        """Calculate growth percentage for each period vs previous."""
        for i, item in enumerate(self._current_data):
            if i == 0:
                item["growth"] = None
            else:
                prev = self._current_data[i - 1]["doanh_thu"]
                curr = item["doanh_thu"]
                if prev > 0:
                    item["growth"] = (curr - prev) / prev * 100
                else:
                    item["growth"] = None

    def _update_kpi_value(self, card: QGroupBox, value: str):
        """Update KPI card value label."""
        # Find the value label (second child)
        layout = card.layout()
        if layout and layout.count() >= 2:
            widget = layout.itemAt(1).widget()
            if isinstance(widget, QLabel):
                widget.setText(value)

    def _populate_table(self):
        """Populate table with revenue data."""
        self._table.setRowCount(len(self._current_data))

        for row, item in enumerate(self._current_data):
            # Kỳ
            period_label = item.get("period", "")
            self._table.setItem(row, 0, QTableWidgetItem(period_label))

            # Số HĐ
            so_hd = item.get("so_hop_dong", 0)
            item_hd = QTableWidgetItem(str(so_hd))
            item_hd.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 1, item_hd)

            # Doanh thu
            doanh_thu = item.get("doanh_thu", 0)
            dt_text = f"{doanh_thu:,} đ".replace(",", ".")
            item_dt = QTableWidgetItem(dt_text)
            item_dt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, item_dt)

            # Tỷ trọng
            ty_le = item.get("ty_le", 0)
            tl_text = f"{ty_le:.1f}%"
            item_tl = QTableWidgetItem(tl_text)
            item_tl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, item_tl)

            # Tăng trưởng
            growth = item.get("growth")
            if growth is not None:
                growth_text = f"{growth:+.1f}%"
                item_g = QTableWidgetItem(growth_text)
                # Color positive green, negative red
                if growth > 0:
                    item_g.setForeground(QColor("#34c759"))
                elif growth < 0:
                    item_g.setForeground(QColor("#ff3b30"))
            else:
                item_g = QTableWidgetItem("—")
            item_g.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 4, item_g)

        # Set column widths
        self._table.setColumnWidth(1, 80)
        self._table.setColumnWidth(2, 130)
        self._table.setColumnWidth(3, 110)
        self._table.setColumnWidth(4, 110)

    def _export_to_excel(self):
        """Export report to Excel."""
        if not self._current_data:
            QMessageBox.information(self, "Thông báo", "Không có dữ liệu để xuất.")
            return

        try:
            from datetime import datetime

            params = self._get_filter_params()

            # Prepare sheet config
            sheet_config = {
                "name": "Báo cáo doanh thu",
                "title": f"Báo cáo doanh thu từ {params['from_date']} đến {params['to_date']}",
                "columns": [
                    {"header": "Kỳ", "key": "period", "width": 15},
                    {"header": "Số HĐ", "key": "so_hop_dong", "width": 12, "format": "number"},
                    {"header": "Doanh thu", "key": "doanh_thu", "width": 18, "format": "money"},
                    {"header": "Tỷ trọng (%)", "key": "ty_le", "width": 15, "format": "percent"},
                    {"header": "Tăng trưởng (%)", "key": "growth", "width": 15, "format": "percent"},
                ],
            }

            # Prepare data (add growth value)
            export_data = []
            for item in self._current_data:
                row = dict(item)
                if item.get("growth") is not None:
                    row["growth"] = item["growth"] / 100  # Will be formatted as percent by exporter
                else:
                    row["growth"] = None
                export_data.append(row)

            # Show save dialog
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"bao_cao_doanh_thu_{timestamp}.xlsx"

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Lưu báo cáo Excel",
                default_name,
                "Excel Files (*.xlsx)"
            )

            if not file_path:
                return

            exporter = ExcelExporter()
            result_path = exporter.export_report(export_data, sheet_config, file_path)

            QMessageBox.information(
                self,
                "Thành công",
                f"Đã xuất báo cáo thành công!\n{result_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất Excel: {str(e)}")

    def refresh(self):
        """Refresh the data."""
        self._load_data()