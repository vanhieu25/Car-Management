"""Dashboard screen - S-DB-01 - Main dashboard with KPI tiles and charts.

Features:
- 7 KPI tiles: revenue_month, hop_dong_month, xe_ton_kho, bh_expiring_30d,
  tg_qua_han, kh_birthday_7d, kn_cao
- 12-month revenue line chart
- Pie charts: xe by brand, hop_dong by status, khach_hang by classification
- "Cảnh báo" section with actionable alerts
- Auto-refresh every 5 minutes via QTimer
- Click KPI tile → navigate to detail screen

References:
- BR-BC-05: Dashboard KPI tiles
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QGroupBox,
    QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush

from app.application.services.dashboard_service import DashboardService
from app.application.services.session import CurrentSession


# ─────────────────────────────────────────────
#   WIDGETS: LineChart, PieChart, KpiCard
# ─────────────────────────────────────────────

class LineChartWidget(QWidget):
    """Simple line chart widget for 12-month revenue."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # List of (month_label, value)
        self.setMinimumHeight(220)

    def set_data(self, data):
        self._data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._data:
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Không có dữ liệu")
            return

        margin_left, margin_right, margin_top, margin_bottom = 60, 20, 20, 40
        chart_rect = self.rect().adjusted(margin_left, margin_top, -margin_right, -margin_bottom)

        values = [v for _, v in self._data]
        max_val = max(values) if values else 1
        min_val = 0
        range_val = max_val - min_val or 1

        # Axes
        painter.setPen(QPen(QColor("#d2d2d7"), 1))
        painter.drawLine(chart_rect.left(), chart_rect.bottom(), chart_rect.right(), chart_rect.bottom())
        painter.drawLine(chart_rect.left(), chart_rect.top(), chart_rect.left(), chart_rect.bottom())

        # Grid + Y labels
        grid_count = 4
        painter.setPen(QPen(QColor("#e5e5ea"), 1))
        for i in range(grid_count + 1):
            y_ratio = i / grid_count
            y = chart_rect.bottom() - int(chart_rect.height() * y_ratio)
            val = int(min_val + range_val * y_ratio)
            label = f"{val // 1000000}M" if val >= 1000000 else f"{val // 1000}K"
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(chart_rect.left() - 50, y + 5, label)
            painter.setPen(QPen(QColor("#e5e5ea"), 1))
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)

        # Points
        point_count = len(self._data)
        if point_count == 0:
            return
        step_x = chart_rect.width() / max(point_count - 1, 1)
        points = []
        for i, (_, value) in enumerate(self._data):
            x = chart_rect.left() + int(i * step_x)
            y = chart_rect.bottom() - int(chart_rect.height() * (value - min_val) / range_val)
            points.append((x, y))

        # Line
        painter.setPen(QPen(QColor("#0066cc"), 2.5))
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

        # Points + X labels
        for i, ((x, y), (label, _)) in enumerate(zip(points, self._data)):
            painter.setBrush(QColor("#0066cc"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRect(x - 4, y - 4, 8, 8))
            if point_count <= 12 or i % 2 == 0:
                painter.setPen(QPen(QColor("#86868b")))
                painter.drawText(x - 15, chart_rect.bottom() + 20, label)


class PieChartWidget(QWidget):
    """Animated pie chart widget with legend and center hole (donut style)."""

    PIE_COLORS = [
        "#0066cc", "#34c759", "#ff9500", "#ff3b30",
        "#af52de", "#5856d6", "#00c7be", "#ff2d55",
        "#64d2ff", "#ffd60a", "#30d158", "#64748b",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments: List[Tuple[str, float]] = []  # (label, value)
        self.setMinimumHeight(280)

    def set_data(self, segments: List[Tuple[str, float]]):
        """Set pie chart data.

        Args:
            segments: List of (label, value) tuples. Values should be positive.
        """
        self._segments = segments
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._segments:
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Không có dữ liệu")
            return

        total = sum(v for _, v in self._segments)
        if total <= 0:
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Dữ liệu không hợp lệ")
            return

        # Layout: left = pie, right = legend
        rect = self.rect()
        pie_size = min(rect.width() // 2, rect.height() - 20, 240)
        pie_rect = QRect(
            20,
            (rect.height() - pie_size) // 2,
            pie_size,
            pie_size,
        )

        # Donut hole
        hole_ratio = 0.55
        inner_radius = int(pie_size // 2 * hole_ratio)
        outer_radius = pie_size // 2

        # Draw pie slices
        start_angle = 90 * 16  # 16ths of degree, starting from top
        for idx, (_, value) in enumerate(self._segments):
            sweep_angle = int((value / total) * 360 * 16)
            color = QColor(self.PIE_COLORS[idx % len(self.PIE_COLORS)])
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            # Draw pie as chord (slice)
            painter.drawPie(QRectF(pie_rect), start_angle, sweep_angle)
            start_angle += sweep_angle

        # Draw white center circle (donut hole) - white background
        center_x = pie_rect.center().x()
        center_y = pie_rect.center().y()
        painter.setBrush(QColor("white"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            int(center_x - inner_radius),
            int(center_y - inner_radius),
            int(inner_radius * 2),
            int(inner_radius * 2),
        )

        # Draw total in center
        total_display = f"{total:,.0f}"
        if total >= 1000000000:
            center_text = f"{total/1000000000:.1f}T"
        elif total >= 1000000:
            center_text = f"{total/1000000:.1f}M"
        elif total >= 1000:
            center_text = f"{total/1000:.0f}K"
        else:
            center_text = f"{total:.0f}"

        painter.setPen(QPen(QColor("#1d1d1f"), 1))
        font = painter.font()
        font.setPixelSize(min(18, inner_radius // 2))
        painter.setFont(font)
        painter.drawText(
            int(center_x - inner_radius),
            int(center_y - inner_radius // 4),
            int(inner_radius * 2),
            int(inner_radius // 2),
            Qt.AlignmentFlag.AlignCenter,
            center_text,
        )

        # Legend on the right
        legend_x = pie_size + 40
        legend_y = 10
        legend_max_width = rect.width() - legend_x - 20

        for idx, (label, value) in enumerate(self._segments):
            color = QColor(self.PIE_COLORS[idx % len(self.PIE_COLORS)])
            pct = (value / total) * 100

            # Color box
            box_size = 14
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(legend_x, legend_y + idx * 26, box_size, box_size)

            # Label
            painter.setPen(QPen(QColor("#1d1d1f")))
            font = painter.font()
            font.setPixelSize(13)
            painter.setFont(font)
            label_text = f"{label} ({pct:.1f}%)"
            painter.drawText(legend_x + box_size + 6, legend_y + idx * 26 + 12, label_text)


class KpiCard(QWidget):
    """KPI card widget - clickable tile for dashboard."""

    clicked = pyqtSignal(str)

    def __init__(
        self,
        key: str,
        title: str,
        value: str,
        subtitle: str = "",
        icon: str = "",
        color: str = "#1d1d1f",
        is_alert: bool = False,
        alert_color: str = "#ff3b30",
        parent=None
    ):
        super().__init__(parent)
        self._key = key
        self._is_alert = is_alert
        self._alert_color = alert_color

        self.setMinimumSize(250, 250)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 10px;
                padding: 14px;
            }}
            QWidget:hover {{
                border: 2px solid #0066cc;
                background-color: #f5f9ff;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Top row: icon + title
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        top_layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 13px; color: #86868b; font-weight: 400;")
        top_layout.addWidget(title_lbl, stretch=1)
        layout.addLayout(top_layout)

        # Value (large)
        value_lbl = QLabel(value)
        val_color = alert_color if is_alert else color
        value_lbl.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {val_color};")
        layout.addWidget(value_lbl)

        # Subtitle (extra info)
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet("font-size: 11px; color: #86868b;")
            layout.addWidget(sub_lbl)

        layout.addStretch()

        self._value_label = value_lbl

    def set_value(self, value: str):
        self._value_label.setText(value)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._key)
        super().mousePressEvent(event)


class AlertListItem(QWidget):
    """Single alert item in the alerts section."""

    clicked = pyqtSignal(str, int)

    def __init__(self, alert_type: str, alert_id: int, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self._alert_type = alert_type
        self._alert_id = alert_id

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 10px 14px;
            }
            QWidget:hover {
                background-color: #fff5f5;
                border-color: #ff3b30;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        icon_lbl = QLabel("⚠️")
        icon_lbl.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_lbl)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #1d1d1f;")
        text_layout.addWidget(title_lbl)
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet("font-size: 11px; color: #86868b;")
            text_layout.addWidget(sub_lbl)
        layout.addLayout(text_layout, stretch=1)

        arrow_lbl = QLabel("›")
        arrow_lbl.setStyleSheet("font-size: 18px; color: #86868b;")
        layout.addWidget(arrow_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._alert_type, self._alert_id)
        super().mousePressEvent(event)


# ─────────────────────────────────────────────
#   DASHBOARD SCREEN
# ─────────────────────────────────────────────

class DashboardScreen(QWidget):
    """Main dashboard screen - S-DB-01."""

    navigate_to = pyqtSignal(str)

    KPI_NAV_MAP = {
        "revenue_month": "bao_cao",
        "hop_dong_month": "hop_dong",
        "xe_ton_kho": "kho",
        "bh_expiring_30d": "bao_hanh",
        "tg_qua_han": "tra_gop",
        "kh_birthday_7d": "khach_hang",
        "kn_cao": "khieu_nai",
    }

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._dashboard_service = DashboardService(db_conn)
        self._kpi_cards: Dict[str, KpiCard] = {}
        self._alerts: list = []

        self._setup_ui()
        self._start_auto_refresh()
        self._load_data()

    def _setup_ui(self):
        """Set up the redesigned dashboard UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # ── Header ──
        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header.addWidget(title)

        self._refresh_time_lbl = QLabel("")
        self._refresh_time_lbl.setStyleSheet("font-size: 13px; color: #86868b;")
        header.addWidget(self._refresh_time_lbl)
        header.addStretch()

        self._refresh_btn = QPushButton("🔄 Làm mới")
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc; color: white;
                border: none; border-radius: 6px;
                padding: 8px 16px; font-size: 14px;
            }
            QPushButton:hover { background-color: #0055aa; }
        """)
        self._refresh_btn.clicked.connect(self._load_data)
        header.addWidget(self._refresh_btn)
        main_layout.addLayout(header)

        # ── Scroll area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(24)

        # ── Section: Tổng quan KPIs (2-column grid) ──
        kpi_label = QLabel("Tổng quan")
        kpi_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        scroll_layout.addWidget(kpi_label)

        kpi_configs = [
            ("revenue_month", "Doanh thu tháng", "💰", "#34c759", False, ""),
            ("hop_dong_month", "Hợp đồng mới", "📄", "#007aff", False, ""),
            ("xe_ton_kho", "Tồn kho xe", "🚗", "#5856d6", False, ""),
            ("bh_expiring_30d", "BH sắp hết (30d)", "🛡️", "#ff9500", True, "xe cần gia hạn"),
            ("tg_qua_han", "Trả góp quá hạn", "⚠️", "#ff3b30", True, "hồ sơ chưa thanh toán"),
            ("kh_birthday_7d", "KH sinh nhật (±7d)", "🎂", "#af52de", False, "khách hàng thân thiết"),
            ("kn_cao", "Khiếu nại cao", "🔴", "#ff3b30", True, "kn mức cao chưa đóng"),
        ]

        # Grid: 4 per row (first 4), then 3 on next row
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(16)

        for idx, (key, title, icon, color, is_alert, subtitle) in enumerate(kpi_configs):
            row = idx // 4
            col = idx % 4
            card = KpiCard(
                key=key, title=title, value="—",
                subtitle=subtitle, icon=icon,
                color=color, is_alert=is_alert,
                alert_color=color if is_alert else "#ff3b30",
            )
            card.clicked.connect(self._on_kpi_clicked)
            kpi_grid.addWidget(card, row, col)
            self._kpi_cards[key] = card

        scroll_layout.addLayout(kpi_grid)

        # ── Section: Biểu đồ tròn (Pie Charts) ──
        charts_label = QLabel("Thống kê")
        charts_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        scroll_layout.addWidget(charts_label)

        # Three pie charts in a row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        # Pie 1: Xe theo hãng
        xe_group = QGroupBox("Xe theo hãng")
        xe_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 10px;
                padding: 16px;
                font-weight: 600; color: #1d1d1f;
            }
            QGroupBox::title { padding: 0 8px; }
        """)
        xe_pie_layout = QVBoxLayout(xe_group)
        self._pie_xe = PieChartWidget()
        xe_pie_layout.addWidget(self._pie_xe)
        charts_row.addWidget(xe_group)

        # Pie 2: Hợp đồng theo trạng thái
        hd_group = QGroupBox("Hợp đồng theo trạng thái")
        hd_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 10px;
                padding: 16px;
                font-weight: 600; color: #1d1d1f;
            }
            QGroupBox::title { padding: 0 8px; }
        """)
        hd_pie_layout = QVBoxLayout(hd_group)
        self._pie_hd = PieChartWidget()
        hd_pie_layout.addWidget(self._pie_hd)
        charts_row.addWidget(hd_group)

        # Pie 3: Khách hàng theo phân loại
        kh_group = QGroupBox("Khách hàng theo phân loại")
        kh_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 10px;
                padding: 16px;
                font-weight: 600; color: #1d1d1f;
            }
            QGroupBox::title { padding: 0 8px; }
        """)
        kh_pie_layout = QVBoxLayout(kh_group)
        self._pie_kh = PieChartWidget()
        kh_pie_layout.addWidget(self._pie_kh)
        charts_row.addWidget(kh_group)

        scroll_layout.addLayout(charts_row)

        # ── Section: Doanh thu 12 tháng ──
        revenue_label = QLabel("Doanh thu 12 tháng")
        revenue_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        scroll_layout.addWidget(revenue_label)

        revenue_group = QGroupBox()
        revenue_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 10px;
                padding: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                font-weight: 600; color: #1d1d1f;
            }
        """)
        revenue_layout = QVBoxLayout(revenue_group)
        self._line_chart = LineChartWidget()
        revenue_layout.addWidget(self._line_chart)
        scroll_layout.addWidget(revenue_group)

        # ── Section: Cảnh báo ──
        alerts_label = QLabel("Cảnh báo")
        alerts_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        scroll_layout.addWidget(alerts_label)

        self._alerts_container = QVBoxLayout()
        self._alerts_container.setSpacing(8)
        self._no_alerts_lbl = QLabel("Không có cảnh báo nào 🎉")
        self._no_alerts_lbl.setStyleSheet("""
            font-size: 14px; color: #34c759;
            padding: 16px;
            background-color: #f0f9f0;
            border-radius: 8px;
        """)
        self._alerts_container.addWidget(self._no_alerts_lbl)
        scroll_layout.addLayout(self._alerts_container)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)

    def _start_auto_refresh(self):
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_data)
        self._refresh_timer.start(5 * 60 * 1000)

    def _load_data(self):
        """Load all dashboard data."""
        import logging
        logger = logging.getLogger("car_management")

        try:
            role = self._session.vai_tro_ma if self._session else "admin"
            user_id = getattr(self._session, "nhan_vien_id", None) if self._session else None

            result = self._dashboard_service.get_summary(role=role, user_id=user_id)
            kpis = result.get("kpis", {})

            # Update KPI cards
            self._update_kpi_card("revenue_month", kpis.get("revenue_month", 0))
            self._update_kpi_card("hop_dong_month", kpis.get("hop_dong_month", 0))
            self._update_kpi_card("xe_ton_kho", kpis.get("xe_ton_kho", 0))
            self._update_kpi_card("bh_expiring_30d", kpis.get("bh_expiring_30d", 0))
            self._update_kpi_card("tg_qua_han", kpis.get("tg_qua_han", 0))
            self._update_kpi_card("kh_birthday_7d", kpis.get("kh_birthday_7d", 0))
            self._update_kpi_card("kn_cao", kpis.get("kn_cao", 0))

            # Load pie charts
            self._load_pie_charts()

            # Load line chart
            self._load_revenue_chart()

            # Load alerts
            self._load_alerts()

            now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            self._refresh_time_lbl.setText(f"Cập nhật lúc: {now}")

        except Exception as e:
            logger.error(f"[Dashboard] Error: {e}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dashboard: {str(e)}")

    def _update_kpi_card(self, key: str, value):
        card = self._kpi_cards.get(key)
        if not card:
            return

        if key == "revenue_month":
            formatted = f"{value:,} đ".replace(",", ".")
        elif key in ("bh_expiring_30d", "tg_qua_han", "kn_cao") and value and value > 0:
            formatted = str(value)
        elif value == "—" or value is None:
            formatted = "—"
        else:
            formatted = str(value)

        card.set_value(formatted)

    def _load_pie_charts(self):
        """Load data for 3 pie charts."""
        try:
            # Pie 1: Xe theo hãng (from xe table)
            cursor = self._db_conn.execute(
                """SELECT hang, SUM(so_luong_ton) as total
                   FROM xe
                   WHERE trang_thai = 'con_hang'
                   GROUP BY hang
                   ORDER BY total DESC"""
            )
            xe_data = [(row[0], row[1]) for row in cursor.fetchall() if row[1] > 0]
            self._pie_xe.set_data(xe_data)

            # Pie 2: Hợp đồng theo trạng thái
            cursor = self._db_conn.execute(
                """SELECT trang_thai, COUNT(*) as total
                   FROM hop_dong
                   GROUP BY trang_thai"""
            )
            status_map = {
                "moi_tao": "Mới tạo",
                "da_xac_nhan": "Đã xác nhận",
                "dang_xu_ly": "Đang xử lý",
                "da_giao_xe": "Đã giao xe",
                "da_huy": "Đã hủy",
                "cho_thanh_toan": "Chờ thanh toán",
            }
            hd_data = [
                (status_map.get(row[0], row[0]), row[1])
                for row in cursor.fetchall()
            ]
            self._pie_hd.set_data(hd_data)

            # Pie 3: Khách hàng theo phân loại
            cursor = self._db_conn.execute(
                """SELECT phan_loai, COUNT(*) as total
                   FROM khach_hang
                   GROUP BY phan_loai"""
            )
            kh_data = [
                ({"VIP": "VIP", "Than_thiet": "Thân thiết", "Thuong": "Thường"}.get(row[0], row[0]), row[1])
                for row in cursor.fetchall()
            ]
            self._pie_kh.set_data(kh_data)

        except Exception as e:
            import logging
            logging.getLogger("car_management").error(f"Pie chart load error: {e}")

    def _load_revenue_chart(self):
        """Load 12-month revenue data for line chart."""
        try:
            from dateutil.relativedelta import relativedelta
            now = datetime.now()
            months_data = []

            for i in range(11, -1, -1):
                d = now - relativedelta(months=i)
                month_label = d.strftime("%m/%Y")
                revenue = self._dashboard_service._get_revenue_month(d.year, d.month)
                months_data.append((month_label, revenue))

            self._line_chart.set_data(months_data)
        except Exception:
            self._line_chart.set_data([])

    def _load_alerts(self):
        """Load alerts section."""
        while self._alerts_container.count():
            item = self._alerts_container.takeAt(0)
            if item.widget() and item.widget() != self._no_alerts_lbl:
                item.widget().deleteLater()

        alerts = []
        try:
            bh = self._kpi_cards["bh_expiring_30d"]
            tg = self._kpi_cards["tg_qua_han"]
            kn = self._kpi_cards["kn_cao"]

            if bh._value_label.text() not in ("—", "0"):
                alerts.append({
                    "type": "bh_expiring",
                    "title": f"Bảo hành sắp hết hạn: {bh._value_label.text()} xe",
                    "subtitle": "Xem danh sách bảo hành sắp hết",
                })
            if tg._value_label.text() not in ("—", "0"):
                alerts.append({
                    "type": "tg_qua_han",
                    "title": f"Trả góp quá hạn: {tg._value_label.text()} hồ sơ",
                    "subtitle": "Xem danh sách trả góp quá hạn",
                })
            if kn._value_label.text() not in ("—", "0"):
                alerts.append({
                    "type": "kn_cao",
                    "title": f"Khiếu nại cấp cao: {kn._value_label.text()} KN",
                    "subtitle": "Xem danh sách khiếu nại",
                })
        except Exception:
            pass

        if alerts:
            self._no_alerts_lbl.setVisible(False)
            for alert in alerts:
                w = AlertListItem(
                    alert_type=alert["type"],
                    alert_id=0,
                    title=alert["title"],
                    subtitle=alert.get("subtitle", ""),
                )
                w.clicked.connect(self._on_alert_clicked)
                self._alerts_container.addWidget(w)
        else:
            self._no_alerts_lbl.setVisible(True)

    def _on_kpi_clicked(self, key: str):
        target = self.KPI_NAV_MAP.get(key)
        if target:
            self.navigate_to.emit(target)

    def _on_alert_clicked(self, alert_type: str, alert_id: int):
        target = self.KPI_NAV_MAP.get(alert_type)
        if target:
            self.navigate_to.emit(target)

    def refresh(self):
        self._load_data()
