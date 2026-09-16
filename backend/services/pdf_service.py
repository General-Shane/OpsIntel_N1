import os
import re
import io
import structlog

logger = structlog.get_logger(__name__)

def generate_pdf_from_markdown(markdown_text: str, title: str = "OPSINTEL Executive Operations Report") -> bytes:
    """
    Converts Markdown report narrative into a multi-page PDF document byte stream.
    Renders markdown headers, bullet lists, markdown tables, callout boxes,
    and running headers/footers with dynamic page numbering (e.g. Page X of Y).
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas

        class NumberedCanvas(canvas.Canvas):
            """
            Two-pass canvas to dynamically compute and stamp total page count (Page X of Y)
            and running corporate headers/footers.
            """
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_header_footer(num_pages)
                    super().showPage()
                super().save()

            def draw_header_footer(self, page_count):
                self.saveState()
                
                # Running Header (pages > 1)
                if self._pageNumber > 1:
                    self.setFont("Helvetica-Bold", 8)
                    self.setFillColor(colors.HexColor("#0070AD"))
                    self.drawString(36, 756, "OPSINTEL")
                    self.setFont("Helvetica", 8)
                    self.setFillColor(colors.HexColor("#64748b"))
                    self.drawString(88, 756, "|  Capgemini IT Operations Intelligence Platform")
                    self.setStrokeColor(colors.HexColor("#e2e8f0"))
                    self.setLineWidth(0.5)
                    self.line(36, 748, 576, 748)

                # Running Footer (all pages)
                self.setStrokeColor(colors.HexColor("#e2e8f0"))
                self.setLineWidth(0.5)
                self.line(36, 42, 576, 42)

                self.setFont("Helvetica", 8)
                self.setFillColor(colors.HexColor("#64748b"))
                self.drawString(36, 30, "© 2026 Capgemini. All rights reserved. Confidential — Internal Corporate Use Only")
                
                page_str = f"Page {self._pageNumber} of {page_count}"
                self.drawRightString(576, 30, page_str)
                self.restoreState()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=48,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        # Capgemini Enterprise Brand Styles
        doc_title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#001935'),
            fontName='Helvetica-Bold',
            spaceAfter=4
        )

        doc_subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#0070AD'),
            fontName='Helvetica-Bold',
            spaceAfter=8
        )
        
        h1_style = ParagraphStyle(
            'SectionH1',
            parent=styles['Heading1'],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#001935'),
            fontName='Helvetica-Bold',
            spaceBefore=14,
            spaceAfter=6
        )

        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#0070AD'),
            fontName='Helvetica-Bold',
            spaceBefore=10,
            spaceAfter=4
        )

        h3_style = ParagraphStyle(
            'SectionH3',
            parent=styles['Heading3'],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#334155'),
            fontName='Helvetica-Bold',
            spaceBefore=6,
            spaceAfter=3
        )
        
        body_style = ParagraphStyle(
            'BodyDark',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=4
        )

        bullet_style = ParagraphStyle(
            'BulletDark',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#334155'),
            spaceAfter=3,
            leftIndent=10
        )

        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        )

        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#1e293b')
        )
        
        code_style = ParagraphStyle(
            'CodeBlock',
            parent=styles['Normal'],
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#0f172a'),
            fontName='Courier',
            spaceBefore=4,
            spaceAfter=4
        )

        elements = []
        
        # Document Header Banner with Official Capgemini Logo
        logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "assets", "capgemini-logo.png"))
        if os.path.exists(logo_path):
            try:
                from reportlab.platypus import Image as RLImage
                logo_img = RLImage(logo_path, width=120, height=27)
                header_table = Table([[Paragraph("OPSINTEL", doc_title_style), logo_img]], colWidths=[410, 130])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                ]))
                elements.append(header_table)
            except Exception as e:
                logger.warning("failed_embedding_pdf_logo", error=str(e))
                elements.append(Paragraph("OPSINTEL — Executive Operations Report", doc_title_style))
        else:
            elements.append(Paragraph("OPSINTEL — Executive Operations Report", doc_title_style))

        elements.append(Paragraph("Capgemini IT Operations Intelligence Platform • Automated SRE Governance", doc_subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0070AD'), spaceBefore=4, spaceAfter=10))

        # Clean unsupported HTML tags for ReportLab
        clean_text = re.sub(r'<span[^>]*>(.*?)</span>', r'<b>\1</b>', markdown_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'</?(div|p|style|font|span)[^>]*>', '', clean_text, flags=re.IGNORECASE)
        lines = clean_text.split('\n')
        in_code_block = False
        code_lines = []
        table_buffer = []

        def flush_table(tbl_lines):
            if not tbl_lines:
                return
            matrix = []
            for r in tbl_lines:
                cells = [c.strip() for c in r.strip('|').split('|')]
                matrix.append(cells)
            
            # Remove markdown separator line if present (e.g. |---|---|)
            if len(matrix) > 1 and all(set(c.replace('-', '').replace(':', '').strip()) == set() for c in matrix[1] if c.strip()):
                matrix.pop(1)

            if not matrix:
                return

            table_data = []
            for row_idx, row in enumerate(matrix):
                row_cells = []
                for cell in row:
                    cell_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cell)
                    if row_idx == 0:
                        row_cells.append(Paragraph(cell_text, table_header_style))
                    else:
                        row_cells.append(Paragraph(cell_text, table_cell_style))
                table_data.append(row_cells)

            num_cols = max(len(r) for r in table_data) if table_data else 1
            col_width = 540.0 / num_cols

            t = Table(table_data, colWidths=[col_width] * num_cols)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070AD')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('TOPPADDING', (0, 0), (-1, 0), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f7fc'), colors.white]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 6))

        for line in lines:
            stripped = line.strip()

            # Handle Markdown Tables
            if stripped.startswith('|') and stripped.endswith('|'):
                table_buffer.append(stripped)
                continue
            elif table_buffer:
                flush_table(table_buffer)
                table_buffer = []

            # Handle Code Blocks
            if stripped.startswith("```"):
                if in_code_block:
                    in_code_block = False
                    code_text = "<br/>".join(code_lines)
                    code_lines = []
                    elements.append(Paragraph(code_text, code_style))
                    elements.append(Spacer(1, 4))
                else:
                    in_code_block = True
                continue

            if in_code_block:
                escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(' ', '&nbsp;')
                code_lines.append(escaped)
                continue

            if not stripped:
                elements.append(Spacer(1, 2))
                continue

            # Page Break Directive
            if stripped == '---' or stripped == '<pagebreak>':
                elements.append(Spacer(1, 4))
                elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=2, spaceAfter=6))
                continue

            # Headers
            if stripped.startswith('# '):
                t = stripped[2:].strip()
                elements.append(Paragraph(t, h1_style))
            elif stripped.startswith('## '):
                t = stripped[3:].strip()
                elements.append(Paragraph(t, h1_style))
            elif stripped.startswith('### '):
                t = stripped[4:].strip()
                elements.append(Paragraph(t, h2_style))
            elif stripped.startswith('#### '):
                t = stripped[5:].strip()
                elements.append(Paragraph(t, h3_style))
            elif stripped.startswith('- ') or stripped.startswith('* '):
                t = stripped[2:].strip()
                t = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', t)
                elements.append(Paragraph(f"• {t}", bullet_style))
            else:
                t = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                elements.append(Paragraph(t, body_style))

        if table_buffer:
            flush_table(table_buffer)

        doc.build(elements, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        logger.warning("reportlab_error_using_fallback", error=str(e))
        return _build_fallback_pdf(markdown_text, title)


def _build_fallback_pdf(text: str, title: str) -> bytes:
    """
    Multi-page pure Python PDF builder for text reports.
    """
    lines = [f"=== {title.upper()} ===", "Capgemini IT Operations Intelligence Platform", ""]
    for l in text.split('\n'):
        clean = l.replace('**', '').replace('#', '').strip()
        if clean:
            lines.append(clean)

    lines_per_page = 50
    pages_lines = [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)]
    if not pages_lines:
        pages_lines = [["No data available"]]

    num_pages = len(pages_lines)
    objects = []
    
    # 1. Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    
    # 2. Pages Parent
    kids_str = " ".join([f"{3 + i*3} 0 R" for i in range(num_pages)])
    objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>\nendobj")
    
    # Page objects and contents
    cur_obj_id = 3
    for p_idx, page in enumerate(pages_lines):
        content_obj_id = cur_obj_id + 1
        font_obj_id = cur_obj_id + 2

        content_stream = f"BT /F1 9 Tf 36 750 Td 13 TL\n"
        for pline in page:
            esc_line = pline.replace('—', '-').replace('–', '-').replace('•', '*').replace('“', '"').replace('”', '"').replace('’', "'")
            esc_line = esc_line.encode('latin1', errors='replace').decode('latin1')
            esc_line = esc_line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            content_stream += f"({esc_line}) '\n"
        content_stream += "ET\n"
        
        stream_len = len(content_stream.encode('latin1'))

        page_obj = f"{cur_obj_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {content_obj_id} 0 R /Resources << /Font << /F1 {font_obj_id} 0 R >> >> >>\nendobj"
        content_obj = f"{content_obj_id} 0 obj\n<< /Length {stream_len} >>\nstream\n{content_stream}endstream\nendobj"
        font_obj = f"{font_obj_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj"
        
        objects.extend([page_obj, content_obj, font_obj])
        cur_obj_id += 3

    pdf_body = "%PDF-1.4\n" + "\n".join(objects) + "\ntrailer\n<< /Size " + str(cur_obj_id) + " /Root 1 0 R >>\n%%EOF\n"
    return pdf_body.encode('latin1')
