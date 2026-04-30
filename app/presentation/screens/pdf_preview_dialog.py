"""PDF preview dialog - S-HD-04 - Contract PDF preview and export.

Features:
- Render PDF inline using QPdfView or QWebEngineView or external preview
- Toolbar: "In" button (calls system print), "Xuất file" (save dialog), "Đóng"
- Uses HopDongService.export_pdf() to generate PDF

References:
- BR-HD-07: PDF must contain required contract information
"""

import os
import tempfile
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QWidget, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QSize, QUrl
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile

from app.application.services.hop_dong_service import HopDongService


class PdfPreviewDialog(QDialog):
    """Dialog for previewing and exporting contract PDF.
    
    Uses web engine to render HTML preview and provides PDF export.
    """
    
    def __init__(self, db_conn, hop_dong_id: int, parent=None):
        """Initialize PDF preview dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            hop_dong_id: Contract ID to preview.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._hop_dong_id = hop_dong_id
        self._hd_service = HopDongService(db_conn)
        self._pdf_path: Optional[str] = None
        self._html_content: Optional[str] = None
        
        self._setup_ui()
        self._generate_preview()
    
    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Xem trước hợp đồng - PDF")
        self.setMinimumSize(800, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #d2d2d7;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 8, 16, 8)
        toolbar_layout.setSpacing(12)
        
        # Contract code label
        self._title_label = QLabel("Đang tải...")
        self._title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f;")
        toolbar_layout.addWidget(self._title_label)
        
        toolbar_layout.addStretch()
        
        # Print button
        self._print_btn = QPushButton("🖨️ In")
        self._print_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._print_btn.clicked.connect(self._on_print)
        toolbar_layout.addWidget(self._print_btn)
        
        # Export button
        self._export_btn = QPushButton("💾 Xuất file")
        self._export_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._export_btn.clicked.connect(self._on_export)
        toolbar_layout.addWidget(self._export_btn)
        
        # Close button
        self._close_btn = QPushButton("✕ Đóng")
        self._close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #86868b;
                border: none;
                padding: 8px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                color: #1d1d1f;
            }
        """)
        self._close_btn.clicked.connect(self.accept)
        toolbar_layout.addWidget(self._close_btn)
        
        layout.addWidget(toolbar)
        
        # Preview area
        self._preview_stack = QStackedWidget()
        
        # Loading placeholder
        self._loading_widget = QWidget()
        loading_layout = QVBoxLayout(self._loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        loading_label = QLabel("⏳ Đang tạo bản xem trước...")
        loading_label.setStyleSheet("font-size: 16px; color: #86868b;")
        loading_layout.addWidget(loading_label)
        
        self._preview_stack.addWidget(self._loading_widget)
        
        # Web view for HTML rendering
        self._web_view = QWebEngineView()
        self._web_view.setMinimumSize(QSize(700, 500))
        self._preview_stack.addWidget(self._web_view)
        
        # Error placeholder
        self._error_widget = QWidget()
        error_layout = QVBoxLayout(self._error_widget)
        error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        error_label = QLabel("❌ Không thể tạo bản xem trước.\nVui lòng thử xuất file PDF.")
        error_label.setStyleSheet("font-size: 14px; color: #86868b;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_layout.addWidget(error_label)
        
        self._preview_stack.addWidget(self._error_widget)
        
        layout.addWidget(self._preview_stack)
    
    def _generate_preview(self):
        """Generate HTML preview of the contract."""
        try:
            # Get contract data
            data = self._hd_service.get_full_contract(self._hop_dong_id)
            if not data:
                self._title_label.setText("❌ Không tìm thấy hợp đồng")
                self._preview_stack.setCurrentWidget(self._error_widget)
                return
            
            hd = data.get('hop_dong', {})
            kh = data.get('khach_hang', {})
            xe = data.get('xe', {})
            nv = data.get('nhan_vien', {})
            pk_list = data.get('phu_kien_list', [])
            km = data.get('khuyen_mai', {})
            
            self._title_label.setText(f"Hợp đồng: {hd.get('ma_hop_dong', 'N/A')}")
            
            # Build HTML content
            self._html_content = self._build_contract_html(data)
            
            # Load into web view
            self._web_view.setHtml(self._html_content)
            self._preview_stack.setCurrentWidget(self._web_view)
            
        except Exception as e:
            self._title_label.setText(f"❌ Lỗi: {str(e)[:50]}")
            self._preview_stack.setCurrentWidget(self._error_widget)
    
    def _build_contract_html(self, data: dict) -> str:
        """Build HTML representation of contract for preview.
        
        Args:
            data: Contract data from get_full_contract.
            
        Returns:
            HTML string for rendering.
        """
        hd = data.get('hop_dong', {})
        kh = data.get('khach_hang', {})
        xe = data.get('xe', {})
        nv = data.get('nhan_vien', {})
        pk_list = data.get('phu_kien_list', [])
        km = data.get('khuyen_mai', {})
        
        # Format helpers
        def fmt_vnd(amount):
            if amount is None:
                return "0 đ"
            return f"{int(amount):,.0f} đ".replace(",", ".")
        
        # Build accessories rows
        pk_rows = ""
        for pk in pk_list:
            pk_rows += f"""
            <tr>
                <td>{pk.get('ten_pk', 'N/A')}</td>
                <td>{pk.get('phan_loai', 'N/A')}</td>
                <td style="text-align: center;">{pk.get('so_luong_mua', 1)}</td>
                <td style="text-align: right;">{fmt_vnd(pk.get('gia_ban_snapshot', 0))}</td>
                <td style="text-align: right;">{fmt_vnd(pk.get('gia_ban_snapshot', 0) * pk.get('so_luong_mua', 1))}</td>
            </tr>
            """
        
        if not pk_rows:
            pk_rows = "<tr><td colspan='5' style='text-align: center; color: #86868b;'>Không có phụ kiện đi kèm</td></tr>"
        
        # Promotion info
        km_info = "Không có khuyến mãi"
        if km:
            km_info = f"{km.get('ten_km', 'N/A')} ({km.get('loai_km', 'N/A')}) - Giảm: {fmt_vnd(hd.get('tien_giam_km', 0))}"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; color: #1d1d1f; background: #fff; padding: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        
        .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0066cc; padding-bottom: 20px; }}
        .header h1 {{ font-size: 24px; color: #0066cc; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 14px; color: #86868b; }}
        
        .section {{ margin-bottom: 24px; }}
        .section-title {{ font-size: 14px; font-weight: 700; color: #0066cc; border-bottom: 1px solid #d2d2d7; padding-bottom: 8px; margin-bottom: 12px; }}
        
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
        .info-item {{ margin-bottom: 8px; }}
        .info-label {{ font-weight: 600; color: #86868b; font-size: 11px; text-transform: uppercase; }}
        .info-value {{ font-size: 13px; color: #1d1d1f; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
        th {{ background: #f5f5f7; padding: 10px 8px; text-align: left; font-weight: 600; font-size: 12px; border-bottom: 2px solid #d2d2d7; }}
        td {{ padding: 8px; border-bottom: 1px solid #e5e5ea; font-size: 12px; }}
        
        .total-section {{ background: #f0f7ff; border: 2px solid #0066cc; border-radius: 8px; padding: 16px; margin-top: 24px; }}
        .total-row {{ display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; }}
        .total-row.grand {{ font-size: 16px; font-weight: 700; color: #0066cc; border-top: 2px solid #0066cc; margin-top: 8px; padding-top: 12px; }}
        
        .timeline {{ margin-top: 24px; }}
        .timeline-item {{ display: flex; align-items: center; margin-bottom: 12px; }}
        .timeline-icon {{ width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 12px; }}
        .timeline-icon.success {{ background: #34c759; color: white; }}
        .timeline-icon.cancel {{ background: #ff3b30; color: white; }}
        .timeline-icon.pending {{ background: #8e8e93; color: white; }}
        .timeline-text {{ font-size: 12px; }}
        
        .footer {{ margin-top: 40px; text-align: center; font-size: 11px; color: #86868b; }}
        
        .notes {{ background: #fafafa; border: 1px solid #d2d2d7; border-radius: 6px; padding: 12px; margin-top: 12px; font-size: 12px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>HỢP ĐỒNG MUA BÁN XE Ô TÔ</h1>
            <div class="subtitle">Mã hợp đồng: <strong>{hd.get('ma_hop_dong', 'N/A')}</strong> | Ngày lập: {hd.get('ngay_tao', '')[:10] if hd.get('ngay_tao') else 'N/A'}</div>
        </div>
        
        <div class="section">
            <div class="section-title">THÔNG TIN KHÁCH HÀNG</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Họ tên</div>
                    <div class="info-value">{kh.get('ho_ten', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Số điện thoại</div>
                    <div class="info-value">{kh.get('so_dien_thoai', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Email</div>
                    <div class="info-value">{kh.get('email', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Địa chỉ</div>
                    <div class="info-value">{kh.get('dia_chi', 'N/A')}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">THÔNG TIN XE</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Hãng xe</div>
                    <div class="info-value">{xe.get('hang', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Dòng xe</div>
                    <div class="info-value">{xe.get('dong_xe', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Mã xe</div>
                    <div class="info-value">{xe.get('ma_xe', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Năm sản xuất</div>
                    <div class="info-value">{xe.get('nam_san_xuat', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Màu sắc</div>
                    <div class="info-value">{xe.get('mau_sac', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Giá bán (cố định)</div>
                    <div class="info-value" style="font-weight: 600; color: #0066cc;">{fmt_vnd(hd.get('gia_xe', 0))}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">PHỤ KIỆN ĐI KÈM</div>
            <table>
                <thead>
                    <tr>
                        <th>Tên phụ kiện</th>
                        <th>Phân loại</th>
                        <th style="text-align: center;">Số lượng</th>
                        <th style="text-align: right;">Giá đơn vị</th>
                        <th style="text-align: right;">Thành tiền</th>
                    </tr>
                </thead>
                <tbody>
                    {pk_rows}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <div class="section-title">KHUYẾN MÃI</div>
            <div class="info-value">{km_info}</div>
        </div>
        
        <div class="total-section">
            <div class="section-title" style="border: none; margin-bottom: 8px;">TỔNG HỢP THANH TOÁN</div>
            <div class="total-row">
                <span>Giá xe:</span>
                <span>{fmt_vnd(hd.get('gia_xe', 0))}</span>
            </div>
            <div class="total-row">
                <span>Phụ kiện:</span>
                <span>{fmt_vnd(hd.get('tong_gia_phu_kien', 0))}</span>
            </div>
            <div class="total-row" style="color: #34c759;">
                <span>Giảm giá KM:</span>
                <span>-{fmt_vnd(hd.get('tien_giam_km', 0))}</span>
            </div>
            <div class="total-row grand">
                <span>TỔNG CỘNG:</span>
                <span>{fmt_vnd(hd.get('tong_tien', 0))}</span>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">TRẠNG THÁI HỢP ĐỒNG</div>
            <div class="timeline">
                <div class="timeline-item">
                    <div class="timeline-icon success">✓</div>
                    <div class="timeline-text"><strong>Tạo hợp đồng</strong> - {hd.get('ngay_tao', '')[:19] if hd.get('ngay_tao') else 'N/A'} - NV: {nv.get('ho_ten', 'N/A')}</div>
                </div>
                {"<div class='timeline-item'><div class='timeline-icon success'>✓</div><div class='timeline-text'><strong>Thanh toán</strong> - " + hd.get('ngay_thanh_toan', '')[:19] + "</div></div>" if hd.get('ngay_thanh_toan') else ""}
                {"<div class='timeline-item'><div class='timeline-icon success'>✓</div><div class='timeline-text'><strong>Giao xe</strong> - " + hd.get('ngay_giao_xe', '')[:19] + "</div></div>" if hd.get('ngay_giao_xe') else ""}
                {"<div class='timeline-item'><div class='timeline-icon cancel'>✕</div><div class='timeline-text'><strong>Hủy hợp đồng</strong> - Lý do: " + (hd.get('ly_do_huy') or 'N/A') + "</div></div>" if hd.get('trang_thai') == 'huy' else ""}
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">GHI CHÚ</div>
            <div class="notes">{"Không có ghi chú" if not hd.get('ghi_chu') else hd.get('ghi_chu')}</div>
        </div>
        
        <div class="footer">
            <p>Hợp đồng này được tạo tự động bởi hệ thống Quản lý Bán xe Ô tô</p>
            <p>Ngày in: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _on_print(self):
        """Handle print button - open print dialog for web view."""
        self._web_view.page().printToPdf(
            lambda path: QDesktopServices.openUrl(QUrl.fromLocalFile(path)),
            QWebEngineProfile.defaultProfile().defaultProfile()
        )
    
    def _on_export(self):
        """Handle export button - save PDF to file."""
        try:
            # Generate PDF file path
            data = self._hd_service.get_full_contract(self._hop_dong_id)
            if not data:
                QMessageBox.critical(self, "Lỗi", "Không tìm thấy hợp đồng")
                return
            
            hd = data.get('hop_dong', {})
            default_name = f"HopDong_{hd.get('ma_hop_dong', 'unknown')}.pdf"
            
            # Show save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Lưu hợp đồng PDF",
                default_name,
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            # Use service to export PDF
            output_path = self._hd_service.export_pdf(self._hop_dong_id, file_path)
            
            QMessageBox.information(
                self,
                "Thành công",
                f"Đã lưu hợp đồng vào:\n{output_path}"
            )
            
            # Offer to open the file
            reply = QMessageBox.question(
                self,
                "Mở file",
                "Bạn có muốn mở file PDF không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(output_path))
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất PDF: {str(e)}")
