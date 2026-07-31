# ==================================================================================== #
# This is the report_generator.py module. The final stage of our reconnaissance.       #
# Migrated to ReportLab to eliminate rigid FPDF coordinate and text-overflow crashes.  #
# Automatically handles text flow, wrapping, and table structures natively.            #
# ==================================================================================== #

import os
import time
import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = logging.getLogger(__name__)

async def generate_scan_report(scan_memory: dict, format_type: str = "pdf") -> str:
    """Generate professional PDF using ReportLab from raw JSON memory."""
    
    if format_type.lower() != "pdf":
        return None
    
    report_id = str(int(time.time()))
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    os.makedirs("generated_reports", exist_ok=True)
    filename = f"generated_reports/Reconnator_Report_{report_id}.pdf"
    
    # Inisialisasi dokumen ReportLab
    doc = SimpleDocTemplate(
        filename, 
        pagesize=letter, 
        rightMargin=30, 
        leftMargin=30, 
        topMargin=30, 
        bottomMargin=30
    )
    story = []
    
    styles = getSampleStyleSheet()
    
    # Styling khusus laporan
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor("#C80000"),
        alignment=1, # Center
        spaceAfter=10
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.white,
        backColor=colors.HexColor("#323232"),
        spaceBefore=10,
        spaceAfter=5,
        leftIndent=5
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        leading=13
    )
    
    meta_head_style = ParagraphStyle(
        'MetaHead',
        parent=body_style,
        fontSize=11,
        fontName="Helvetica-Bold",
        backColor=colors.HexColor("#E6E6E6")
    )

    story.append(Paragraph("RECONNATOR VULNERABILITY REPORT", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#C80000"), spaceAfter=15))
    story.append(Paragraph(" SCAN METADATA SUMMARY", meta_head_style))
    story.append(Spacer(1, 5))
    
    used_tools = set()
    for k in scan_memory.keys():
        if k == "_metadata":
            continue
        engine_name = k.split("_")[0] if "_" in k else k
        used_tools.add(engine_name.upper())
    tools_str = ", ".join(list(used_tools)) if used_tools else "Unknown Engine"

    metadata = scan_memory.get("_metadata", {})
    duration = metadata.get("duration", "Pending Engine Integration (N/A)")
    
    meta_data = [
        [Paragraph("<b>Report ID:</b>", body_style), Paragraph(f"REC-{report_id}", body_style)],
        [Paragraph("<b>Date / Time:</b>", body_style), Paragraph(f"{current_time} (Server Time)", body_style)],
        [Paragraph("<b>Engines Used:</b>", body_style), Paragraph(tools_str, body_style)],
        [Paragraph("<b>Total Duration:</b>", body_style), Paragraph(str(duration), body_style)],
    ]
    
    t = Table(meta_data, colWidths=[90, 430])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    for target_key, vulnerabilities in scan_memory.items():
        if target_key == "_metadata":
            continue 

        story.append(Paragraph(f" TARGET DATA: {target_key.upper()} ", section_style))
        story.append(Spacer(1, 5))

        if isinstance(vulnerabilities, list) and len(vulnerabilities) > 0:
            for item in vulnerabilities:
                info = item.get("info", {})
                vuln_name = info.get("name", "Unknown Vulnerability")
                severity = info.get("severity", "INFO").upper()
                target_url = item.get("url", item.get("host", "Unknown Host"))

                color_map = {
                    "CRITICAL": "#C80000",
                    "HIGH": "#C80000",
                    "MEDIUM": "#C86400",
                    "LOW": "#0EFF22",
                    "INFO": "#0064C8"
                }
                sev_color = color_map.get(severity, "#0064C8")
                
                vuln_style = ParagraphStyle(
                    'VulnTitle',
                    parent=body_style,
                    fontSize=10,
                    fontName="Helvetica-Bold",
                    textColor=colors.HexColor(sev_color)
                )
                
                story.append(Paragraph(f"<b>[{severity}]</b> {vuln_name}", vuln_style))
                story.append(Paragraph(f"<b>Endpoint :</b> {target_url}", body_style))
                
                refs = info.get("reference", [])
                if refs:
                    story.append(Paragraph(f"<b>Reference:</b> {refs[0]}", body_style))
                
                story.append(Spacer(1, 4))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceAfter=6))
        else:
            story.append(Paragraph("<i>No active vulnerabilities found or parsing format unsupported.</i>", body_style))
            story.append(Spacer(1, 10))

    doc.build(story)
    
    return filename