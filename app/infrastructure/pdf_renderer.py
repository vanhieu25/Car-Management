"""PDF Renderer for contract documents.

Uses Jinja2 for templating and WeasyPrint for PDF generation.
"""

import os
from typing import Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from weasyprint import HTML, CSS


class PdfRenderer:
    """Renders contract documents as PDF using Jinja2 templates and WeasyPrint."""

    def __init__(self, template_dir: str, css_path: str):
        """Initialize the PDF renderer.

        Args:
            template_dir: Directory containing Jinja2 templates.
            css_path: Path to the CSS file for styling.
        """
        self.template_dir = template_dir
        self.css_path = css_path
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render_contract(self, hop_dong_id: int, output_path: str, conn) -> str:
        """Render a contract as PDF.

        Loads contract data by ID with all relations (KH, xe, pk list, km),
        renders the Jinja2 template, and converts to PDF.

        Args:
            hop_dong_id: Contract ID.
            output_path: Path to save the PDF file.
            conn: Database connection for loading contract data.

        Returns:
            Path to the saved PDF file.
        """
        # Load contract with all relations
        data = self._load_contract_data(hop_dong_id, conn)

        # Load and render template
        template = self.env.get_template("contract.html")
        html_content = template.render(**data)

        # Generate PDF
        html_obj = HTML(string=html_content)

        if os.path.exists(self.css_path):
            css_obj = CSS(filename=self.css_path)
            html_obj.write_pdf(output_path, stylesheets=[css_obj])
        else:
            html_obj.write_pdf(output_path)

        return output_path

    def _load_contract_data(self, hop_dong_id: int, conn) -> dict:
        """Load contract data with all relations.

        Args:
            hop_dong_id: Contract ID.
            conn: Database connection.

        Returns:
            Dict with contract data and all relations for template rendering.
        """
        cursor = conn.execute("SELECT * FROM hop_dong WHERE id = ?", (hop_dong_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Không tìm thấy hợp đồng với ID {hop_dong_id}")

        hop_dong = dict(row)

        # Load customer
        cursor = conn.execute(
            "SELECT * FROM khach_hang WHERE id = ?",
            (hop_dong["khach_hang_id"],)
        )
        kh_row = cursor.fetchone()
        hop_dong["khach_hang"] = dict(kh_row) if kh_row else {}

        # Load vehicle
        cursor = conn.execute(
            "SELECT * FROM xe WHERE id = ?",
            (hop_dong["xe_id"],)
        )
        xe_row = cursor.fetchone()
        hop_dong["xe"] = dict(xe_row) if xe_row else {}

        # Load employee
        cursor = conn.execute(
            "SELECT * FROM nhan_vien WHERE id = ?",
            (hop_dong["nhan_vien_id"],)
        )
        nv_row = cursor.fetchone()
        hop_dong["nhan_vien"] = dict(nv_row) if nv_row else {}

        # Load accessories
        cursor = conn.execute(
            """SELECT pk.*, hdpk.so_luong as so_luong_mua, hdpk.gia_ban as gia_ban_snapshot
               FROM hop_dong_phu_kien hdpk
               JOIN phu_kien pk ON hdpk.phu_kien_id = pk.id
               WHERE hdpk.hop_dong_id = ?""",
            (hop_dong_id,)
        )
        hop_dong["phu_kien_list"] = [dict(row) for row in cursor.fetchall()]

        # Load promotion if exists
        if hop_dong.get("khuyen_mai_id"):
            cursor = conn.execute(
                "SELECT * FROM khuyen_mai WHERE id = ?",
                (hop_dong["khuyen_mai_id"],)
            )
            km_row = cursor.fetchone()
            hop_dong["khuyen_mai"] = dict(km_row) if km_row else None
        else:
            hop_dong["khuyen_mai"] = None

        # Load system settings for dealer info
        cursor = conn.execute("SELECT ma_settings, gia_tri FROM system_settings")
        settings = {}
        for row in cursor.fetchall():
            settings[row[0]] = row[1]
        hop_dong["system_settings"] = settings

        # Add helper functions/filters for template
        hop_dong["format_vnd"] = self._format_vnd

        return hop_dong

    @staticmethod
    def _format_vnd(amount: int) -> str:
        """Format amount as VND currency string.

        Args:
            amount: Amount in VND.

        Returns:
            Formatted string like "1.000.000 đ".
        """
        if amount is None:
            return "0 đ"
        s = str(int(amount))
        result = []
        for i, c in enumerate(reversed(s)):
            if i > 0 and i % 3 == 0:
                result.append(".")
            result.append(c)
        return "".join(reversed(result)) + " đ"
