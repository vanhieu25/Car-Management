"""Installment progress screen - S-TG-03 - View and manage installment payment progress.

Features:
- Installment details header (ma_hd, khach_hang, ngan_hang, so_tien_vay, lai_suat, so_ky)
- Progress bar showing X/n kỳ đã trả
- Table of all kỳ: ky, ngay_den_han, so_tien, trang_thai (badge)
- "Ghi nhận thanh toán" button on each 'chua_tra' kỳ
- Click button → confirm → update to 'da_tra'
- Red highlight for 'qua_han' kỳ

References:
- BR-TG-04: Record payment updates kỳ to 'da_tra'
- BR-TG-05: All kỳ paid → tra_gop.status = 'hoan_thanh'
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QGroupBox, QProgressBar, QScrollArea, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from app.application.services.tra_gop_service import TraGopService, TraGopDetail, TraGopListItem
from app.application.services.session import CurrentSession


class InstallmentProgressScreen(QWidget):
    """Screen for viewing and managing installment payment progress - S-TG-03.

    Signals:
        back_clicked(): User wants to go back to list.
    """

    back_clicked = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, tra_gop_id: int, parent=None):
        """Initialize installment progress screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            tra_gop_id: TraGop ID to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = TraGopService(db_conn)
        self._tra_gop_id = tra_gop_id

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header with back button
        header_layout = QHBoxLayout()

        self._back_btn = QPushButton("← Quay lại")
        self._back_btn.setStyleSheet("""
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
        self._back_btn.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(self._back_btn)

        header_layout.addStretch()

        title = QLabel("Chi tiết trả góp")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        scroll.setMinimumHeight(600)

        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #f5f5f7;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(24, 24, 24, 24)

        # Installment details header
        details_group = QGroupBox("Thông tin trả góp")
        details_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 16px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
        """)
        details_layout = QHBoxLayout(details_group)
        details_layout.setSpacing(24)

        # Left column - contract info
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)

        self._ma_hd_label = self._create_info_row("Mã HĐ:", "-")
        left_layout.addLayout(self._ma_hd_label)

        self._khach_hang_label = self._create_info_row("Khách hàng:", "-")
        left_layout.addLayout(self._khach_hang_label)

        self._sdt_label = self._create_info_row("SĐT:", "-")
        left_layout.addLayout(self._sdt_label)

        self._xe_label = self._create_info_row("Xe:", "-")
        left_layout.addLayout(self._xe_label)

        details_layout.addLayout(left_layout)

        # Right column - installment info
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)

        self._ngan_hang_label = self._create_info_row("Ngân hàng:", "-")
        right_layout.addLayout(self._ngan_hang_label)

        self._so_tien_vay_label = self._create_info_row("Số tiền vay:", "-")
        right_layout.addLayout(self._so_tien_vay_label)

        self._lai_suat_label = self._create_info_row("Lãi suất:", "-")
        right_layout.addLayout(self._lai_suat_label)

        self._so_ky_label = self._create_info_row("Số kỳ:", "-")
        right_layout.addLayout(self._so_ky_label)

        details_layout.addLayout(right_layout)

        content_layout.addWidget(details_group)

        # Progress section
        progress_group = QGroupBox("Tiến độ trả góp")
        progress_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 16px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
        """)
        progress_layout = QVBoxLayout(progress_group)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #d2d2d7;
                border-radius: 4px;
                text-align: center;
                height: 24px;
            }
            QProgressBar::chunk {
                background-color: #34c759;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self._progress_bar)

        self._progress_label = QLabel("0 / 0 kỳ đã trả")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_label.setStyleSheet("color: #86868b; font-size: 14px;")
        progress_layout.addWidget(self._progress_label)

        content_layout.addWidget(progress_group)

        # Payment schedule table
        schedule_group = QGroupBox("Lịch sử trả góp")
        schedule_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 16px;
                font-weight: 600;
                min-width: 700px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
        """)
        schedule_layout = QVBoxLayout(schedule_group)

        self._schedule_table = QTableWidget()
        self._schedule_table.setColumnCount(4)
        self._schedule_table.setHorizontalHeaderLabels([
            "Kỳ", "Ngày đến hạn", "Số tiền", "Trạng thái"
        ])
        self._schedule_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._schedule_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._schedule_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e5ea;
                border-radius: 6px;
                gridline-color: #e5e5ea;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 10px 8px;
                font-weight: 600;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #0066cc;
                color: white;
            }
        """)
        self._schedule_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self._schedule_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setMinimumSectionSize(120)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._schedule_table.verticalHeader().setVisible(False)
        self._schedule_table.setMinimumHeight(400)
        self._schedule_table.itemSelectionChanged.connect(self._on_selection_changed)
        schedule_layout.addWidget(self._schedule_table)

        # Payment button below table
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._pay_btn = QPushButton("💰 Ghi nhận thanh toán")
        self._pay_btn.setEnabled(False)
        self._pay_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
            QPushButton:disabled {
                background-color: #d2d2d7;
                color: #86868b;
            }
        """)
        self._pay_btn.clicked.connect(self._on_pay_clicked)
        btn_layout.addWidget(self._pay_btn)
        schedule_layout.addLayout(btn_layout)

        content_layout.addWidget(schedule_group)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def _create_info_row(self, label_text: str, value: str) -> QHBoxLayout:
        """Create a label-value info row.

        Args:
            label_text: Label text.
            value: Initial value.

        Returns:
            QHBoxLayout with label and value.
        """
        layout = QHBoxLayout()
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setStyleSheet("color: #86868b; min-width: 100px;")
        layout.addWidget(label)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-weight: 500; color: #1d1d1f;")
        layout.addWidget(value_label)

        layout.addStretch()

        return layout

    def _on_back_clicked(self):
        """Handle back button click."""
        self.back_clicked.emit()

    def _load_data(self):
        """Load installment data and populate UI."""
        try:
            detail = self._service.get_detail(self._tra_gop_id)
            if not detail:
                QMessageBox.critical(self, "Lỗi", "Không tìm thấy thông tin trả góp")
                self._on_back_clicked()
                return

            self._populate_details(detail)
            self._populate_schedule(detail)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_details(self, detail: TraGopDetail):
        """Populate the details section.

        Args:
            detail: TraGopDetail with installment info.
        """
        tg = detail.tra_gop

        self._ma_hd_label.itemAt(1).widget().setText(detail.ma_hop_dong)
        self._khach_hang_label.itemAt(1).widget().setText(detail.khach_hang_ten)
        self._sdt_label.itemAt(1).widget().setText(detail.so_dien_thoai or "-")
        self._xe_label.itemAt(1).widget().setText(f"{detail.xe_hang} {detail.xe_dong}")

        self._ngan_hang_label.itemAt(1).widget().setText(tg.ngan_hang)
        self._so_tien_vay_label.itemAt(1).widget().setText(
            f"{tg.so_tien_vay:,} đ".replace(",", ".")
        )
        self._lai_suat_label.itemAt(1).widget().setText(f"{tg.lai_suat_nam:.2f}%")
        self._so_ky_label.itemAt(1).widget().setText(f"{tg.so_ky} tháng")

    def _populate_schedule(self, detail: TraGopDetail):
        """Populate the payment schedule table.

        Args:
            detail: TraGopDetail with payment history.
        """
        tg = detail.tra_gop
        lich_su_list = detail.lich_su_list

        total = len(lich_su_list)
        da_tra = sum(1 for ls in lich_su_list if ls.trang_thai == "da_tra")
        qua_han = sum(1 for ls in lich_su_list if ls.trang_thai == "qua_han")

        # Update progress bar
        if total > 0:
            pct = int(da_tra / total * 100)
        else:
            pct = 0

        self._progress_bar.setValue(pct)
        self._progress_label.setText(f"{da_tra} / {total} kỳ đã trả ({pct}%)")

        # Populate table
        self._schedule_table.setRowCount(len(lich_su_list))

        status_colors = {
            "chua_tra": "#8e8e93",    # Gray
            "da_tra": "#34c759",      # Green
            "qua_han": "#ff3b30",     # Red
        }

        status_labels = {
            "chua_tra": "Chưa trả",
            "da_tra": "Đã trả",
            "qua_han": "Quá hạn",
        }

        for row, ls in enumerate(lich_su_list):
            # Kỳ
            self._schedule_table.setItem(row, 0, QTableWidgetItem(str(ls.ky_thu)))

            # Ngày đến hạn
            ngay_den_han = ls.ngay_den_han[:10] if ls.ngay_den_han else "-"
            self._schedule_table.setItem(row, 1, QTableWidgetItem(ngay_den_han))

            # Số tiền
            tien_text = f"{ls.so_tien_phai_tra:,} đ".replace(",", ".")
            item_tien = QTableWidgetItem(tien_text)
            item_tien.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self._schedule_table.setItem(row, 2, item_tien)

            # Trạng thái
            status_text = status_labels.get(ls.trang_thai, ls.trang_thai)
            item_status = QTableWidgetItem(status_text)
            color_hex = status_colors.get(ls.trang_thai, "#8e8e93")
            item_status.setBackground(QColor(color_hex))
            item_status.setForeground(QColor(255, 255, 255))
            item_status.setData(Qt.ItemDataRole.UserRole, ls.id)
            item_status.setData(Qt.ItemDataRole.UserRole + 1, ls.trang_thai)
            self._schedule_table.setItem(row, 3, item_status)

        # Store lich_su list for reference
        self._lich_su_list = lich_su_list
        self._selected_lich_su_id = None
        self._pay_btn.setEnabled(False)

    def _on_selection_changed(self):
        """Handle row selection change."""
        selected = self._schedule_table.selectedItems()
        if not selected:
            self._pay_btn.setEnabled(False)
            self._selected_lich_su_id = None
            return

        # Get the selected row
        row = selected[0].row()
        item = self._schedule_table.item(row, 3)
        if item:
            ls_id = item.data(Qt.ItemDataRole.UserRole)
            status = item.data(Qt.ItemDataRole.UserRole + 1)
            if status == "chua_tra":
                self._selected_lich_su_id = ls_id
                self._pay_btn.setEnabled(True)
            else:
                self._selected_lich_su_id = None
                self._pay_btn.setEnabled(False)

    def _on_pay_clicked(self):
        """Handle pay button click."""
        if not self._selected_lich_su_id:
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận thanh toán",
            "Bạn có chắc chắn muốn ghi nhận thanh toán cho kỳ này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.record_payment(
                lich_su_id=self._selected_lich_su_id,
                nhan_vien_id=self._session.nhan_vien_id if self._session else None,
            )
            QMessageBox.information(self, "Thành công", "Đã ghi nhận thanh toán thành công!")
            self._schedule_table.clearSelection()
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể ghi nhận thanh toán: {str(e)}")

    def refresh(self):
        """Refresh the data."""
        self._load_data()
