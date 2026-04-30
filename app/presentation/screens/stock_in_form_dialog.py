"""Stock-in form dialog - S-KHO-02 - Import inventory form.

Features:
- Form for stock-in (nhập kho) operations
- Item list with add/remove capability
- Recent stock-in history
- Toast notification on success

References:
- UC-KHO-02: Nhập kho
"""

from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QComboBox,
    QSpinBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from app.application.services.nhap_kho_service import NhapKhoService
from app.application.services.kho_service import KhoService
from app.application.services.session import CurrentSession


class StockInFormDialog(QDialog):
    """Dialog for stock-in operations - S-KHO-02.
    
    Signals:
        saved: Emitted when stock-in was saved successfully.
    """
    
    saved = pyqtSignal()
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize stock-in form dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._nhap_kho_service = NhapKhoService(db_conn)
        self._kho_service = KhoService(db_conn)
        self._items: List[Dict[str, Any]] = []
        
        self._setup_ui()
        self._load_nha_cung_cap()
        self._load_recent_history()
    
    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Nhập kho")
        self.setMinimumSize(700, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                font-size: 14px;
                color: #1d1d1f;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Toast notification (hidden by default)
        self._toast_label = QLabel("")
        self._toast_label.setStyleSheet("""
            background-color: #e8f5e9;
            color: #2e7d32;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
        """)
        self._toast_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._toast_label.setVisible(False)
        layout.addWidget(self._toast_label)
        
        # Form group
        form_group = QGroupBox("Thông tin nhập kho")
        form_group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 16px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
        """)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        
        # Row 1: Nha cung cap + Loai item
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(12)
        
        # Nha cung cap
        ncc_layout = QVBoxLayout()
        ncc_layout.setSpacing(4)
        
        ncc_label = QLabel("Nhà cung cấp *:")
        ncc_label.setStyleSheet("font-weight: 500;")
        ncc_layout.addWidget(ncc_label)
        
        self._ncc_combo = QComboBox()
        self._ncc_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 200px;
            }
            QComboBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        ncc_layout.addWidget(self._ncc_combo)
        
        row1_layout.addLayout(ncc_layout)
        
        # Loai item
        loai_layout = QVBoxLayout()
        loai_layout.setSpacing(4)
        
        loai_label = QLabel("Loại item *:")
        loai_label.setStyleSheet("font-weight: 500;")
        loai_layout.addWidget(loai_label)
        
        self._loai_combo = QComboBox()
        self._loai_combo.addItems(["Xe", "Phụ kiện"])
        self._loai_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 120px;
            }
            QComboBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        self._loai_combo.currentTextChanged.connect(self._on_loai_changed)
        loai_layout.addWidget(self._loai_combo)
        
        row1_layout.addLayout(loai_layout)
        
        form_layout.addLayout(row1_layout)
        
        # Row 2: Item + So luong
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(12)
        
        # Item
        item_layout = QVBoxLayout()
        item_layout.setSpacing(4)
        
        item_label = QLabel("Item *:")
        item_label.setStyleSheet("font-weight: 500;")
        item_layout.addWidget(item_label)
        
        self._item_combo = QComboBox()
        self._item_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 200px;
            }
            QComboBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        item_layout.addWidget(self._item_combo)
        
        row2_layout.addLayout(item_layout)
        
        # So luong
        sl_layout = QVBoxLayout()
        sl_layout.setSpacing(4)
        
        sl_label = QLabel("Số lượng *:")
        sl_label.setStyleSheet("font-weight: 500;")
        sl_layout.addWidget(sl_label)
        
        self._so_luong_spin = QSpinBox()
        self._so_luong_spin.setMinimum(1)
        self._so_luong_spin.setValue(1)
        self._so_luong_spin.setStyleSheet("""
            QSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 100px;
            }
            QSpinBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        sl_layout.addWidget(self._so_luong_spin)
        
        row2_layout.addLayout(sl_layout)
        
        # Gia nhap
        gia_layout = QVBoxLayout()
        gia_layout.setSpacing(4)
        
        gia_label = QLabel("Giá nhập *:")
        gia_label.setStyleSheet("font-weight: 500;")
        gia_layout.addWidget(gia_label)
        
        self._gia_nhap_spin = QSpinBox()
        self._gia_nhap_spin.setMinimum(0)
        self._gia_nhap_spin.setValue(0)
        self._gia_nhap_spin.setSingleStep(1000000)
        self._gia_nhap_spin.setStyleSheet("""
            QSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 150px;
            }
            QSpinBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        gia_layout.addWidget(self._gia_nhap_spin)
        
        row2_layout.addLayout(gia_layout)
        
        form_layout.addLayout(row2_layout)
        
        # Row 3: Ngay nhap + Ghi chu
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(12)
        
        # Ngay nhap
        ngay_layout = QVBoxLayout()
        ngay_layout.setSpacing(4)
        
        ngay_label = QLabel("Ngày nhập *:")
        ngay_label.setStyleSheet("font-weight: 500;")
        ngay_layout.addWidget(ngay_label)
        
        self._ngay_nhap_edit = QDateEdit()
        self._ngay_nhap_edit.setCalendarPopup(True)
        self._ngay_nhap_edit.setDate(self._ngay_nhap_edit.date().currentDate())
        self._ngay_nhap_edit.setStyleSheet("""
            QDateEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 150px;
            }
            QDateEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        ngay_layout.addWidget(self._ngay_nhap_edit)
        
        row3_layout.addLayout(ngay_layout)
        
        # Ghi chu
        ghichu_layout = QVBoxLayout()
        ghichu_layout.setSpacing(4)
        
        ghichu_label = QLabel("Ghi chú:")
        ghichu_label.setStyleSheet("font-weight: 500;")
        ghichu_layout.addWidget(ghichu_label)
        
        self._ghi_chu_input = QLineEdit()
        self._ghi_chu_input.setPlaceholderText("VD: Nhập hàng tháng...")
        self._ghi_chu_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        ghichu_layout.addWidget(self._ghi_chu_input)
        
        row3_layout.addLayout(ghichu_layout)
        
        form_layout.addLayout(row3_layout)
        
        # Add item button
        self._add_item_btn = QPushButton("➕ Thêm item")
        self._add_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
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
        self._add_item_btn.clicked.connect(self._on_add_item)
        form_layout.addWidget(self._add_item_btn)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Items table
        items_group = QGroupBox("Danh sách items đã thêm")
        items_group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 16px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
        """)
        items_layout = QVBoxLayout()
        items_layout.setSpacing(8)
        
        self._items_table = QTableWidget()
        self._items_table.setColumnCount(5)
        self._items_table.setHorizontalHeaderLabels([
            "Loại", "Item", "Số lượng", "Giá nhập", "Thành tiền"
        ])
        self._items_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background: white;
            }
            QHeaderView::section {
                background: #f5f5f7;
                padding: 8px;
                font-weight: 600;
                font-size: 13px;
            }
        """)
        self._items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._items_table.setColumnWidth(0, 80)   # Loai
        self._items_table.setColumnWidth(1, 200)  # Item
        self._items_table.setColumnWidth(2, 80)   # So luong
        self._items_table.setColumnWidth(3, 120)  # Gia nhap
        self._items_table.setColumnWidth(4, 120)  # Thanh tien
        items_layout.addWidget(self._items_table)
        
        items_group.setLayout(items_layout)
        layout.addWidget(items_group)
        
        # Recent history table
        history_group = QGroupBox("Lịch sử nhập kho gần nhất")
        history_group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 16px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
        """)
        history_layout = QVBoxLayout()
        history_layout.setSpacing(8)
        
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(4)
        self._history_table.setHorizontalHeaderLabels([
            "Ngày", "NCC", "Số items", "Tổng giá trị"
        ])
        self._history_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background: white;
            }
            QHeaderView::section {
                background: #f5f5f7;
                padding: 8px;
                font-weight: 600;
                font-size: 13px;
            }
        """)
        self._history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self._history_table)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._cancel_btn = QPushButton("Hủy bỏ")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)
        
        self._submit_btn = QPushButton("📥 Nhập kho")
        self._submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._submit_btn.clicked.connect(self._on_submit)
        btn_layout.addWidget(self._submit_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_nha_cung_cap(self):
        """Load nha cung cap into combo box."""
        try:
            ncc_list = self._nhap_kho_service.get_nha_cung_cap_list()
            self._ncc_combo.clear()
            for ncc in ncc_list:
                self._ncc_combo.addItem(ncc["ten_ncc"], ncc["id"])
        except Exception as e:
            QMessageBox.warning(self, "Cảnh báo", f"Không thể tải danh sách NCC: {str(e)}")
    
    def _load_items_by_loai(self, loai: str):
        """Load items based on loai (Xe or Phu kien).
        
        Args:
            loai: Item type ('Xe' or 'Phụ kiện').
        """
        try:
            items = self._kho_service.get_items_by_loai(loai)
            self._item_combo.clear()
            for item in items:
                display_text = f"{item.get('ma', '')} - {item.get('ten', '')}"
                self._item_combo.addItem(display_text, item.get("id"))
        except Exception as e:
            QMessageBox.warning(self, "Cảnh báo", f"Không thể tải danh sách items: {str(e)}")
    
    def _load_recent_history(self):
        """Load recent stock-in history (last 10 records)."""
        try:
            history = self._nhap_kho_service.get_recent_history(limit=10)
            self._history_table.setRowCount(len(history))
            
            for i, record in enumerate(history):
                # Ngay
                ngay = record.get("ngay_nhap", "-")
                if ngay and len(ngay) > 10:
                    ngay = ngay[:10]
                self._history_table.setItem(i, 0, QTableWidgetItem(ngay))
                
                # NCC
                self._history_table.setItem(i, 1, QTableWidgetItem(record.get("ten_ncc", "-")))
                
                # So items
                self._history_table.setItem(i, 2, QTableWidgetItem(str(record.get("so_items", 0))))
                
                # Tong gia tri
                tong_gia = record.get("tong_gia_tri", 0)
                self._history_table.setItem(i, 3, QTableWidgetItem(
                    f"{tong_gia:,.0f} đ".replace(",", ".")
                ))
                
        except Exception as e:
            # Silently fail for history table
            pass
    
    def _on_loai_changed(self, text: str):
        """Handle loai item change.
        
        Args:
            text: Selected loai text.
        """
        loai = "Xe" if text == "Xe" else "PhuKien"
        self._load_items_by_loai(loai)
    
    def _on_add_item(self):
        """Handle add item button click."""
        ncc_id = self._ncc_combo.currentData()
        if ncc_id is None:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn nhà cung cấp!")
            return
        
        item_id = self._item_combo.currentData()
        if item_id is None:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn item!")
            return
        
        loai_text = self._loai_combo.currentText()
        loai = "Xe" if loai_text == "Xe" else "PhuKien"
        item_text = self._item_combo.currentText()
        so_luong = self._so_luong_spin.value()
        gia_nhap = self._gia_nhap_spin.value()
        thanh_tien = so_luong * gia_nhap
        
        # Add to items list
        item_entry = {
            "loai": loai,
            "loai_text": loai_text,
            "item_id": item_id,
            "item_text": item_text,
            "so_luong": so_luong,
            "gia_nhap": gia_nhap,
            "thanh_tien": thanh_tien,
        }
        self._items.append(item_entry)
        
        # Update table
        row = self._items_table.rowCount()
        self._items_table.insertRow(row)
        
        self._items_table.setItem(row, 0, QTableWidgetItem(loai_text))
        self._items_table.setItem(row, 1, QTableWidgetItem(item_text))
        
        item_sl = QTableWidgetItem(str(so_luong))
        item_sl.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self._items_table.setItem(row, 2, item_sl)
        
        item_gia = QTableWidgetItem(f"{gia_nhap:,.0f} đ".replace(",", "."))
        item_gia.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._items_table.setItem(row, 3, item_gia)
        
        item_tt = QTableWidgetItem(f"{thanh_tien:,.0f} đ".replace(",", "."))
        item_tt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._items_table.setItem(row, 4, item_tt)
        
        # Add delete button column
        delete_btn = QPushButton("🗑️ Xóa")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.clicked.connect(lambda: self._on_delete_item(row))
        self._items_table.setCellWidget(row, 4, delete_btn)
        
        # Reset form for next item
        self._so_luong_spin.setValue(1)
        self._gia_nhap_spin.setValue(0)
    
    def _on_delete_item(self, row: int):
        """Handle delete item button click.
        
        Args:
            row: Row index to delete.
        """
        if row < len(self._items):
            self._items.pop(row)
            self._items_table.removeRow(row)
    
    def _show_toast(self, message: str, is_success: bool = True):
        """Show toast notification.
        
        Args:
            message: Message to display.
            is_success: True for success (green), False for error (red).
        """
        if is_success:
            self._toast_label.setStyleSheet("""
                background-color: #e8f5e9;
                color: #2e7d32;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            """)
        else:
            self._toast_label.setStyleSheet("""
                background-color: #ffebee;
                color: #c62828;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            """)
        
        self._toast_label.setText(message)
        self._toast_label.setVisible(True)
        
        # Hide after 5 seconds
        QTimer.singleShot(5000, lambda: self._toast_label.setVisible(False))
    
    def _on_submit(self):
        """Handle submit (Nhập kho) button click."""
        if not self._items:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng thêm ít nhất một item!")
            return
        
        ncc_id = self._ncc_combo.currentData()
        if ncc_id is None:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn nhà cung cấp!")
            return
        
        ngay_nhap = self._ngay_nhap_edit.date().toString("yyyy-MM-dd")
        ghi_chu = self._ghi_chu_input.text().strip()
        
        try:
            # Prepare data for NhapKhoService.create()
            nhan_vien_id = self._session.nhan_vien_id if self._session else None
            
            result = self._nhap_kho_service.create(
                nha_cung_cap_id=ncc_id,
                nhan_vien_id=nhan_vien_id,
                ngay_nhap=ngay_nhap,
                ghi_chu=ghi_chu,
                items=self._items,
            )
            
            # Show success toast
            ton_moi = result.get("ton_moi", "N/A")
            self._show_toast(f"Đã nhập kho thành công! Tồn mới: {ton_moi}", is_success=True)
            
            # Reload history
            self._load_recent_history()
            
            # Emit saved signal and close after delay
            QTimer.singleShot(1500, self._on_saved_and_close)
            
        except Exception as e:
            self._show_toast(f"Lỗi: {str(e)}", is_success=False)
            QMessageBox.critical(self, "Lỗi", f"Không thể nhập kho: {str(e)}")
    
    def _on_saved_and_close(self):
        """Handle successful save and close."""
        self.saved.emit()
        self.accept()
