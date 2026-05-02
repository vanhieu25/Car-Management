"""Order form dialog - S-NCC-03 - Create/Edit purchase orders.

Features:
- Select NCC (dropdown)
- Add items: xe or phu_kien, quantity, unit price
- Preview total price
- Submit creates order

References:
- BR-NCC-04: Create order with status 'cho_xu_ly'
- BR-NCC-05: set_received creates nhap_kho
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox,
    QDialog, QMessageBox, QFormLayout,
    QGroupBox, QScrollArea, QLineEdit, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.presentation.widgets.inputs import InlineNumericEdit

from app.application.services.don_dat_hang_service import (
    DonDatHangService,
    DonDatHangItemData,
    DonDatHangCreateData,
    DonDatHangServiceError,
)
from app.application.services.nha_cung_cap_service import NhaCungCapService
from app.application.services.session import CurrentSession


class OrderFormDialog(QDialog):
    """Dialog for creating/editing purchase orders.

    Signals:
        order_created(order: dict): Order was successfully created.
        cancelled(): User cancelled the operation.
    """

    order_created = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, parent=None, order_id: int = None):
        """Initialize order form dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
            order_id: If provided, edit existing order. If None, create new.
        """
        super().__init__(parent)
        self.setWindowTitle("Tạo đơn đặt hàng mới" if order_id is None else "Chỉnh sửa đơn đặt hàng")
        self.setMinimumSize(700, 500)
        self._db_conn = db_conn
        self._session = session
        self._order_id = order_id

        self._ddh_service = DonDatHangService(db_conn)
        self._ncc_service = NhaCungCapService(db_conn)

        # Get available items (xe and phu_kien)
        self._available_xe = self._get_available_xe()
        self._available_phu_kien = self._get_available_phu_kien()

        # Order items
        self._items: List[dict] = []

        self._setup_ui()
        self._load_ncc_list()

        if order_id:
            self._load_order(order_id)

    def _get_available_xe(self) -> List[dict]:
        """Get list of available xe for ordering."""
        cursor = self._db_conn.execute(
            """SELECT id, ma_xe, hang, dong_xe, gia_ban FROM xe 
               WHERE trang_thai = 'con_hang' ORDER BY ma_xe"""
        )
        return [dict(row) for row in cursor.fetchall()]

    def _get_available_phu_kien(self) -> List[dict]:
        """Get list of available phu_kien for ordering."""
        cursor = self._db_conn.execute(
            """SELECT id, ma_pk, ten_pk, gia_ban FROM phu_kien 
               WHERE ton_kho > 0 ORDER BY ten_pk"""
        )
        return [dict(row) for row in cursor.fetchall()]

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Supplier selection
        supplier_group = QGroupBox("Nhà cung cấp")
        supplier_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 12px;
                margin-top: 4px;
            }
        """)
        supplier_layout = QHBoxLayout(supplier_group)

        supplier_layout.addWidget(QLabel("Chọn nhà cung cấp:"))

        self._ncc_combo = QComboBox()
        self._ncc_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 300px;
                background: white;
            }
        """)
        supplier_layout.addWidget(self._ncc_combo, stretch=1)

        layout.addWidget(supplier_group)

        # Items section
        items_group = QGroupBox("Danh sách items")
        items_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 12px;
                margin-top: 4px;
            }
        """)
        items_layout = QVBoxLayout(items_group)

        # Add item row
        add_item_layout = QHBoxLayout()
        add_item_layout.setSpacing(12)

        self._item_type_combo = QComboBox()
        self._item_type_combo.addItems(["Xe", "Phụ kiện"])
        self._item_type_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 100px;
                background: white;
            }
        """)
        self._item_type_combo.currentIndexChanged.connect(self._on_item_type_changed)
        add_item_layout.addWidget(self._item_type_combo)

        self._item_combo = QComboBox()
        self._item_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 250px;
                background: white;
            }
        """)
        add_item_layout.addWidget(self._item_combo)

        self._quantity_spin = InlineNumericEdit(
            value=1,
            minimum=1,
            maximum=100,
            step=1,
            is_float=False,
        )
        add_item_layout.addWidget(self._quantity_spin)

        self._price_spin = InlineNumericEdit(
            value=0,
            minimum=0,
            maximum=999999999,
            step=100000,
            suffix="đ",
            is_float=False,
        )
        add_item_layout.addWidget(self._price_spin)

        add_btn = QPushButton("➕ Thêm")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
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
        add_btn.clicked.connect(self._on_add_item)
        add_item_layout.addWidget(add_btn)

        items_layout.addLayout(add_item_layout)

        # Items table
        self._items_table = QTableWidget()
        self._items_table.setColumnCount(6)
        self._items_table.setHorizontalHeaderLabels([
            "Loại", "Mã/Tên", "Số lượng", "Đơn giá", "Thành tiền", "Xóa"
        ])
        self._items_table.setStyleSheet("""
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
                padding: 8px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
        """)
        self._items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        items_layout.addWidget(self._items_table)

        layout.addWidget(items_group)

        # Total preview
        total_group = QGroupBox("Tổng cộng")
        total_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 12px;
                margin-top: 4px;
            }
        """)
        total_layout = QHBoxLayout(total_group)

        self._total_label = QLabel("0 đ")
        self._total_label.setStyleSheet("font-size: 24px; font-weight: 600; color: #34c759;")
        total_layout.addWidget(self._total_label)

        total_layout.addStretch()

        layout.addWidget(total_group)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Hủy bỏ")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        cancel_btn.clicked.connect(self._on_cancel)
        buttons_layout.addWidget(cancel_btn)

        self._submit_btn = QPushButton("💾 Tạo đơn đặt hàng")
        self._submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._submit_btn.clicked.connect(self._on_submit)
        buttons_layout.addWidget(self._submit_btn)

        layout.addLayout(buttons_layout)

        # Initial item type
        self._on_item_type_changed(0)

    def _load_ncc_list(self):
        """Load supplier list into combo."""
        try:
            result = self._ncc_service.search(page_size=1000)
            self._ncc_list = result.items

            self._ncc_combo.clear()
            for ncc in self._ncc_list:
                self._ncc_combo.addItem(ncc["ten_ncc"], ncc["id"])

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải danh sách nhà cung cấp: {str(e)}")

    def _on_item_type_changed(self, index: int):
        """Handle item type change."""
        self._item_combo.clear()

        if index == 0:  # Xe
            for xe in self._available_xe:
                text = f"{xe['ma_xe']} - {xe['hang']} {xe['dong_xe']}"
                self._item_combo.addItem(text, xe["id"])
            if self._available_xe:
                self._price_spin.setValue(self._available_xe[0]["gia_ban"])
        else:  # Phu kien
            for pk in self._available_phu_kien:
                text = f"{pk['ma_pk']} - {pk['ten_pk']}"
                self._item_combo.addItem(text, pk["id"])
            if self._available_phu_kien:
                self._price_spin.setValue(self._available_phu_kien[0]["gia_ban"])

    def _on_add_item(self):
        """Handle add item button."""
        item_id = self._item_combo.currentData()
        if item_id is None:
            return

        loai_item = "xe" if self._item_type_combo.currentIndex() == 0 else "phu_kien"
        item_text = self._item_combo.currentText()
        so_luong = self._quantity_spin.value()
        gia_don = int(self._price_spin.value())

        if so_luong <= 0:
            QMessageBox.warning(self, "Lỗi", "Số lượng phải > 0")
            return

        if gia_don < 0:
            QMessageBox.warning(self, "Lỗi", "Đơn giá không được âm")
            return

        # Check if item already exists
        for i, item in enumerate(self._items):
            if item["item_id"] == item_id and item["loai_item"] == loai_item:
                # Update quantity and price
                self._items[i]["so_luong"] += so_luong
                self._items[i]["gia_don"] = gia_don
                self._refresh_items_table()
                return

        # Add new item
        self._items.append({
            "loai_item": loai_item,
            "item_id": item_id,
            "item_text": item_text,
            "so_luong": so_luong,
            "gia_don": gia_don,
        })

        self._refresh_items_table()

    def _refresh_items_table(self):
        """Refresh the items table."""
        self._items_table.setRowCount(len(self._items))

        total = 0
        for row, item in enumerate(self._items):
            loai_text = "Xe" if item["loai_item"] == "xe" else "Phụ kiện"
            thanh_tien = item["so_luong"] * item["gia_don"]
            total += thanh_tien

            self._items_table.setItem(row, 0, QTableWidgetItem(loai_text))
            self._items_table.setItem(row, 1, QTableWidgetItem(item["item_text"]))
            self._items_table.setItem(row, 2, QTableWidgetItem(str(item["so_luong"])))

            gia_text = f"{item['gia_don']:,}".replace(",", ".")
            self._items_table.setItem(row, 3, QTableWidgetItem(gia_text))

            thanh_text = f"{thanh_tien:,}".replace(",", ".")
            item_thanh = QTableWidgetItem(thanh_text)
            item_thanh.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self._items_table.setItem(row, 4, item_thanh)

            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff3b30;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #d63030;
                }
            """)
            delete_btn.clicked.connect(lambda _, r=row: self._on_delete_item(r))
            self._items_table.setCellWidget(row, 5, delete_btn)

        # Update total
        total_text = f"{total:,}".replace(",", ".")
        self._total_label.setText(f"{total_text} đ")
        self._total_label.setStyleSheet("font-size: 24px; font-weight: 600; color: #34c759;")

    def _on_delete_item(self, row: int):
        """Handle delete item button."""
        if 0 <= row < len(self._items):
            del self._items[row]
            self._refresh_items_table()

    def _load_order(self, order_id: int):
        """Load existing order for editing."""
        # TODO: Implement if needed
        pass

    def _on_cancel(self):
        """Handle cancel button."""
        self.cancelled.emit()
        self.reject()

    def _on_submit(self):
        """Handle submit button."""
        ncc_id = self._ncc_combo.currentData()
        if ncc_id is None:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn nhà cung cấp")
            return

        if not self._items:
            QMessageBox.warning(self, "Lỗi", "Vui lòng thêm ít nhất 1 item")
            return

        try:
            # Build items data
            items_data = []
            for item in self._items:
                items_data.append(DonDatHangItemData(
                    loai_item=item["loai_item"],
                    item_id=item["item_id"],
                    so_luong=item["so_luong"],
                    gia_don=item["gia_don"],
                ))

            create_data = DonDatHangCreateData(
                nha_cung_cap_id=ncc_id,
                items=items_data,
            )

            order = self._ddh_service.create(create_data)

            QMessageBox.information(self, "Thành công", f"Đơn đặt hàng '{order['ma_don']}' đã được tạo!")

            self.order_created.emit(order)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo đơn đặt hàng: {str(e)}")