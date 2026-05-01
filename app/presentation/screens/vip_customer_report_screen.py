"""VIP customer report screen - S-BC-04 - Top VIP customers report.

Features:
- Top N filter (10, 20, 50, 100)
- Table: Mã KH, Tên KH, Số HĐ, Tổng giá trị mua, Số xe đã mua, Ngày mua gần nhất
- "Gửi tin nhắn chăm sóc" button (mock)
- Export to Excel

References:
- BR-BC-03: Top customers by total purchase value
- RP-04: VIP customer report
"""

from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from app.application.services.bao_cao_service import BaoCaoService
from app.infrastructure.exporters.excel_exporter import ExcelExporter


class VIPCustomerReportScreen(QWidget):
    """VIP customer report screen - S-BC-04."""

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize VIP customer report screen.

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
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Khách hàng VIP")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Care message button
        self._care_btn = QPushButton("📱 Gửi tin nhắn chăm sóc")
        self._care_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9500;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e68600;
            }
        """)
        self._care_btn.clicked.connect(self._on_care_message_clicked)
        header_layout.addWidget(self._care_btn)

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

        # Top N filter
        filter_layout.addWidget(QLabel("Top khách hàng:"))
        self._top_combo = QComboBox()
        self._top_combo.addItems(["10", "20", "50", "100"])
        self._top_combo.setCurrentText("20")
        self._top_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 80px;
                background: white;
            }
        """)
        self._top_combo.currentTextChanged.connect(self._load_data)
        filter_layout.addWidget(self._top_combo)

        filter_layout.addStretch()

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)

        # Top 10 badge
        top10_badge = QLabel("<span style='background:#34c759; color:white; padding:4px 12px; border-radius:12px; font-size:12px;'>🌟 Top 10</span>")
        legend_layout.addWidget(top10_badge)

        # Regular VIP badge
        vip_badge = QLabel("<span style='background:#007aff; color:white; padding:4px 12px; border-radius:12px; font-size:12px;'>⭐ VIP</span>")
        legend_layout.addWidget(vip_badge)

        filter_layout.addLayout(legend_layout)

        layout.addWidget(filter_group)

        # Summary KPIs
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self._kpi_total = self._create_kpi_card("Tổng giá trị mua", "0 đ", "#34c759")
        self._kpi_count = self._create_kpi_card("Số khách hàng", "0", "#007aff")
        self._kpi_avg = self._create_kpi_card("Giá trị trung bình", "0 đ", "#5856d6")

        kpi_layout.addWidget(self._kpi_total)
        kpi_layout.addWidget(self._kpi_count)
        kpi_layout.addWidget(self._kpi_avg)
        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)

        # Data table
        table_label = QLabel("Danh sách khách hàng VIP")
        table_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Mã KH", "Tên khách hàng", "Số điện thoại", "Số HĐ",
            "Tổng giá trị mua", "Số xe đã mua", "Ngày mua gần nhất"
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
        """Load VIP customer report data."""
        top = int(self._top_combo.currentText())

        try:
            result = self._bao_cao_service.vip_customers(top=top)

            # Calculate totals
            total_value = sum(item.get("tong_gia_tri_mua", 0) for item in result)
            customer_count = len(result)
            avg_value = total_value // customer_count if customer_count > 0 else 0

            # Update KPI cards
            self._update_kpi_value(self._kpi_total, f"{total_value:,} đ".replace(",", "."))
            self._update_kpi_value(self._kpi_count, str(customer_count))
            self._update_kpi_value(self._kpi_avg, f"{avg_value:,} đ".replace(",", "."))

            self._current_data = result

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
        """Populate table with VIP customer data."""
        self._table.setRowCount(len(self._current_data))

        for row, item in enumerate(self._current_data):
            khach_hang_id = item.get("khach_hang_id", 0)

            # Mã KH
            item_ma = QTableWidgetItem(f"KH{khach_hang_id:04d}")
            item_ma.setData(Qt.ItemDataRole.UserRole, khach_hang_id)
            item_ma.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, item_ma)

            # Tên KH
            ho_ten = item.get("ho_ten", "")
            self._table.setItem(row, 1, QTableWidgetItem(ho_ten))

            # Số điện thoại
            so_dien_thoai = item.get("so_dien_thoai", "") or "—"
            self._table.setItem(row, 2, QTableWidgetItem(so_dien_thoai))

            # Số HĐ
            so_hd = item.get("so_hop_dong", 0) or 0
            item_hd = QTableWidgetItem(str(so_hd))
            item_hd.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, item_hd)

            # Tổng giá trị mua
            tong_gia_tri = item.get("tong_gia_tri_mua", 0)
            tg_text = f"{tong_gia_tri:,} đ".replace(",", ".")
            item_tg = QTableWidgetItem(tg_text)
            item_tg.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 4, item_tg)

            # Số xe đã mua
            so_xe = item.get("so_xe_da_mua", 0) or 0
            item_xe = QTableWidgetItem(str(so_xe))
            item_xe.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 5, item_xe)

            # Ngày mua gần nhất
            lan_mua_cuoi = item.get("lan_mua_cuoi", "")
            if lan_mua_cuoi:
                ngay_text = lan_mua_cuoi[:10]
            else:
                ngay_text = "—"
            self._table.setItem(row, 6, QTableWidgetItem(ngay_text))

            # Highlight top 10 with green
            if row < 10:
                for col in range(self._table.columnCount()):
                    self._table.item(row, col).setBackground(QColor("#d4edda"))

        # Set column widths
        self._table.setColumnWidth(0, 80)
        self._table.setColumnWidth(2, 130)
        self._table.setColumnWidth(3, 80)
        self._table.setColumnWidth(4, 150)
        self._table.setColumnWidth(5, 100)
        self._table.setColumnWidth(6, 150)

    def _on_row_double_clicked(self, row: int, column: int):
        """Handle row double click - open customer detail."""
        item = self._table.item(row, 0)
        if item:
            kh_id = item.data(Qt.ItemDataRole.UserRole)
            if kh_id:
                # Navigate to customer detail if signal connected
                pass

    def _on_care_message_clicked(self):
        """Handle care message button - mock implementation."""
        selected_rows = self._table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.information(
                self,
                "Thông báo",
                "Vui lòng chọn ít nhất một khách hàng để gửi tin nhắn chăm sóc."
            )
            return

        customer_names = []
        for index in selected_rows:
            row = index.row()
            name_item = self._table.item(row, 1)
            if name_item:
                customer_names.append(name_item.text())

        # In real implementation, this would open a dialog to compose message
        # For now, just log to console and show info
        print(f"[VIP Care] Sending care messages to: {', '.join(customer_names)}")

        QMessageBox.information(
            self,
            "Gửi tin nhắn chăm sóc",
            f"Đã chọn {len(customer_names)} khách hàng:\n\n" +
            "\n".join(f"• {name}" for name in customer_names) +
            "\n\nTính năng gửi tin nhắn đang được phát triển."
        )

    def _export_to_excel(self):
        """Export report to Excel."""
        if not self._current_data:
            QMessageBox.information(self, "Thông báo", "Không có dữ liệu để xuất.")
            return

        try:
            from datetime import datetime

            top = int(self._top_combo.currentText())

            # Prepare sheet config
            sheet_config = {
                "name": f"Top {top} KH VIP",
                "title": f"Top {top} khách hàng VIP",
                "columns": [
                    {"header": "Mã KH", "key": "ma_kh", "width": 10},
                    {"header": "Tên khách hàng", "key": "ho_ten", "width": 25},
                    {"header": "Số điện thoại", "key": "so_dien_thoai", "width": 15},
                    {"header": "Email", "key": "email", "width": 25},
                    {"header": "Số HĐ", "key": "so_hop_dong", "width": 10, "format": "number"},
                    {"header": "Tổng giá trị mua", "key": "tong_gia_tri_mua", "width": 18, "format": "money"},
                    {"header": "Số xe đã mua", "key": "so_xe_da_mua", "width": 12, "format": "number"},
                    {"header": "Ngày mua gần nhất", "key": "lan_mua_cuoi", "width": 15, "format": "date"},
                ],
            }

            # Prepare data
            export_data = []
            for item in self._current_data:
                export_data.append({
                    "ma_kh": f"KH{item.get('khach_hang_id', 0):04d}",
                    "ho_ten": item.get("ho_ten", ""),
                    "so_dien_thoai": item.get("so_dien_thoai", "") or "",
                    "email": item.get("email", "") or "",
                    "so_hop_dong": item.get("so_hop_dong", 0) or 0,
                    "tong_gia_tri_mua": item.get("tong_gia_tri_mua", 0),
                    "so_xe_da_mua": item.get("so_xe_da_mua", 0) or 0,
                    "lan_mua_cuoi": item.get("lan_mua_cuoi", "") or "",
                })

            # Show save dialog
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"kh_vip_top_{top}_{timestamp}.xlsx"

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