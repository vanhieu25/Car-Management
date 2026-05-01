"""Employee KPI report screen - S-BC-03 - Employee performance KPI report.

Features:
- Month picker (YYYY-MM format)
- Comparison bar chart - employees side by side
- Table: Mã NV, Tên NV, Số HĐ mới, Số HĐ đã thanh toán,
  Tỷ lệ chốt %, Doanh thu
- Color coding: highlight top performer green, bottom performer yellow/red
- Export to Excel

References:
- BR-CALC-05: Employee KPI formula
- BR-CALC-06: Conversion rate formula
- RP-03: Employee KPI report
"""

from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QFont

from app.application.services.bao_cao_service import BaoCaoService
from app.infrastructure.exporters.excel_exporter import ExcelExporter


class ComparisonBarChartWidget(QWidget):
    """Comparison bar chart for employee KPIs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # List of (label, revenue_value) tuples
        self.setMinimumHeight(280)

    def set_data(self, data):
        """Set chart data.

        Args:
            data: List of (label, value) tuples.
        """
        self._data = data
        self.update()

    def paintEvent(self, event):
        """Paint the comparison bar chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._data:
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Không có dữ liệu")
            return

        # Chart area with margins
        margin_left = 100
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
            painter.drawText(chart_rect.left() - 8, y + 5, label)
            painter.setPen(QPen(QColor("#e5e5ea"), 1))

        # Draw bars
        bar_count = len(self._data)
        if bar_count == 0:
            return

        bar_width = max(20, min(50, (chart_rect.width() - 20) // bar_count - 10))
        total_width = bar_count * (bar_width + 8) - 8
        start_x = chart_rect.left() + max(0, (chart_rect.width() - total_width) // 2)

        for i, (label, value) in enumerate(self._data):
            x = start_x + i * (bar_width + 8)

            # Calculate bar height
            bar_height = int(chart_rect.height() * (value - min_val) / range_val)
            if bar_height < 2:
                bar_height = 2

            # Determine color (first = green, last = red, others = blue)
            if i == 0:
                bar_color = QColor("#34c759")  # Top performer - green
            elif i == bar_count - 1:
                bar_color = QColor("#ff3b30")  # Bottom performer - red
            else:
                bar_color = QColor("#007aff")  # Default blue

            # Draw bar
            painter.fillRect(
                x,
                chart_rect.bottom() - bar_height,
                bar_width,
                bar_height,
                bar_color
            )

            # X-axis label
            painter.setPen(QPen(QColor("#86868b")))
            # Truncate label
            display_label = label[:10] + "..." if len(label) > 10 else label
            painter.drawText(
                x + bar_width // 2 - 20,
                chart_rect.bottom() + 18,
                display_label
            )


class EmployeeKPIReportScreen(QWidget):
    """Employee KPI report screen - S-BC-03."""

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize employee KPI report screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bao_cao_service = BaoCaoService(db_conn)

        self._current_data = []

        self._setup_ui()
        self._load_month_options()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Báo cáo KPI nhân viên")
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

        # Month picker
        filter_layout.addWidget(QLabel("Tháng:"))
        self._month_combo = QComboBox()
        self._month_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 120px;
                background: white;
            }
        """)
        self._month_combo.currentTextChanged.connect(self._load_data)
        filter_layout.addWidget(self._month_combo)

        filter_layout.addStretch()

        layout.addWidget(filter_group)

        # Summary KPIs
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self._kpi_revenue = self._create_kpi_card("Tổng doanh thu", "0 đ", "#34c759")
        self._kpi_contracts = self._create_kpi_card("Tổng HĐ mới", "0", "#007aff")
        self._kpi_top_performer = self._create_kpi_card("Nhân viên xuất sắc", "—", "#34c759")
        self._kpi_avg_rate = self._create_kpi_card("Tỷ lệ chốt TB", "—", "#5856d6")

        kpi_layout.addWidget(self._kpi_revenue)
        kpi_layout.addWidget(self._kpi_contracts)
        kpi_layout.addWidget(self._kpi_top_performer)
        kpi_layout.addWidget(self._kpi_avg_rate)
        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)

        # Chart
        chart_group = QGroupBox("So sánh doanh thu nhân viên")
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

        self._chart = ComparisonBarChartWidget()
        chart_layout.addWidget(self._chart)

        layout.addWidget(chart_group)

        # Data table
        table_label = QLabel("Chi tiết KPI nhân viên")
        table_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Mã NV", "Tên nhân viên", "Số HĐ mới", "HĐ đã thanh toán",
            "HĐ giao thành công", "Tỷ lệ chốt (%)", "Doanh thu"
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

    def _load_month_options(self):
        """Load available months (last 12 months) for selection."""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        self._month_combo.clear()

        now = datetime.now()
        for i in range(12):
            d = now - relativedelta(months=i)
            month_key = d.strftime("%Y-%m")
            month_label = d.strftime("%m/%Y")
            self._month_combo.addItem(month_label, month_key)

    def _load_data(self):
        """Load employee KPI data."""
        month = self._month_combo.currentData()
        if not month:
            return

        try:
            result = self._bao_cao_service.kpi_nv(month)

            # Calculate totals
            total_revenue = sum(item.get("doanh_thu", 0) for item in result)
            total_contracts = sum(item.get("so_hop_dong_moi_tao", 0) for item in result)

            # Find top performer
            top_performer = None
            if result:
                top_performer = max(result, key=lambda x: x.get("doanh_thu", 0))

            # Calculate average conversion rate
            avg_rate = 0
            rates = [item.get("ti_le_chot", 0) for item in result if item.get("ti_le_chot", 0) > 0]
            if rates:
                avg_rate = sum(rates) / len(rates)

            # Update KPI cards
            self._update_kpi_value(self._kpi_revenue, f"{total_revenue:,} đ".replace(",", "."))
            self._update_kpi_value(self._kpi_contracts, str(total_contracts))
            self._update_kpi_value(
                self._kpi_top_performer,
                top_performer.get("ho_ten", "—") if top_performer else "—"
            )
            self._update_kpi_value(self._kpi_avg_rate, f"{avg_rate:.1f}%")

            self._current_data = result

            # Update chart
            chart_data = [
                (item.get("ho_ten", "")[:15], item.get("doanh_thu", 0))
                for item in result
            ]
            self._chart.set_data(chart_data)

            # Update table
            self._populate_table()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải báo cáo: {str(e)}")

    def _update_kpi_value(self, card: QGroupBox, value: str):
        """Update KPI card value label."""
        layout = card.layout()
        if layout and layout.count() >= 2:
            widget = layout.itemAt(1).widget()
            if isinstance(widget, QLabel):
                widget.setText(value)

    def _populate_table(self):
        """Populate table with employee KPI data."""
        self._table.setRowCount(len(self._current_data))

        # Find max and min for highlighting
        max_revenue = max((item.get("doanh_thu", 0) for item in self._current_data), default=0)
        min_revenue = min((item.get("doanh_thu", 0) for item in self._current_data), default=0)

        for row, item in enumerate(self._current_data):
            nhan_vien_id = item.get("nhan_vien_id", "")
            ho_ten = item.get("ho_ten", "")

            # Mã NV
            item_ma = QTableWidgetItem(f"NV{nhan_vien_id:04d}")
            item_ma.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, item_ma)

            # Tên NV
            self._table.setItem(row, 1, QTableWidgetItem(ho_ten))

            # Số HĐ mới
            so_hd_moi = item.get("so_hop_dong_moi_tao", 0)
            item_moi = QTableWidgetItem(str(so_hd_moi))
            item_moi.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 2, item_moi)

            # HĐ đã thanh toán
            so_hd_tt = item.get("so_hop_dong_da_thanh_toan", 0)
            item_tt = QTableWidgetItem(str(so_hd_tt))
            item_tt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, item_tt)

            # HĐ giao thành công
            so_hd_giao = item.get("so_hop_dong_giao_thanh_cong", 0)
            item_giao = QTableWidgetItem(str(so_hd_giao))
            item_giao.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 4, item_giao)

            # Tỷ lệ chốt
            ti_le = item.get("ti_le_chot", 0)
            item_rate = QTableWidgetItem(f"{ti_le:.1f}%")
            item_rate.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 5, item_rate)

            # Doanh thu
            doanh_thu = item.get("doanh_thu", 0)
            dt_text = f"{doanh_thu:,} đ".replace(",", ".")
            item_dt = QTableWidgetItem(dt_text)
            item_dt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 6, item_dt)

            # Highlight top performer green, bottom performer yellow/red
            if self._current_data:
                if row == 0 and doanh_thu == max_revenue and max_revenue > 0:
                    # Top performer
                    for col in range(self._table.columnCount()):
                        self._table.item(row, col).setBackground(QColor("#d4edda"))
                        self._table.item(row, col).setForeground(QColor("#155724"))
                elif doanh_thu == min_revenue and min_revenue < max_revenue and len(self._current_data) > 1:
                    # Bottom performer
                    for col in range(self._table.columnCount()):
                        self._table.item(row, col).setBackground(QColor("#fff3cd"))
                        self._table.item(row, col).setForeground(QColor("#856404"))

        # Set column widths
        self._table.setColumnWidth(0, 80)
        self._table.setColumnWidth(2, 90)
        self._table.setColumnWidth(3, 120)
        self._table.setColumnWidth(4, 130)
        self._table.setColumnWidth(5, 100)
        self._table.setColumnWidth(6, 150)

    def _export_to_excel(self):
        """Export report to Excel."""
        if not self._current_data:
            QMessageBox.information(self, "Thông báo", "Không có dữ liệu để xuất.")
            return

        try:
            from datetime import datetime

            month = self._month_combo.currentData()

            # Prepare sheet config
            sheet_config = {
                "name": "KPI nhân viên",
                "title": f"Báo cáo KPI nhân viên tháng {self._month_combo.currentText()}",
                "columns": [
                    {"header": "Mã NV", "key": "ma_nv", "width": 10},
                    {"header": "Tên nhân viên", "key": "ho_ten", "width": 25},
                    {"header": "Số HĐ mới", "key": "so_hop_dong_moi_tao", "width": 12, "format": "number"},
                    {"header": "HĐ đã thanh toán", "key": "so_hop_dong_da_thanh_toan", "width": 15, "format": "number"},
                    {"header": "HĐ giao thành công", "key": "so_hop_dong_giao_thanh_cong", "width": 18, "format": "number"},
                    {"header": "Tỷ lệ chốt (%)", "key": "ti_le_chot", "width": 15, "format": "percent"},
                    {"header": "Doanh thu", "key": "doanh_thu", "width": 18, "format": "money"},
                ],
            }

            # Prepare data
            export_data = []
            for item in self._current_data:
                export_data.append({
                    "ma_nv": f"NV{item.get('nhan_vien_id', 0):04d}",
                    "ho_ten": item.get("ho_ten", ""),
                    "so_hop_dong_moi_tao": item.get("so_hop_dong_moi_tao", 0),
                    "so_hop_dong_da_thanh_toan": item.get("so_hop_dong_da_thanh_toan", 0),
                    "so_hop_dong_giao_thanh_cong": item.get("so_hop_dong_giao_thanh_cong", 0),
                    "ti_le_chot": (item.get("ti_le_chot", 0) or 0) / 100,
                    "doanh_thu": item.get("doanh_thu", 0),
                })

            # Show save dialog
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"kpi_nhan_vien_{month}_{timestamp}.xlsx"

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