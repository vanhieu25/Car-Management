"""Employee profile screen - S-NV-03 - Own profile and KPI for A-02/A-03.

Features:
- Display: ho_ten, email, so_dien_thoai, vai_tro
- KPI cards: số xe bán tháng này, doanh thu tháng này
- Button: Đổi mật khẩu (opens change_password_dialog)

References:
- BR-NV-01..08: Employee management rules
- BR-CALC-05: Employee KPI calculation
- UC-SEC-02: Change password
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QPushButton, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.application.services.nhan_vien_service import NhanVienService
from app.application.services.session import CurrentSession
from app.domain.entities import NhanVien
from app.presentation.screens.change_password_dialog import ChangePasswordDialog


class KpiCard(QWidget):
    """KPI card widget with title, value, and optional subtitle."""
    
    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = None,
        color: str = "#007AFF",
        parent=None
    ):
        """Initialize KPI card.
        
        Args:
            title: Card title (e.g., "Số xe bán")
            value: Main value (e.g., "12")
            subtitle: Optional subtitle/hint
            color: Accent color
            parent: Parent widget.
        """
        super().__init__(parent)
        self._color = color
        self._setup_ui(title, value, subtitle)
    
    def _setup_ui(self, title: str, value: str, subtitle: str = None):
        """Set up UI components."""
        self.setMinimumWidth(180)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #E5E5EA;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title, self)
        title_label.setStyleSheet("""
            font-size: 13px;
            color: #86868B;
            font-weight: 500;
        """)
        layout.addWidget(title_label)
        
        # Value
        self._value_label = QLabel(value, self)
        self._value_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {self._color};
        """)
        layout.addWidget(self._value_label)
        
        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle, self)
            subtitle_label.setStyleSheet("""
                font-size: 12px;
                color: #8E8E93;
            """)
            layout.addWidget(subtitle_label)
        
        layout.addStretch()
    
    def set_value(self, value: str):
        """Update the displayed value."""
        self._value_label.setText(value)


class EmployeeProfileScreen(QWidget):
    """Employee profile screen - S-NV-03.
    
    For A-02/A-03 to view their own profile and KPI.
    """
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize employee profile screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session (must have nhan_vien_id).
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._nv_service = NhanVienService(db_conn, session)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("👤 Hồ sơ cá nhân")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Change password button
        self._change_pw_btn = QPushButton("🔐 Đổi mật khẩu")
        self._change_pw_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0055BB;
            }
        """)
        self._change_pw_btn.clicked.connect(self._on_change_password)
        header_layout.addWidget(self._change_pw_btn)
        
        layout.addLayout(header_layout)
        
        # Profile info card
        profile_card = QWidget(self)
        profile_card.setStyleSheet("""
            QWidget#profile_card {
                background-color: white;
                border-radius: 12px;
                padding: 24px;
                border: 1px solid #E5E5EA;
            }
        """)
        profile_card.setObjectName("profile_card")
        
        profile_layout = QVBoxLayout(profile_card)
        profile_layout.setSpacing(16)
        
        # Profile header
        profile_header = QLabel("Thông tin cá nhân")
        profile_header.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1C1C1E;
        """)
        profile_layout.addWidget(profile_header)
        
        # Info grid
        info_grid = QGridLayout()
        info_grid.setSpacing(12)
        
        # Row 1: Ho ten
        info_grid.addWidget(QLabel("Họ tên:", self), 0, 0)
        self._ho_ten_label = QLabel("-", self)
        self._ho_ten_label.setStyleSheet("font-size: 14px; color: #1C1C1E;")
        info_grid.addWidget(self._ho_ten_label, 0, 1)
        
        # Row 2: Username
        info_grid.addWidget(QLabel("Username:", self), 1, 0)
        self._username_label = QLabel("-", self)
        self._username_label.setStyleSheet("font-size: 14px; color: #1C1C1E;")
        info_grid.addWidget(self._username_label, 1, 1)
        
        # Row 3: Email
        info_grid.addWidget(QLabel("Email:", self), 2, 0)
        self._email_label = QLabel("-", self)
        self._email_label.setStyleSheet("font-size: 14px; color: #1C1C1E;")
        info_grid.addWidget(self._email_label, 2, 1)
        
        # Row 4: So dien thoai
        info_grid.addWidget(QLabel("Số điện thoại:", self), 3, 0)
        self._sdt_label = QLabel("-", self)
        self._sdt_label.setStyleSheet("font-size: 14px; color: #1C1C1E;")
        info_grid.addWidget(self._sdt_label, 3, 1)
        
        # Row 5: Vai tro
        info_grid.addWidget(QLabel("Vai trò:", self), 4, 0)
        self._vai_tro_label = QLabel("-", self)
        self._vai_tro_label.setStyleSheet("font-size: 14px; color: #1C1C1E;")
        info_grid.addWidget(self._vai_tro_label, 4, 1)
        
        # Row 6: Trang thai
        info_grid.addWidget(QLabel("Trạng thái:", self), 5, 0)
        self._trang_thai_label = QLabel("-", self)
        self._trang_thai_label.setStyleSheet("font-size: 14px; color: #1C1C1E;")
        info_grid.addWidget(self._trang_thai_label, 5, 1)
        
        profile_layout.addLayout(info_grid)
        
        layout.addWidget(profile_card)
        
        # KPI Section
        kpi_header = QLabel("📊 KPI tháng này")
        kpi_header.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(kpi_header)
        
        # KPI cards row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)
        
        self._so_xe_card = KpiCard(
            title="Số xe bán",
            value="0",
            subtitle="Hợp đồng đã giao",
            color="#34C759"
        )
        kpi_row.addWidget(self._so_xe_card)
        
        self._doanh_thu_card = KpiCard(
            title="Doanh thu tháng",
            value="0 đ",
            subtitle="Tổng giá trị",
            color="#007AFF"
        )
        kpi_row.addWidget(self._doanh_thu_card)
        
        self._ti_le_chot_card = KpiCard(
            title="Tỷ lệ chốt",
            value="N/A",
            subtitle="Không có dữ liệu",
            color="#FF9500"
        )
        kpi_row.addWidget(self._ti_le_chot_card)
        
        layout.addLayout(kpi_row)
        
        layout.addStretch()
    
    def _load_data(self):
        """Load employee data and KPI."""
        if not self._session:
            return
        
        nhan_vien_id = self._session.user_id
        
        try:
            # Get employee info
            nv = self._nv_service.get_by_id(nhan_vien_id)
            if nv:
                self._ho_ten_label.setText(nv.ho_ten)
                self._username_label.setText(nv.username)
                self._email_label.setText(nv.email or "-")
                self._sdt_label.setText(nv.so_dien_thoai or "-")
                
                # Role label
                role_labels = {
                    1: ("Admin", "#FF3B30"),
                    2: ("Sales", "#007AFF"),
                    3: ("Kỹ thuật BH", "#34C759"),
                }
                role_text, _ = role_labels.get(nv.vai_tro_id, ("N/A", "#8E8E93"))
                self._vai_tro_label.setText(role_text)
                
                # Status label
                if nv.trang_thai == "active":
                    status_text = "Hoạt động"
                else:
                    status_text = "Bị khoá"
                self._trang_thai_label.setText(status_text)
            
            # Get KPI
            kpi = self._nv_service.get_current_month_kpi(nhan_vien_id)
            
            # Update KPI cards
            so_xe = kpi.get('so_hop_dong', 0)
            self._so_xe_card.set_value(str(so_xe))
            
            doanh_thu = kpi.get('doanh_thu', 0)
            if doanh_thu > 0:
                doanh_thu_text = f"{doanh_thu:,.0f} đ".replace(",", ".")
            else:
                doanh_thu_text = "0 đ"
            self._doanh_thu_card.set_value(doanh_thu_text)
            
            ti_le = kpi.get('ti_le_chot')
            if ti_le is not None:
                self._ti_le_chot_card.set_value(f"{ti_le:.1f}%")
            else:
                self._ti_le_chot_card.set_value("N/A")
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
    
    def _on_change_password(self):
        """Handle change password button click."""
        if not self._session:
            return
        
        user_id = self._session.user_id
        
        dialog = ChangePasswordDialog(
            user_id=user_id,
            require_old_password=True,
            force_change=False,
            parent=self
        )
        dialog.password_changed.connect(self._on_password_changed)
        dialog.exec()
    
    def _on_password_changed(self):
        """Handle successful password change."""
        QMessageBox.information(
            self,
            "Thành công",
            "Đổi mật khẩu thành công!"
        )
    
    def refresh(self):
        """Refresh the data."""
        self._load_data()
