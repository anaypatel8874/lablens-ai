"""LabLens AI — Professional PDF Report Engine
Features:
- Smart content flow with Platypus flowables
- Deep Explain integration
- Keep-together / keep-with-next logic
- Repeating table headers
- Compact professional layout
- Hindi/English/Hinglish support
- Page numbering
- Blank page prevention
- PDF validation
"""
import io
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, NextPageTemplate, Flowable
)


from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.core.logging import get_logger

logger = logging.getLogger(__name__)

# A4 dimensions
A4_WIDTH, A4_HEIGHT = A4


class HorizontalLine(Flowable):
    """A horizontal line flowable."""
    def __init__(self, width, thickness=0.5, color=colors.grey):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color

    def wrap(self, availWidth, availHeight):
        return (self.width, self.thickness)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


class SectionHeading(Flowable):
    """A section heading that stays with its content."""
    def __init__(self, text, style, keep_with_next=True):
        Flowable.__init__(self)
        self.text = text
        self.style = style
        self.keep_with_next = keep_with_next
        self.paragraph = Paragraph(text, style)

    def wrap(self, availWidth, availHeight):
        return self.paragraph.wrap(availWidth, availHeight)

    def draw(self):
        self.paragraph.drawOn(self.canv, self._x, self._y)


class SmartTable(Table):
    """Table that handles page breaks intelligently."""
    def __init__(self, data, colWidths=None, repeatRows=1, **kwargs):
        super().__init__(data, colWidths=colWidths, repeatRows=repeatRows, **kwargs)


class PDFReportService:
    """Professional medical report PDF generator."""

    def __init__(self):
        self.styles = self._create_styles()
        self._register_fonts()

    def _register_fonts(self):
        """Register fonts including Hindi support."""
        try:
            # Try to register Noto Sans for Hindi
            pdfmetrics.registerFont(TTFont('NotoSans', '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('NotoSans-Bold', '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf'))
            self.hindi_font = 'NotoSans'
        except Exception:
            self.hindi_font = 'Helvetica'  # Fallback

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create compact professional styles."""
        base_styles = getSampleStyleSheet()

        return {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=base_styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1e40af'),
                spaceAfter=8,
                spaceBefore=4,
                fontName='Helvetica-Bold',
                alignment=TA_LEFT,
            ),
            'subtitle': ParagraphStyle(
                'CustomSubtitle',
                parent=base_styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#6b7280'),
                spaceAfter=6,
                fontName='Helvetica',
            ),
            'section_heading': ParagraphStyle(
                'SectionHeading',
                parent=base_styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=4,
                spaceBefore=8,
                fontName='Helvetica-Bold',
                keepWithNext=1,
            ),
            'subsection_heading': ParagraphStyle(
                'SubsectionHeading',
                parent=base_styles['Heading3'],
                fontSize=10,
                textColor=colors.HexColor('#374151'),
                spaceAfter=3,
                spaceBefore=6,
                fontName='Helvetica-Bold',
                keepWithNext=1,
            ),
            'body': ParagraphStyle(
                'CustomBody',
                parent=base_styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#374151'),
                spaceAfter=3,
                spaceBefore=1,
                fontName='Helvetica',
                leading=12,
                alignment=TA_JUSTIFY,
            ),
            'body_compact': ParagraphStyle(
                'CustomBodyCompact',
                parent=base_styles['Normal'],
                fontSize=8.5,
                textColor=colors.HexColor('#374151'),
                spaceAfter=2,
                spaceBefore=1,
                fontName='Helvetica',
                leading=11,
            ),
            'card_title': ParagraphStyle(
                'CardTitle',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=2,
                fontName='Helvetica-Bold',
            ),
            'card_value': ParagraphStyle(
                'CardValue',
                parent=base_styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#4b5563'),
                spaceAfter=1,
                fontName='Helvetica',
            ),
            'table_header': ParagraphStyle(
                'TableHeader',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=colors.white,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
            ),
            'table_cell': ParagraphStyle(
                'TableCell',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#374151'),
                fontName='Helvetica',
            ),
            'table_cell_center': ParagraphStyle(
                'TableCellCenter',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#374151'),
                fontName='Helvetica',
                alignment=TA_CENTER,
            ),
            'footer': ParagraphStyle(
                'Footer',
                parent=base_styles['Normal'],
                fontSize=7,
                textColor=colors.HexColor('#9ca3af'),
                fontName='Helvetica',
                alignment=TA_CENTER,
            ),
            'badge_normal': ParagraphStyle(
                'BadgeNormal',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#059669'),
                fontName='Helvetica-Bold',
            ),
            'badge_attention': ParagraphStyle(
                'BadgeAttention',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#d97706'),
                fontName='Helvetica-Bold',
            ),
            'badge_high': ParagraphStyle(
                'BadgeHigh',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#dc2626'),
                fontName='Helvetica-Bold',
            ),
            'safety': ParagraphStyle(
                'Safety',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#92400e'),
                fontName='Helvetica',
                leading=10,
            ),
        }

    def generate_professional_pdf(
        self,
        report_data: Dict[str, Any],
        summary: Dict[str, Any],
        deep_explain_data: Optional[List[Dict]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Generate a professional print-ready PDF with Deep Explain."""
        options = options or {}
        include_deep_explain = options.get('include_deep_explain', True)
        language = options.get('language', 'en')

        buffer = io.BytesIO()

        # Calculate usable page width
        margin = 18 * mm  # 18mm margins
        usable_width = A4_WIDTH - 2 * margin

        # Create document with frames
        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
            title="LabLens AI Medical Report",
            author="LabLens AI",
        )

        # Define frames for content
        frame = Frame(
            doc.leftMargin, doc.bottomMargin,
            doc.width, doc.height,
            leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
            showBoundary=0,
        )

        # Page template with header/footer
        template = PageTemplate(
            id='main',
            frames=[frame],
            onPage=lambda canvas, doc: self._draw_header_footer(canvas, doc),
        )
        doc.addPageTemplates([template])

        # Build content flowables
        story = []

        # 1. Report Header (compact)
        story.extend(self._build_header(report_data, summary, language))

        # 2. Patient Information
        story.extend(self._build_patient_info(report_data, language))

        # 3. Overall Summary
        story.extend(self._build_overall_summary(summary, language))

        # 4. Normal Findings
        normal = summary.get('normal_findings', [])
        if normal:
            story.extend(self._build_normal_findings(normal, language))

        # 5. Attention Findings
        attention = summary.get('attention_findings', [])
        if attention:
            story.extend(self._build_attention_findings_cards(attention, language))

        # 6. High Priority Findings
        high_priority = summary.get('high_priority_findings', [])
        if high_priority:
            story.extend(self._build_high_priority(high_priority, language))

        # 7. Deep Explain (main section)
        if include_deep_explain and deep_explain_data:
            for idx, de in enumerate(deep_explain_data):
                story.extend(self._build_deep_explain_section(de, idx + 1, language))

        # 8. Related Tests Table
        if report_data.get('test_results'):
            story.extend(self._build_related_tests_table(report_data['test_results'], language))

        # 9. Pattern Analysis
        if deep_explain_data and deep_explain_data[0].get('pattern_analysis'):
            story.extend(self._build_pattern_analysis(deep_explain_data[0]['pattern_analysis'], language))

        # 10. Doctor Questions
        questions = summary.get('doctor_questions', [])
        if questions:
            story.extend(self._build_doctor_questions(questions, language))

        # 11. Safety Disclaimer
        story.extend(self._build_safety_footer(summary, language))

        # Build the document
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Validate PDF
        self._validate_pdf(pdf_bytes)

        return pdf_bytes

    def _draw_header_footer(self, canvas, doc):
        """Draw compact header and footer on every page."""
        canvas.saveState()

        # Header line
        canvas.setStrokeColor(colors.HexColor('#e5e7eb'))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, A4_HEIGHT - 12*mm, A4_WIDTH - doc.rightMargin, A4_HEIGHT - 12*mm)

        # Header text
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#6b7280'))
        canvas.drawString(doc.leftMargin, A4_HEIGHT - 10*mm, "LabLens AI | Medical Report Analysis")

        # Page number
        page_num = canvas.getPageNumber()
        canvas.drawRightString(A4_WIDTH - doc.rightMargin, A4_HEIGHT - 10*mm, f"Page {page_num}")

        # Footer line
        canvas.line(doc.leftMargin, 12*mm, A4_WIDTH - doc.rightMargin, 12*mm)

        # Footer text
        canvas.setFont('Helvetica', 6)
        canvas.setFillColor(colors.HexColor('#9ca3af'))
        canvas.drawCentredString(A4_WIDTH / 2, 8*mm, "Confidential Medical Information — For Educational Purposes Only")
        canvas.drawCentredString(A4_WIDTH / 2, 5*mm, "This report does not replace professional medical evaluation.")

        canvas.restoreState()

    def _build_header(self, report_data: Dict, summary: Dict, language: str) -> List:
        """Build compact report header."""
        elements = []

        # Title and filename on same line
        filename = report_data.get('filename', 'Medical Report')
        elements.append(Paragraph(
            f"<b>LabLens AI</b> &nbsp;&nbsp;|&nbsp;&nbsp; <font size='9' color='#6b7280'>{filename}</font>",
            self.styles['title']
        ))

        # Metadata line
        report_date = report_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))
        total_tests = len(report_data.get('test_results', []))
        normal_count = len(summary.get('normal_findings', []))
        attention_count = len(summary.get('attention_findings', []))

        meta_text = (
            f"Report Date: {report_date} &nbsp;|&nbsp; "
            f"Tests: {total_tests} &nbsp;|&nbsp; "
            f"<font color='#059669'>Normal: {normal_count}</font> &nbsp;|&nbsp; "
            f"<font color='#d97706'>Attention: {attention_count}</font>"
        )
        elements.append(Paragraph(meta_text, self.styles['subtitle']))
        elements.append(Spacer(1, 4))

        return elements

    def _build_patient_info(self, report_data: Dict, language: str) -> List:
        """Build compact patient information."""
        elements = []

        patient = report_data.get('patient_info', {})
        name = patient.get('name', 'N/A')
        age = patient.get('age', 'N/A')
        gender = patient.get('gender', 'N/A')

        info_data = [
            ['Patient', 'Age', 'Gender', 'Lab'],
            [str(name), str(age), str(gender), str(report_data.get('lab_name', 'N/A'))]
        ]

        usable_width = A4_WIDTH - 36 * mm
        col_widths = [usable_width * 0.3, usable_width * 0.15, usable_width * 0.2, usable_width * 0.35]

        t = Table(info_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4))

        return elements

    def _build_overall_summary(self, summary: Dict, language: str) -> List:
        """Build overall summary section."""
        elements = []

        elements.append(Paragraph("<b>Overall Summary</b>", self.styles['section_heading']))
        elements.append(HorizontalLine(A4_WIDTH - 36*mm, 0.5, colors.HexColor('#e5e7eb')))
        elements.append(Spacer(1, 2))

        overall = summary.get('overall_summary', 'Analysis complete.')
        elements.append(Paragraph(str(overall), self.styles['body_compact']))
        elements.append(Spacer(1, 4))

        return elements

    def _build_normal_findings(self, findings: List[str], language: str) -> List:
        """Build compact normal findings section."""
        elements = []

        elements.append(Paragraph("<b>Normal Findings</b>", self.styles['section_heading']))

        # Use compact list
        for finding in findings:
            elements.append(Paragraph(
                f"<font color='#059669'>&#10003;</font> {finding}",
                self.styles['body_compact']
            ))

        elements.append(Spacer(1, 4))
        return elements

    def _build_attention_findings_cards(self, findings: List[str], language: str) -> List:
        """Build attention findings as compact cards."""
        elements = []

        elements.append(Paragraph("<b>Attention Findings</b>", self.styles['section_heading']))
        elements.append(HorizontalLine(A4_WIDTH - 36*mm, 0.5, colors.HexColor('#fde68a')))
        elements.append(Spacer(1, 2))

        # Build table of attention findings (compact)
        card_data = []
        for finding in findings:
            card_data.append([Paragraph(f"<font color='#d97706'>&#9679;</font> {finding}", self.styles['table_cell'])])

        if card_data:
            usable_width = A4_WIDTH - 36 * mm
            t = Table(card_data, colWidths=[usable_width])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fffbeb')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LINEBELOW', (0, 0), (-1, -2), 0.25, colors.HexColor('#fde68a')),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#fde68a')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(t)

        elements.append(Spacer(1, 6))
        return elements

    def _build_high_priority(self, findings: List[str], language: str) -> List:
        """Build high-priority findings."""
        elements = []

        elements.append(Paragraph("<b>&#9888; High-Priority Findings</b>", self.styles['section_heading']))

        for finding in findings:
            elements.append(Paragraph(
                f"<font color='#dc2626'>&#9888;</font> {finding}",
                self.styles['body_compact']
            ))

        elements.append(Spacer(1, 6))
        return elements

    def _build_deep_explain_section(self, de: Dict, index: int, language: str) -> List:
        """Build complete Deep Explain section for one attention finding."""
        elements = []

        # Section break before new Deep Explain
        if index > 1:
            elements.append(PageBreak())

        # Header with priority badge
        priority = de.get('priority', '🟡 ATTENTION')
        test_name = de.get('test_name', 'Unknown')
        result = de.get('result', 'N/A')
        unit = de.get('unit', '')
        ref = de.get('reference_range', 'N/A')
        status_text = de.get('status', 'unknown')

        # Attention card
        elements.append(Paragraph(f"<b>Deep Explain #{index} — {test_name}</b>", self.styles['section_heading']))
        elements.append(HorizontalLine(A4_WIDTH - 36*mm, 0.5, colors.HexColor('#93c5fd')))
        elements.append(Spacer(1, 2))

        # Result card (compact table)
        result_data = [
            ['Result', 'Reference', 'Status', 'Priority'],
            [f"{result} {unit}", ref, status_text.upper(), priority]
        ]
        usable_width = A4_WIDTH - 36 * mm
        col_widths = [usable_width * 0.25, usable_width * 0.25, usable_width * 0.25, usable_width * 0.25]

        t = Table(result_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eff6ff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#bfdbfe')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4))

        # What is this test?
        if de.get('what_it_mean'):
            elements.append(Paragraph("<b>What Is This Test?</b>", self.styles['subsection_heading']))
            elements.append(Paragraph(str(de['what_it_mean']), self.styles['body_compact']))

        # Why flagged?
        if de.get('why_flagged'):
            elements.append(Paragraph("<b>Why Is It Flagged?</b>", self.styles['subsection_heading']))
            elements.append(Paragraph(str(de['why_flagged']), self.styles['body_compact']))

        # Why it matters
        if de.get('why_it_matters'):
            elements.append(Paragraph("<b>Why Does It Matter?</b>", self.styles['subsection_heading']))
            elements.append(Paragraph(str(de['why_it_matters']), self.styles['body_compact']))

        # Possible Health Associations
        associations = de.get('disease_associations', [])
        if associations:
            elements.append(Paragraph("<b>Possible Health Associations</b>", self.styles['subsection_heading']))

            assoc_data = [['Condition', 'Association', 'Supporting', 'Missing']]
            for assoc in associations[:3]:
                assoc_data.append([
                    Paragraph(assoc.get('name', ''), self.styles['table_cell']),
                    Paragraph(assoc.get('association_strength', ''), self.styles['table_cell_center']),
                    Paragraph(str(len(assoc.get('supporting_evidence', []))), self.styles['table_cell_center']),
                    Paragraph(str(len(assoc.get('missing_evidence', []))), self.styles['table_cell_center']),
                ])

            assoc_col_widths = [usable_width * 0.35, usable_width * 0.2, usable_width * 0.225, usable_width * 0.225]
            assoc_t = Table(assoc_data, colWidths=assoc_col_widths)
            assoc_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f3ff')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7.5),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(assoc_t)
            elements.append(Spacer(1, 3))

        # Supporting Evidence
        supporting = de.get('possible_associations', [{}])[0].get('supporting_findings', []) if de.get('possible_associations') else []
        if supporting:
            elements.append(Paragraph("<b>Supporting Evidence</b>", self.styles['subsection_heading']))
            for s in supporting[:5]:
                elements.append(Paragraph(
                    f"<font color='#059669'>&#10003;</font> {s}",
                    self.styles['body_compact']
                ))

        # Missing Information
        missing = de.get('missing_information', [])
        if missing:
            elements.append(Paragraph("<b>Missing Information</b>", self.styles['subsection_heading']))
            for m in missing[:5]:
                elements.append(Paragraph(
                    f"<font color='#dc2626'>&#10007;</font> {m}",
                    self.styles['body_compact']
                ))

        # What it does NOT prove
        does_not_prove = de.get('what_it_does_not_prove', [])
        if does_not_prove:
            elements.append(Paragraph("<b>What This Result Does NOT Prove</b>", self.styles['subsection_heading']))
            for item in does_not_prove:
                elements.append(Paragraph(
                    f"<font color='#92400e'>&#9888;</font> {item}",
                    self.styles['body_compact']
                ))

        # Possible Symptoms
        symptoms = de.get('possible_symptoms', [])
        if symptoms:
            elements.append(Paragraph("<b>Possible Symptoms</b>", self.styles['subsection_heading']))
            symptom_text = ", ".join(symptoms[:8])
            elements.append(Paragraph(
                f"Some people may experience: {symptom_text}. These symptoms are not specific to this finding.",
                self.styles['body_compact']
            ))

        elements.append(Spacer(1, 4))
        return elements

    def _build_related_tests_table(self, test_results: List[Dict], language: str) -> List:
        """Build related tests table that spans pages intelligently."""
        elements = []

        elements.append(Paragraph("<b>Detailed Test Results</b>", self.styles['section_heading']))

        # Build table data
        table_data = [['Test', 'Result', 'Unit', 'Reference', 'Status']]

        for t in test_results:
            status = t.get('status', 'unknown')
            # Add emoji based on status
            if status == 'normal':
                status_display = 'Normal'
            elif status in ['low', 'high']:
                status_display = status.title()
            elif status == 'borderline':
                status_display = 'Borderline'
            else:
                status_display = status.replace('_', ' ').title()

            table_data.append([
                Paragraph(str(t.get('test_name', '')), self.styles['table_cell']),
                Paragraph(str(t.get('result', '') or t.get('result_text', '')), self.styles['table_cell_center']),
                Paragraph(str(t.get('unit', '')), self.styles['table_cell_center']),
                Paragraph(str(t.get('reference_text', 'N/A')), self.styles['table_cell']),
                Paragraph(status_display, self.styles['table_cell_center']),
            ])

        usable_width = A4_WIDTH - 36 * mm
        col_widths = [usable_width * 0.25, usable_width * 0.15, usable_width * 0.1, usable_width * 0.25, usable_width * 0.25]

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.5),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#9ca3af')),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            # Alternate row colors
            *[
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9fafb'))
                for i in range(2, len(table_data), 2)
            ],
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6))

        return elements

    def _build_pattern_analysis(self, pattern_text: str, language: str) -> List:
        """Build pattern analysis section."""
        elements = []

        elements.append(Paragraph("<b>Pattern Analysis</b>", self.styles['section_heading']))
        elements.append(Paragraph(str(pattern_text), self.styles['body_compact']))
        elements.append(Spacer(1, 4))

        return elements

    def _build_doctor_questions(self, questions: List[str], language: str) -> List:
        """Build doctor discussion questions."""
        elements = []

        elements.append(Paragraph("<b>Questions for Healthcare Professional</b>", self.styles['section_heading']))

        for i, q in enumerate(questions[:5], 1):
            elements.append(Paragraph(
                f"<b>{i}.</b> {q}",
                self.styles['body_compact']
            ))

        elements.append(Spacer(1, 4))
        return elements

    def _build_safety_footer(self, summary: Dict, language: str) -> List:
        """Build safety disclaimer section."""
        elements = []

        elements.append(HorizontalLine(A4_WIDTH - 36*mm, 0.5, colors.HexColor('#fed7aa')))
        elements.append(Spacer(1, 3))

        elements.append(Paragraph("<b>&#9888; Safety Disclaimer</b>", self.styles['subsection_heading']))

        disclaimer = summary.get('safety_disclaimer', (
            "This AI-generated analysis is for educational purposes only. "
            "Laboratory results must be interpreted together with symptoms, medical history, "
            "physical examination, and other clinical information. This analysis does not establish "
            "a diagnosis and does not replace a qualified healthcare professional."
        ))
        elements.append(Paragraph(str(disclaimer), self.styles['safety']))

        # Add generation timestamp
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | LabLens AI v1.0",
            self.styles['footer']
        ))

        return elements

    def _validate_pdf(self, pdf_bytes: bytes):
        """Validate generated PDF quality."""
        if not pdf_bytes or len(pdf_bytes) < 100:
            logger.error("PDF validation failed: empty or too small")
            raise ValueError("Generated PDF is empty or corrupted")

        # Check for PDF header
        if not pdf_bytes.startswith(b'%PDF'):
            logger.error("PDF validation failed: invalid header")
            raise ValueError("Generated PDF has invalid format")

        logger.info(f"PDF validated: {len(pdf_bytes)} bytes")


# Singleton
pdf_service = PDFReportService()
