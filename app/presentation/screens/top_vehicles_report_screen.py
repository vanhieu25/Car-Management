"""Top vehicles report screen - S-BC-02 - Top 10 best-selling vehicles report.

Features:
- Date range filter (from_date, to_date)
- Horizontal bar chart showing top vehicles by revenue
- Table: STT, Tên xe, Dòng xe, Số lượng bán, Doanh thu, Tỷ lệ %
- Export to Excel

References:
- BR-BC-02: Top vehicle sales by count and revenue
- RP-02: Top-selling vehicle report
"""

from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QDateEdit, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPainter, QPen

from app.application.services.bao_cao_service import BaoCaoService
from app.infrastructure.exporters.excel_exporter import ExcelExporter


class HorizontalBarChartWidget(QWidget):
    """Horizontal bar chart widget for top vehicles."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # List of (label, value) tuples
        self.setMinimumHeight(300)

    def set_data(self, data):
        """Set chart data.

        Args:
            data: List of (label, value) tuples.
        """
        self._data = data
        self.update()

    def paintEvent(self, event):
        """Paint the horizontal bar chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._data:
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Không có dữ liệu")
            return

        # Chart area with margins
        margin_left = 150
        margin_right = 80
        margin_top = 20
        margin_bottom = 20
        chart_rect = self.rect().adjusted(margin_left, margin_top, -margin_right, -margin_bottom)

        # Find max value for scaling
        values = [v for _, v in self._data]
        max_val = max(values) if values else 1
        if max_val == 0:
            max_val = 1

        # Draw bars
        bar_height = 28
        bar_spacing = 12

        for i, (label, value) in enumerate(self._data):
            y = chart_rect.top() + i * (bar_height + bar_spacing)

            # Draw label
            painter.setPen(QPen(QColor("#1d1d1f")))
            label_rect = QRect(0, y, margin_left - 10, bar_height)
            # Truncate label if too long
            display_label = label[:20] + "..." if len(label) > 20 else label
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, display_label)

            # Calculate bar width
            bar_width = int(chart_rect.width() * value / max_val)
            if bar_width < 2:
                bar_width = 2

            # Draw bar
            bar_rect = QRect(chart_rect.left(), y + 4, bar_width, bar_height - 8)
            painter.fillRect(bar_rect, QColor("#0066cc"))

            # Draw value label
            value_text = f"{value:,} đ".replace(",", ".")
            value_rect = QRect(bar_rect.right() + 8, y, 70, bar_height)
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(value_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, value_text)


class TopVehiclesReportScreen(QWidget):
    """Top vehicles report screen - S-BC-02."""

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize top vehicles report screen.

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
        self._total_revenue = 0

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Top xe bán chạy")
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
        self._date_from.setDate(QDate.currentDate().addMonths(-6))
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
        self._date_to.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self._date_to)

        # Top N
        filter_layout.addWidget(QLabel("Top:"))
        self._top_combo = QComboBox()
        self._top_combo.addItems(["10", "20", "50"])
        self._top_combo.setCurrentText("10")
        self._top_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 70px;
                background: white;
            }
        """)
        self._top_combo.currentTextChanged.connect(self._load_data)
        filter_layout.addWidget(self._top_combo)

        filter_layout.addStretch()

        layout.addWidget(filter_group)

        # Summary KPIs
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self._kpi_total = self._create_kpi_card("Tổng doanh thu", "0 đ", "#34c759")
        self._kpi_count = self._create_kpi_card("Tổng xe bán", "0", "#007aff")

        kpi_layout.addWidget(self._kpi_total)
        kpi_layout.addWidget(self._kpi_count)
        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)

        # Chart
        chart_group = QGroupBox("Top xe theo doanh thu")
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

        self._chart = HorizontalBarChartWidget()
        chart_layout.addWidget(self._chart)

        layout.addWidget(chart_group)

        # Data table
        table_label = QLabel("Chi tiết top xe bán chạy")
        table_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "STT", "Tên xe", "Dòng xe", "Màu sắc", "Số lượng bán", "Doanh thu"
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

    def _load_data(self):
        """Load top vehicles report data."""
        from_date = self._date_from.date().toString("yyyy-MM-dd")
        to_date = self._date_to.date().toString("yyyy-MM-dd")
        top = int(self._top_combo.currentText())

        try:
            result = self._bao_cao_service.top_xe(
                from_date=from_date,
                to_date=to_date,
                top=top,
            )

            # Calculate totals
            self._total_revenue = sum(item.get("doanh_thu", 0) for item in result)
            total_count = sum(item.get("so_lan_ban", 0) for item in result)

            # Update KPI cards
            self._update_kpi_value(self._kpi_total, f"{self._total_revenue:,} đ".replace(",", "."))
            self._update_kpi_value(self._kpi_count, str(total_count))

            # Calculate percentage
            for item in result:
                if self._total_revenue > 0:
                    item["ty_le"] = item.get("doanh_thu", 0) / self._total_revenue * 100
                else:
                    item["ty_le"] = 0

            self._current_data = result

            # Update chart
            chart_data = [
                (f"{item.get('hang', '')} {item.get('dong_xe', '')}", item.get("doanh_thu", 0))
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
        """Populate table with top vehicles data."""
        self._table.setRowCount(len(self._current_data))

        for row, item in enumerate(self._current_data):
            # STT
            item_stt = QTableWidgetItem(str(row + 1))
            item_stt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, item_stt)

            # Tên xe (hang + dong_xe)
            ten_xe = f"{item.get('hang', '')} {item.get('dong_xe', '')}"
            self._table.setItem(row, 1, QTableWidgetItem(ten_xe))

            # Dòng xe
            self._table.setItem(row, 2, QTableWidgetItem(item.get("dong_xe", "") or ""))

            # Màu sắc
            self._table.setItem(row, 3, QTableWidgetItem(item.get("mau_sac", "") or ""))

            # Số lượng bán
            so_luong = item.get("so_lan_ban", 0)
            item_sl = QTableWidgetItem(str(so_luong))
            item_sl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 4, item_sl)

            # Doanh thu
            doanh_thu = item.get("doanh_thu", 0)
            dt_text = f"{doanh_thu:,} đ".replace(",", ".")
            item_dt = QTableWidgetItem(dt_text)
            item_dt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 5, item_dt)

        # Set column widths
        self._table.setColumnWidth(0, 50)
        self._table.setColumnWidth(2, 120)
        self._table.setColumnWidth(3, 100)
        self._table.setColumnWidth(4, 100)
        self._table.setColumnWidth(5, 150)

    def _export_to_excel(self):
        """Export report to Excel."""
        if not self._current_data:
            QMessageBox.information(self, "Thông báo", "Không có dữ liệu để xuất.")
            return

        try:
            from datetime import datetime

            from_date = self._date_from.date().toString("yyyy-MM-dd")
            to_date = self._date_to.date().toString("yyyy-MM-dd")
            top = int(self._top_combo.currentText())

            # Prepare sheet config
            sheet_config = {
                "name": f"Top {top} xe bán chạy",
                "title": f"Top {top} xe bán chạy từ {from_date} đến {to_date}",
                "columns": [
                    {"header": "STT", "key": "stt", "width": 8},
                    {"header": "Tên xe", "key": "ten_xe", "width": 25},
                    {"header": "Dòng xe", "key": "dong_xe", "width": 15},
                    {"header": "Màu sắc", "key": "mau_sac", "width": 12},
                    {"header": "Số lượng bán", "key": "so_lan_ban", "width": 15, "format": "number"},
                    {"header": "Doanh thu", "key": "doanh_thu", "width": 18, "format": "money"},
                    {"header": "Tỷ lệ (%)", "key": "ty_le", "width": 12, "format": "percent"},
                ],
            }

            # Prepare data
            export_data = []
            for row, item in enumerate(self._current_data):
                export_data.append({
                    "stt": row + 1,
                    "ten_xe": f"{item.get('hang', '')} {item.get('dong_xe', '')}",
                    "dong_xe": item.get("dong_xe", "") or "",
                    "mau_sac": item.get("mau_sac", "") or "",
                    "so_lan_ban": item.get("so_lan_ban", 0),
                    "doanh_thu": item.get("doanh_thu", 0),
                    "ty_le": (item.get("ty_le", 0) or 0) / 100,
                })

            # Show save dialog
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"top_{top}_xe_ban_chay_{timestamp}.xlsx"

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