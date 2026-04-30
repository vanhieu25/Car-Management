"""Promotion effectiveness screen - S-KM-03 - Promotion effectiveness report.

Features:
- KpiCard row: so_hop_dong, doanh_thu, tong_giam
- Bar chart comparing KM effectiveness
- List of all KM with their effectiveness stats
- Filter by date range

References:
- BR-KM-09: Promotion effectiveness report
- UC-KM-05: Báo cáo hiệu quả KM
"""

from typing import Optional, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QDateEdit, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QPainter, QPen

from app.application.services.khuyen_mai_service import KhuyenMaiService
from app.application.services.session import CurrentSession


PAGE_SIZE = 50

LOAI_KM_LABELS = {
    "giam_tien_mat": "Giảm tiền mặt",
    "giam_phan_tram": "Giảm phần trăm",
    "tang_phu_kien": "Tặng phụ kiện",
    "giam_lai_suat": "Giảm lãi suất",
    "combo": "Combo",
}


class BarChartWidget(QWidget):
    """Simple horizontal bar chart widget for comparing KM effectiveness."""

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data or []
        self.setMinimumHeight(300)

    def set_data(self, data):
        """Set chart data.

        Args:
            data: List of dicts with 'ten_km', 'doanh_thu', 'tong_giam'.
        """
        self._data = data
        self.update()

    def paintEvent(self, event):
        """Paint the bar chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._data:
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Không có dữ liệu")
            return

        # Chart area
        margin = 20
        chart_rect = self.rect().adjusted(margin, margin, -margin, -margin)

        # Find max value for scaling
        max_val = max((d.get("tong_giam", 0) for d in self._data), default=1)
        if max_val == 0:
            max_val = 1

        bar_height = 30
        bar_spacing = 15
        label_width = 150
        value_width = 100

        y = chart_rect.top()
        for d in self._data:
            ten_km = d.get("ten_km", "")[:20]
            tong_giam = d.get("tong_giam", 0)

            # Label
            painter.setPen(QPen(QColor("#1d1d1f")))
            label_rect = QRect(chart_rect.left(), y, label_width, bar_height)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, ten_km)

            # Bar
            bar_width = int((chart_rect.width() - label_width - value_width - 20) * tong_giam / max_val)
            if bar_width < 2:
                bar_width = 2

            bar_rect = QRect(chart_rect.left() + label_width + 10, y + 5, bar_width, bar_height - 10)
            painter.fillRect(bar_rect, QColor("#0066cc"))

            # Value label
            value_text = f"{tong_giam:,} đ".replace(",", ".")
            value_rect = QRect(bar_rect.right() + 10, y, value_width, bar_height)
            painter.drawText(value_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, value_text)

            y += bar_height + bar_spacing


class KpiCard(QWidget):
    """KPI card widget with icon, value, and label."""

    def __init__(self, title: str, value: str, icon: str = "", color: str = "#1d1d1f", parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 80)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        self._icon_label = QLabel(icon)
        self._icon_label.setStyleSheet("font-size: 20px;")
        top_layout.addWidget(self._icon_label)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("font-size: 13px; color: #86868b; font-weight: 400;")
        top_layout.addWidget(self._title_label, stretch=1)

        self._value_label = QLabel(value)
        self._value_label.setStyleSheet(f"font-size: 24px; font-weight: 600; color: {color};")
        layout.addLayout(top_layout)
        layout.addWidget(self._value_label, alignment=Qt.AlignmentFlag.AlignLeft)


class PromoEffectivenessScreen(QWidget):
    """Promotion effectiveness screen - S-KM-03.

    Signals:
        view_promo_clicked(km_id: int): User wants to view a specific promotion.
    """

    view_promo_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize promotion effectiveness screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._km_service = KhuyenMaiService(db_conn, session)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Báo cáo hiệu quả khuyến mãi")
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

        filter_layout.addStretch()

        layout.addWidget(filter_group)

        # KPI Cards row
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self._kpi_contracts = KpiCard("Số hợp đồng", "0", "📄", "#0066cc")
        self._kpi_revenue = KpiCard("Doanh thu", "0 đ", "💰", "#34c759")
        self._kpi_discount = KpiCard("Tổng giảm giá", "0 đ", "🏷️", "#ff9500")

        kpi_layout.addWidget(self._kpi_contracts)
        kpi_layout.addWidget(self._kpi_revenue)
        kpi_layout.addWidget(self._kpi_discount)
        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)

        # Bar chart
        chart_group = QGroupBox("So sánh hiệu quả khuyến mãi (theo tổng giảm)")
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

        self._bar_chart = BarChartWidget()
        chart_layout.addWidget(self._bar_chart)

        layout.addWidget(chart_group)

        # Data table
        table_label = QLabel("Chi tiết theo chương trình khuyến mãi")
        table_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "ID", "Tên khuyến mãi", "Loại", "Số HĐ", "Doanh thu", "Tổng giảm", "Hiệu quả"
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
        self._table.cellDoubleClicked.connect(self._on_row_double_clicked)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)

        layout.addWidget(self._table)

        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()

        self._total_label = QLabel("Tổng: 0 khuyến mãi")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b;")
        pagination_layout.addWidget(self._total_label)

        layout.addLayout(pagination_layout)

    def _on_filter_changed(self):
        """Handle filter change - reload data."""
        self._load_data()

    def _load_data(self):
        """Load promotion effectiveness data."""
        try:
            all_km = self._km_service.get_all(limit=1000, offset=0)

            # Get effectiveness for each KM
            km_stats = []
            total_contracts = 0
            total_revenue = 0
            total_discount = 0

            for km in all_km:
                stats = self._km_service.report_effectiveness(km.id)
                so_hop_dong = stats.get("so_hop_dong", 0)
                doanh_thu = stats.get("doanh_thu", 0)
                tong_giam = stats.get("tong_giam", 0)

                total_contracts += so_hop_dong
                total_revenue += doanh_thu
                total_discount += tong_giam

                km_stats.append({
                    "id": km.id,
                    "ten_km": km.ten_km,
                    "loai_km": km.loai_km,
                    "so_hop_dong": so_hop_dong,
                    "doanh_thu": doanh_thu,
                    "tong_giam": tong_giam,
                })

            # Update KPI cards
            self._kpi_contracts._value_label.setText(str(total_contracts))
            self._kpi_revenue._value_label.setText(f"{total_revenue:,} đ".replace(",", "."))
            self._kpi_discount._value_label.setText(f"{total_discount:,} đ".replace(",", "."))

            # Update bar chart (top 10 by discount)
            chart_data = sorted(km_stats, key=lambda x: x["tong_giam"], reverse=True)[:10]
            self._bar_chart.set_data(chart_data)

            # Update table
            self._populate_table(km_stats)

            self._total_label.setText(f"Tổng: {len(km_stats)} khuyến mãi")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, items):
        """Populate table with effectiveness data.

        Args:
            items: List of dicts with KM stats.
        """
        self._table.setRowCount(len(items))

        for row, d in enumerate(items):
            # ID
            item_id = QTableWidgetItem(str(d["id"]))
            item_id.setData(Qt.ItemDataRole.UserRole, d["id"])
            self._table.setItem(row, 0, item_id)

            # Tên KM
            self._table.setItem(row, 1, QTableWidgetItem(d["ten_km"]))

            # Loại KM
            loai_text = LOAI_KM_LABELS.get(d["loai_km"], d["loai_km"])
            self._table.setItem(row, 2, QTableWidgetItem(loai_text))

            # Số HĐ
            item_hd = QTableWidgetItem(str(d["so_hop_dong"]))
            item_hd.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, item_hd)

            # Doanh thu
            doanh_thu_text = f"{d['doanh_thu']:,} đ".replace(",", ".")
            item_dt = QTableWidgetItem(doanh_thu_text)
            item_dt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 4, item_dt)

            # Tổng giảm
            tong_giam_text = f"{d['tong_giam']:,} đ".replace(",", ".")
            item_tg = QTableWidgetItem(tong_giam_text)
            item_tg.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 5, item_tg)

            # Hiệu quả (%)
            if d["doanh_thu"] > 0:
                hieu_qua = d["tong_giam"] / d["doanh_thu"] * 100
                hieu_qua_text = f"{hieu_qua:.1f}%"
            else:
                hieu_qua_text = "N/A"
            item_hq = QTableWidgetItem(hieu_qua_text)
            item_hq.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 6, item_hq)

        # Set column widths
        self._table.setColumnWidth(0, 50)
        self._table.setColumnWidth(2, 120)
        self._table.setColumnWidth(3, 80)
        self._table.setColumnWidth(4, 120)
        self._table.setColumnWidth(5, 120)
        self._table.setColumnWidth(6, 100)

    def _on_row_double_clicked(self, row: int, column: int):
        """Handle row double click."""
        item = self._table.item(row, 0)
        if item:
            km_id = item.data(Qt.ItemDataRole.UserRole)
            if km_id:
                self.view_promo_clicked.emit(km_id)

    def refresh(self):
        """Refresh the data."""
        self._load_data()
