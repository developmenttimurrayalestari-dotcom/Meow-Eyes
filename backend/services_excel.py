"""Excel export helpers using openpyxl."""
from __future__ import annotations
from io import BytesIO
from typing import List, Dict, Any
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


HEADER_FILL = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)
THIN = Border(left=Side(style="thin", color="CCCCCC"),
              right=Side(style="thin", color="CCCCCC"),
              top=Side(style="thin", color="CCCCCC"),
              bottom=Side(style="thin", color="CCCCCC"))


def build_workbook(
    title: str,
    headers: List[str],
    rows: List[List[Any]],
    meta: Dict[str, Any] | None = None,
) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = title[:30] or "Report"

    # Title
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(1, len(headers)))
    title_cell = ws.cell(row=1, column=1, value=title)
    title_cell.font = Font(size=16, bold=True, color="0B192C")
    title_cell.alignment = Alignment(horizontal="left", vertical="center")

    # Meta
    meta = meta or {}
    meta_row = 2
    meta_lines = [
        f"Periode: {meta.get('period', '-')}",
        f"Tanggal Export: {datetime.now().strftime('%d %b %Y %H:%M')}",
        f"Admin: {meta.get('admin', '-')}",
    ]
    for line in meta_lines:
        ws.merge_cells(start_row=meta_row, start_column=1, end_row=meta_row, end_column=max(1, len(headers)))
        c = ws.cell(row=meta_row, column=1, value=line)
        c.font = Font(size=10, color="4A5568")
        meta_row += 1

    header_row_idx = meta_row + 1
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=header_row_idx, column=i, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = THIN

    for r_idx, row in enumerate(rows, start=header_row_idx + 1):
        for c_idx, val in enumerate(row, start=1):
            c = ws.cell(row=r_idx, column=c_idx, value=val)
            c.border = THIN
            c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # Auto-width
    for i, h in enumerate(headers, start=1):
        col = get_column_letter(i)
        max_len = len(str(h))
        for row in rows:
            if i - 1 < len(row):
                max_len = max(max_len, len(str(row[i - 1])))
        ws.column_dimensions[col].width = min(48, max(12, max_len + 2))

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()
