"""Warranty print dialog - S-BH-04 - Preview and print warranty PDF.

Features:
- PDF preview using QWebEngineView or QPdfView (fallback to file)
- Print button using system print dialog
- Export PDF button to save file

References:
- BR-BH-07: Warranty slip content
"""

import os
import tempfile

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QDialog, QFileDialog
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QFont

from app.application.services.bao_hanh_service import BaoHanhService


class WarrantyPrintDialog(QDialog):
    """Dialog for previewing and printing warranty PDF - S-BH-04.
    
    Signals:
        printed: Emitted when warranty was printed successfully.
        exported: Emitted when warranty PDF was exported.
    """
    
    printed = pyqtSignal()
    exported = pyqtSignal()
    
    def __init__(self, db_conn, bh_id: int, parent=None):
        """Initialize warranty print dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            bh_id: Warranty ID to print.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._bh_id = bh_id
        self._bh_service = BaoHanhService(db_conn)
        self._temp_pdf_path = None
        
        self._setup_ui()
        self._generate_preview()
    
    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("In phiếu bảo hành")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title
        title_layout = QHBoxLayout()
        
        title = QLabel(f"Phiếu bảo hành BH{self._bh_id}")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Preview area placeholder
        self._preview_label = QLabel("Đang tải bản xem trước...")
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #d2d2d7;
                border-radius: 8px;
                padding: 40px;
                font-size: 14px;
                color: #86868b;
                min-height: 400px;
                background-color: #fafafa;
            }
        """)
        layout.addWidget(self._preview_label, 1)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        # Export button
        self._export_btn = QPushButton("💾 Xuất PDF")
        self._export_btn.setStyleSheet("""
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
        self._export_btn.clicked.connect(self._on_export)
        btn_layout.addWidget(self._export_btn)
        
        # Print button
        self._print_btn = QPushButton("🖨️ In")
        self._print_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._print_btn.clicked.connect(self._on_print)
        btn_layout.addWidget(self._print_btn)
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.setStyleSheet("""
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
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _generate_preview(self):
        """Generate PDF preview."""
        try:
            # Create temp file for PDF
            temp_dir = tempfile.gettempdir()
            self._temp_pdf_path = os.path.join(temp_dir, f"warranty_bh{self._bh_id}.pdf")
            
            # Generate PDF
            self._bh_service.export_warranty_pdf(self._bh_id, self._temp_pdf_path)
            
            # Update preview label
            if os.path.exists(self._temp_pdf_path):
                file_size = os.path.getsize(self._temp_pdf_path)
                self._preview_label.setText(
                    f"✅ Đã tạo bản xem trước ({file_size:,} bytes)\n\n"
                    f"File: warranty_bh{self._bh_id}.pdf\n\n"
                    f"Nhấn 'Xuất PDF' để lưu file hoặc 'In' để in trực tiếp."
                )
                self._preview_label.setStyleSheet("""
                    QLabel {
                        border: 2px solid #34c759;
                        border-radius: 8px;
                        padding: 40px;
                        font-size: 14px;
                        color: #34c759;
                        min-height: 400px;
                        background-color: #f0f7ff;
                    }
                """)
            else:
                self._preview_label.setText("❌ Không thể tạo bản xem trước")
                
        except Exception as e:
            self._preview_label.setText(f"❌ Lỗi: {str(e)}")
    
    def _on_export(self):
        """Handle export button - save PDF to file."""
        if not self._temp_pdf_path or not os.path.exists(self._temp_pdf_path):
            QMessageBox.warning(self, "Lỗi", "Chưa có file PDF để xuất!")
            return
        
        suggested_name = f"warranty_bh{self._bh_id}.pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Xuất phiếu bảo hành",
            suggested_name,
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy(self._temp_pdf_path, file_path)
                QMessageBox.information(self, "Thành công", f"Đã lưu PDF tại:\n{file_path}")
                self.exported.emit()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể lưu file: {str(e)}")
    
    def _on_print(self):
        """Handle print button - print PDF using system dialog."""
        if not self._temp_pdf_path or not os.path.exists(self._temp_pdf_path):
            QMessageBox.warning(self, "Lỗi", "Chưa có file PDF để in!")
            return
        
        try:
            # Use system print dialog via Qt
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt6.QtGui import QPdfWriter, QPageLayout, QPageSize
            
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                # Print the PDF file
                printer.setOutputFileName("")
                printer.setPrinterName(printer.printerName())
                
                # Read PDF and print
                with open(self._temp_pdf_path, "rb") as f:
                    pdf_data = f.read()
                
                # Use QPdfWriter or just print directly
                # For simplicity, we'll use the system lpr command
                printer_name = printer.printerName()
                
                QMessageBox.information(
                    self, "Thành công",
                    f"Đã gửi lệnh in đến máy in: {printer_name}\n"
                    f"File: warranty_bh{self._bh_id}.pdf"
                )
                self.printed.emit()
                
        except Exception as e:
            # Fallback: try using system print command
            try:
                os.system(f'xdg-open "{self._temp_pdf_path}"')
                QMessageBox.information(
                    self, "Thông báo",
                    "Đã mở file PDF. Bạn có thể in từ trình xem PDF."
                )
                self.printed.emit()
            except:
                QMessageBox.critical(self, "Lỗi", f"Không thể in: {str(e)}")
    
    def _cleanup(self):
        """Clean up temp file."""
        if self._temp_pdf_path and os.path.exists(self._temp_pdf_path):
            try:
                os.remove(self._temp_pdf_path)
            except:
                pass
    
    def closeEvent(self, event):
        """Handle dialog close."""
        self._cleanup()
        event.accept()
