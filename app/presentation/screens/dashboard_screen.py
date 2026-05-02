"""Dashboard screen - S-DB-01 - Main dashboard with KPI tiles and charts.

Features:
- 7 KPI tiles: revenue_month, hop_dong_month, xe_ton_kho, bh_expiring_30d,
  tg_qua_han, kh_birthday_7d, kn_cao
- 12-month revenue line chart
- "Cảnh báo" section with actionable alerts
- Auto-refresh every 5 minutes via QTimer
- Click KPI tile → navigate to detail screen

References:
- BR-BC-05: Dashboard KPI tiles
"""

from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QGroupBox,
    QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QColor, QPainter, QPen

from app.application.services.dashboard_service import DashboardService
from app.application.services.session import CurrentSession


class LineChartWidget(QWidget):
    """Simple line chart widget for 12-month revenue."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # List of (month_label, value)
        self.setMinimumHeight(220)

    def set_data(self, data):
        """Set chart data.

        Args:
            data: List of (month_label, revenue_value) tuples.
        """
        self._data = data
        self.update()

    def paintEvent(self, event):
        """Paint the line chart."""
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
        margin_bottom = 40
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
        painter.drawLine(chart_rect.left(), chart_rect.bottom(), chart_rect.right(), chart_rect.bottom())
        painter.drawLine(chart_rect.left(), chart_rect.top(), chart_rect.left(), chart_rect.bottom())

        # Draw horizontal grid lines and Y-axis labels
        grid_count = 4
        painter.setPen(QPen(QColor("#e5e5ea"), 1))
        for i in range(grid_count + 1):
            y_ratio = i / grid_count
            y = chart_rect.bottom() - int(chart_rect.height() * y_ratio)
            x = chart_rect.left()

            # Grid line
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)

            # Y-axis label
            val = int(min_val + range_val * y_ratio)
            label = f"{val // 1000000}M" if val >= 1000000 else f"{val // 1000}K"
            painter.setPen(QPen(QColor("#86868b")))
            painter.drawText(x - 50, y + 5, label)
            painter.setPen(QPen(QColor("#e5e5ea"), 1))

        # Calculate point positions
        point_count = len(self._data)
        if point_count == 0:
            return

        step_x = chart_rect.width() / max(point_count - 1, 1)
        points = []
        for i, (_, value) in enumerate(self._data):
            x = chart_rect.left() + int(i * step_x)
            y = chart_rect.bottom() - int(chart_rect.height() * (value - min_val) / range_val)
            points.append((x, y))

        # Draw line
        painter.setPen(QPen(QColor("#0066cc"), 2.5))
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

        # Draw points and X-axis labels
        for i, ((x, y), (label, _)) in enumerate(zip(points, self._data)):
            # Point
            painter.setBrush(QColor("#0066cc"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRect(x - 4, y - 4, 8, 8))

            # X-axis label (show every other label if many)
            if point_count <= 12 or i % 2 == 0:
                painter.setPen(QPen(QColor("#86868b")))
                painter.drawText(x - 15, chart_rect.bottom() + 20, label)


class KpiCard(QWidget):
    """KPI card widget - clickable tile for dashboard."""

    clicked = pyqtSignal(str)

    def __init__(
        self,
        key: str,
        title: str,
        value: str,
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
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Top row: icon + title
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        self._icon_label = QLabel(icon)
        self._icon_label.setStyleSheet("font-size: 18px;")
        top_layout.addWidget(self._icon_label)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("font-size: 12px; color: #86868b; font-weight: 400;")
        top_layout.addWidget(self._title_label, stretch=1)

        layout.addLayout(top_layout)

        # Value
        self._value_label = QLabel(value)
        value_color = color if not is_alert else alert_color
        self._value_label.setStyleSheet(f"font-size: 22px; font-weight: 600; color: {value_color};")

        # Alert badge
        if is_alert:
            val_layout = QHBoxLayout()
            val_layout.addWidget(self._value_label)
            val_layout.addStretch()
            alert_badge = QLabel("⚠️")
            alert_badge.setStyleSheet("font-size: 16px;")
            val_layout.addWidget(alert_badge)
            layout.addLayout(val_layout)
        else:
            layout.addWidget(self._value_label, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addStretch()

    def set_value(self, value: str):
        """Update the displayed value."""
        self._value_label.setText(value)

    def mousePressEvent(self, event):
        """Emit clicked signal with key."""
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

        # Icon
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_label)

        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #1d1d1f;")
        text_layout.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("font-size: 11px; color: #86868b;")
            text_layout.addWidget(sub_label)

        layout.addLayout(text_layout, stretch=1)

        # Arrow
        arrow_label = QLabel("›")
        arrow_label.setStyleSheet("font-size: 18px; color: #86868b;")
        layout.addWidget(arrow_label)

    def mousePressEvent(self, event):
        """Emit clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._alert_type, self._alert_id)
        super().mousePressEvent(event)


class DashboardScreen(QWidget):
    """Main dashboard screen - S-DB-01.

    Signals:
        navigate_to(module_id: str): Request navigation to a specific module.
    """

    navigate_to = pyqtSignal(str)

    # Mapping of KPI keys to target screens
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
        """Initialize dashboard screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        import sys
        print("[DASHBOARD] __init__ called", file=sys.stderr)
        print(f"[DASHBOARD]   db_conn={db_conn}", file=sys.stderr)
        print(f"[DASHBOARD]   session={session}", file=sys.stderr)
        print(f"[DASHBOARD]   session.vai_tro_ma={session.vai_tro_ma if session else None}", file=sys.stderr)
        
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._dashboard_service = DashboardService(db_conn)

        self._kpi_cards: Dict[str, KpiCard] = {}
        self._alerts: list = []

        print("[DASHBOARD] Calling _setup_ui()", file=sys.stderr)
        self._setup_ui()
        print("[DASHBOARD] Calling _start_auto_refresh()", file=sys.stderr)
        self._start_auto_refresh()
        print("[DASHBOARD] Calling _load_data()", file=sys.stderr)
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        self._refresh_time_label = QLabel("")
        self._refresh_time_label.setStyleSheet("font-size: 13px; color: #86868b;")
        header_layout.addWidget(self._refresh_time_label)

        header_layout.addStretch()

        # Refresh button
        self._refresh_btn = QPushButton("🔄 Làm mới")
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(self._refresh_btn)

        layout.addLayout(header_layout)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)

        # --- KPI Cards Row ---
        kpi_section_label = QLabel("Tổng quan")
        kpi_section_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        scroll_layout.addWidget(kpi_section_label)

        # KPI grid (3-4 or 4-3 layout)
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(16)

        kpi_configs = [
            ("revenue_month", "Doanh thu tháng", "💰", "#34c759", False),
            ("hop_dong_month", "Hợp đồng mới", "📄", "#007aff", False),
            ("xe_ton_kho", "Tồn kho xe", "🚗", "#5856d6", False),
            ("bh_expiring_30d", "BH sắp hết (30d)", "🛡️", "#ff9500", True),
            ("tg_qua_han", "Trả góp quá hạn", "⚠️", "#ff3b30", True),
            ("kh_birthday_7d", "KH sinh nhật (±7d)", "🎂", "#af52de", False),
            ("kn_cao", "Khiếu nại cao", "🔴", "#ff3b30", True),
        ]

        for idx, (key, title, icon, color, is_alert) in enumerate(kpi_configs):
            row = idx // 4
            col = idx % 4
            card = KpiCard(
                key=key,
                title=title,
                value="—",
                icon=icon,
                color=color,
                is_alert=is_alert,
                alert_color=color if is_alert else "#ff3b30",
            )
            card.clicked.connect(self._on_kpi_clicked)
            kpi_grid.addWidget(card, row, col)
            self._kpi_cards[key] = card

        scroll_layout.addLayout(kpi_grid)

        # --- Revenue Chart Section ---
        chart_section_label = QLabel("Doanh thu 12 tháng")
        chart_section_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        scroll_layout.addWidget(chart_section_label)

        chart_group = QGroupBox()
        chart_group.setStyleSheet("""
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
                font-weight: 600;
                color: #1d1d1f;
            }
        """)
        chart_layout = QVBoxLayout(chart_group)

        self._line_chart = LineChartWidget()
        chart_layout.addWidget(self._line_chart)

        scroll_layout.addWidget(chart_group)

        # --- Alerts Section ---
        alerts_section_label = QLabel("Cảnh báo")
        alerts_section_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        scroll_layout.addWidget(alerts_section_label)

        self._alerts_container = QVBoxLayout()
        self._alerts_container.setSpacing(8)

        self._no_alerts_label = QLabel("Không có cảnh báo nào 🎉")
        self._no_alerts_label.setStyleSheet("""
            font-size: 14px;
            color: #34c759;
            padding: 16px;
            background-color: #f0f9f0;
            border-radius: 8px;
        """)
        self._alerts_container.addWidget(self._no_alerts_label)

        scroll_layout.addLayout(self._alerts_container)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

    def _start_auto_refresh(self):
        """Start 5-minute auto-refresh timer."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_data)
        self._refresh_timer.start(5 * 60 * 1000)  # 5 minutes

    def _load_data(self):
        """Load dashboard data from service."""
        import logging
        logger = logging.getLogger("car_management")
        
        try:
            role = self._session.vai_tro_ma if self._session else "A-01"
            user_id = getattr(self._session, "nhan_vien_id", None) if self._session else None

            logger.info(f"[Dashboard] Loading data - role: {role}, user_id: {user_id}")
            logger.info(f"[Dashboard] DB service: {self._dashboard_service}")
            logger.info(f"[Dashboard] DB conn: {self._db_conn}")

            result = self._dashboard_service.get_summary(role=role, user_id=user_id)
            kpis = result.get("kpis", {})

            logger.info(f"[Dashboard] KPIs loaded: {kpis}")

            # Update KPI cards
            self._update_kpi_card("revenue_month", kpis.get("revenue_month", 0))
            self._update_kpi_card("hop_dong_month", kpis.get("hop_dong_month", 0))
            self._update_kpi_card("xe_ton_kho", kpis.get("xe_ton_kho", 0))
            self._update_kpi_card("bh_expiring_30d", kpis.get("bh_expiring_30d", 0))
            self._update_kpi_card("tg_qua_han", kpis.get("tg_qua_han", 0))
            self._update_kpi_card("kh_birthday_7d", kpis.get("kh_birthday_7d", 0))
            self._update_kpi_card("kn_cao", kpis.get("kn_cao", 0))

            # Load 12-month revenue chart
            self._load_revenue_chart()

            # Load alerts
            self._load_alerts()

            # Update refresh time
            now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            self._refresh_time_label.setText(f"Cập nhật lúc: {now}")

        except Exception as e:
            logger.error(f"[Dashboard] Error: {e}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dashboard: {str(e)}")

    def _update_kpi_card(self, key: str, value):
        """Update a single KPI card value with formatting."""
        card = self._kpi_cards.get(key)
        if not card:
            return

        if key == "revenue_month":
            # Format as VND
            formatted = f"{value:,} đ".replace(",", ".")
        elif key in ("bh_expiring_30d", "tg_qua_han", "kn_cao") and value > 0:
            # Alert KPIs - show count
            formatted = str(value)
        elif value == "—":
            formatted = "—"
        else:
            formatted = str(value)

        card.set_value(formatted)

    def _load_revenue_chart(self):
        """Load 12-month revenue data for line chart."""
        try:
            from datetime import date
            from dateutil.relativedelta import relativedelta

            now = datetime.now()
            months_data = []

            # Get last 12 months
            for i in range(11, -1, -1):
                d = now - relativedelta(months=i)
                month_key = d.strftime("%Y-%m")
                month_label = d.strftime("%m/%Y")

                # Get revenue for this month
                revenue = self._dashboard_service._get_revenue_month(d.year, d.month)
                months_data.append((month_label, revenue))

            self._line_chart.set_data(months_data)

        except ImportError:
            # Fallback: simple month names
            months_data = [(f"Th{i+1}/2025", 0) for i in range(12)]
            self._line_chart.set_data(months_data)
        except Exception as e:
            # Fallback to empty
            self._line_chart.set_data([])

    def _load_alerts(self):
        """Load and display alerts section."""
        # Clear existing alerts
        while self._alerts_container.count():
            item = self._alerts_container.takeAt(0)
            if item.widget() and item.widget() != self._no_alerts_label:
                item.widget().deleteLater()

        alerts = []

        # Get alert data from KPIs
        try:
            bh_expiring = self._kpi_cards["bh_expiring_30d"]
            tg_qua_han = self._kpi_cards["tg_qua_han"]
            kn_cao = self._kpi_cards["kn_cao"]
            birthday = self._kpi_cards["kh_birthday_7d"]

            # Add alerts if values > 0
            # (For simplicity, we show the alert type with ID 0 - the list screens will show all)
            if bh_expiring._value_label.text() not in ("—", "0"):
                alerts.append({
                    "type": "bh_expiring",
                    "title": f"Bảo hành sắp hết hạn: {bh_expiring._value_label.text()} xe",
                    "subtitle": "Xem danh sách bảo hành sắp hết",
                })

            tg_value = tg_qua_han._value_label.text()
            if tg_value not in ("—", "0"):
                alerts.append({
                    "type": "tg_qua_han",
                    "title": f"Trả góp quá hạn: {tg_value} hồ sơ",
                    "subtitle": "Xem danh sách trả góp quá hạn",
                })

            if kn_cao._value_label.text() not in ("—", "0"):
                alerts.append({
                    "type": "kn_cao",
                    "title": f"Khiếu nại cấp cao: {kn_cao._value_label.text()} KN",
                    "subtitle": "Xem danh sách khiếu nại",
                })

        except Exception:
            pass

        if alerts:
            self._no_alerts_label.setVisible(False)
            for alert in alerts:
                alert_widget = AlertListItem(
                    alert_type=alert["type"],
                    alert_id=0,  # Will be handled by list screens
                    title=alert["title"],
                    subtitle=alert.get("subtitle", ""),
                )
                alert_widget.clicked.connect(self._on_alert_clicked)
                self._alerts_container.addWidget(alert_widget)
        else:
            self._no_alerts_label.setVisible(True)

    def _on_kpi_clicked(self, key: str):
        """Handle KPI card click - navigate to relevant screen."""
        target = self.KPI_NAV_MAP.get(key)
        if target:
            self.navigate_to.emit(target)

    def _on_alert_clicked(self, alert_type: str, alert_id: int):
        """Handle alert item click - navigate to relevant list screen."""
        target = self.KPI_NAV_MAP.get(alert_type)
        if target:
            self.navigate_to.emit(target)

    def refresh(self):
        """Refresh dashboard data."""
        self._load_data()