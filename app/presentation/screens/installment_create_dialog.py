"""Installment create dialog - S-TG-02 - Create installment plan.

Features:
- Select hop_dong (dropdown of contracts without installment)
- Input: ngan_hang, so_tien_vay, lai_suat_nam (slider 0-30%), so_ky (slider 6-84)
- Live preview: show M calculated in real-time as user adjusts values
- Preview full schedule: table of all n kỳ with dates and amounts
- Confirm button → create installment

References:
- BR-TG-01: UNIQUE hop_dong_id
- BR-TG-02: P <= hop_dong.tong_tien
- BR-CALC-04: M = P × r × (1+r)^n / ((1+r)^n − 1)
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox, QLineEdit,
    QHeaderView, QMessageBox, QDialog, QScrollArea, QGroupBox,
    QFormLayout, QDoubleSpinBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.application.services.tra_gop_service import TraGopService, ValidationError
from app.application.services.hop_dong_service import HopDongService
from app.application.services.session import CurrentSession


class InstallmentCreateDialog(QDialog):
    """Dialog for creating a new installment plan - S-TG-02.

    Signals:
        created(tra_gop_id: int): Installment was created successfully.
    """

    created = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize installment create dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._tg_service = TraGopService(db_conn)
        self._hd_service = HopDongService(db_conn)

        self.setWindowTitle("Tạo phương án trả góp")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
            }
        """)

        self._setup_ui()
        self._load_contracts()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Tạo phương án trả góp")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(title)

        # Contract selection
        contract_group = QGroupBox("Thông tin hợp đồng")
        contract_group.setStyleSheet("""
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
        contract_layout = QFormLayout(contract_group)

        self._contract_combo = QComboBox()
        self._contract_combo.setPlaceholderText("Chọn hợp đồng...")
        self._contract_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 300px;
                background: white;
            }
        """)
        self._contract_combo.currentIndexChanged.connect(self._on_contract_changed)
        contract_layout.addRow("Hợp đồng:", self._contract_combo)

        self._contract_info_label = QLabel("Chưa chọn hợp đồng")
        self._contract_info_label.setStyleSheet("color: #86868b; font-size: 13px;")
        contract_layout.addRow("", self._contract_info_label)

        layout.addWidget(contract_group)

        # Installment parameters
        params_group = QGroupBox("Thông tin trả góp")
        params_group.setStyleSheet("""
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
        params_layout = QFormLayout(params_group)

        # Bank
        self._bank_input = QLineEdit()
        self._bank_input.setPlaceholderText("Tên ngân hàng...")
        self._bank_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 200px;
            }
        """)
        params_layout.addRow("Ngân hàng:", self._bank_input)

        # Loan amount
        self._amount_input = QSpinBox()
        self._amount_input.setRange(0, 100000000000)
        self._amount_input.setSuffix(" đ")
        self._amount_input.setStyleSheet("""
            QSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 200px;
            }
        """)
        self._amount_input.valueChanged.connect(self._on_params_changed)
        params_layout.addRow("Số tiền vay:", self._amount_input)

        # Interest rate slider
        rate_layout = QHBoxLayout()
        self._rate_slider = QSpinBox()
        self._rate_slider.setRange(0, 30)
        self._rate_slider.setSuffix(" %")
        self._rate_slider.setStyleSheet("""
            QSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 80px;
            }
        """)
        self._rate_slider.valueChanged.connect(self._on_params_changed)
        rate_layout.addWidget(self._rate_slider)
        rate_layout.addWidget(QLabel("Lãi suất năm"))

        self._rate_slider.valueChanged.connect(self._on_params_changed)
        params_layout.addRow("Lãi suất:", self._rate_slider)

        # Months slider
        self._months_slider = QSpinBox()
        self._months_slider.setRange(6, 84)
        self._months_slider.setSuffix(" tháng")
        self._months_slider.setStyleSheet("""
            QSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 80px;
            }
        """)
        self._months_slider.valueChanged.connect(self._on_params_changed)
        params_layout.addRow("Số kỳ trả:", self._months_slider)

        layout.addWidget(params_group)

        # Live preview
        preview_group = QGroupBox("Xem trước")
        preview_group.setStyleSheet("""
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
        preview_layout = QVBoxLayout(preview_group)

        # Monthly payment preview
        self._monthly_payment_label = QLabel("0 đ")
        self._monthly_payment_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #007aff;
            padding: 8px 0;
        """)
        self._monthly_payment_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self._monthly_payment_label)

        preview_note = QLabel("Số tiền trả hàng tháng")
        preview_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_note.setStyleSheet("color: #86868b; font-size: 13px;")
        preview_layout.addWidget(preview_note)

        # Schedule table
        self._schedule_table = QTableWidget()
        self._schedule_table.setColumnCount(4)
        self._schedule_table.setHorizontalHeaderLabels([
            "Kỳ", "Ngày đến hạn", "Số tiền", "Trạng thái"
        ])
        self._schedule_table.setMaximumHeight(200)
        self._schedule_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e5ea;
                border-radius: 6px;
                gridline-color: #e5e5ea;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 8px;
                font-weight: 600;
            }
        """)
        self._schedule_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self._schedule_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        preview_layout.addWidget(self._schedule_table)

        layout.addWidget(preview_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_btn = QPushButton("Hủy")
        self._cancel_btn.setStyleSheet("""
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
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        self._confirm_btn = QPushButton("✅ Xác nhận tạo")
        self._confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._confirm_btn.clicked.connect(self._on_confirm)
        self._confirm_btn.setEnabled(False)
        button_layout.addWidget(self._confirm_btn)

        layout.addLayout(button_layout)

    def _load_contracts(self):
        """Load contracts eligible for installment (da_thanh_toan or da_giao_xe, no existing installment)."""
        self._contract_combo.clear()
        self._contract_combo.addItem("Chọn hợp đồng...", None)

        try:
            # Get contracts that are paid/delivered and don't have installment
            cursor = self._db_conn.execute("""
                SELECT hd.id, hd.ma_hop_dong, kh.ho_ten, xe.hang, xe.dong_xe, hd.tong_tien
                FROM hop_dong hd
                JOIN khach_hang kh ON hd.khach_hang_id = kh.id
                JOIN xe ON hd.xe_id = xe.id
                LEFT JOIN tra_gop tg ON tg.hop_dong_id = hd.id
                WHERE tg.id IS NULL
                  AND hd.trang_thai IN ('da_thanh_toan', 'da_giao_xe')
                ORDER BY hd.ngay_tao DESC
            """)
            for row in cursor.fetchall():
                text = f"{row[1]} - {row[2]} ({row[3]} {row[4]})"
                self._contract_combo.addItem(text, {
                    "id": row[0],
                    "ma_hop_dong": row[1],
                    "khach_hang": row[2],
                    "xe": f"{row[3]} {row[4]}",
                    "tong_tien": row[5],
                })
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải danh sách hợp đồng: {str(e)}")

    def _on_contract_changed(self, index: int):
        """Handle contract selection change."""
        data = self._contract_combo.currentData()
        if data:
            self._contract_info_label.setText(
                f"Khách hàng: {data['khach_hang']} | Xe: {data['xe']} | Tổng tiền: {data['tong_tien']:,}đ".replace(",", ".")
            )
            # Set max amount to contract total
            self._amount_input.setMaximum(data["tong_tien"])
            self._amount_input.setValue(data["tong_tien"])
        else:
            self._contract_info_label.setText("Chưa chọn hợp đồng")
            self._confirm_btn.setEnabled(False)

        self._update_preview()

    def _on_params_changed(self):
        """Handle parameter changes - update preview."""
        self._update_preview()

    def _update_preview(self):
        """Update the live preview (monthly payment and schedule)."""
        data = self._contract_combo.currentData()
        if not data:
            self._monthly_payment_label.setText("0 đ")
            self._schedule_table.setRowCount(0)
            self._confirm_btn.setEnabled(False)
            return

        P = self._amount_input.value()
        r_year = self._rate_slider.value()
        n = self._months_slider.value()

        if P <= 0 or n <= 0:
            self._monthly_payment_label.setText("0 đ")
            self._schedule_table.setRowCount(0)
            self._confirm_btn.setEnabled(False)
            return

        # Calculate monthly payment
        M = self._tg_service.calculate_monthly_payment(P, r_year, n)
        self._monthly_payment_label.setText(
            f"{M:,.0f} đ/tháng".replace(",", ".")
        )

        # Build schedule table
        from dateutil.relativedelta import relativedelta
        from datetime import date, datetime

        # Get start date from contract
        cursor = self._db_conn.execute(
            "SELECT ngay_thanh_toan FROM hop_dong WHERE id = ?",
            (data["id"],)
        )
        row = cursor.fetchone()
        if row and row[0]:
            start_date = datetime.fromisoformat(row[0]).date()
        else:
            start_date = date.today()

        self._schedule_table.setRowCount(n)
        for ky in range(1, n + 1):
            ngay_den_han = start_date + relativedelta(months=ky)

            # Kỳ
            self._schedule_table.setItem(
                ky - 1, 0,
                QTableWidgetItem(str(ky))
            )

            # Ngày đến hạn
            self._schedule_table.setItem(
                ky - 1, 1,
                QTableWidgetItem(ngay_den_han.strftime("%d/%m/%Y"))
            )

            # Số tiền
            item_tien = QTableWidgetItem(f"{M:,.0f} đ".replace(",", "."))
            item_tien.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self._schedule_table.setItem(ky - 1, 2, item_tien)

            # Trạng thái
            item_status = QTableWidgetItem("Chưa trả")
            item_status.setBackground(QColor("#8e8e93"))
            item_status.setForeground(QColor(255, 255, 255))
            self._schedule_table.setItem(ky - 1, 3, item_status)

        # Enable confirm if all params are valid
        self._confirm_btn.setEnabled(
            P > 0 and r_year >= 0 and r_year <= 30 and 6 <= n <= 84
        )

    def _on_confirm(self):
        """Handle confirm button click."""
        data = self._contract_combo.currentData()
        if not data:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn hợp đồng")
            return

        hop_dong_id = data["id"]
        ngan_hang = self._bank_input.text().strip()
        P = self._amount_input.value()
        r_year = self._rate_slider.value()
        n = self._months_slider.value()

        if not ngan_hang:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tên ngân hàng")
            return

        try:
            tra_gop = self._tg_service.create(
                hop_dong_id=hop_dong_id,
                ngan_hang=ngan_hang,
                P=P,
                r_year=r_year,
                n=n,
                nhan_vien_id=self._session.nhan_vien_id if self._session else None,
            )

            QMessageBox.information(
                self, "Thành công",
                f"Đã tạo phương án trả góp thành công!\n"
                f"Số tiền trả hàng tháng: {tra_gop.so_tien_tra_thang:,}đ".replace(",", ".")
            )

            self.created.emit(tra_gop.id)
            self.accept()

        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi validation", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo phương án trả góp: {str(e)}")
