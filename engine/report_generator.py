"""
PDF report builder using fpdf2.
Produces a formatted security audit report from scored findings.
"""

from fpdf import FPDF
import io
from datetime import datetime

SEVERITY_COLORS = {
    "Critical": (239, 68, 68),
    "High": (249, 115, 22),
    "Medium": (234, 179, 8),
    "Low": (34, 197, 94),
    "Pass": (100, 116, 139),
}


class AuditReport(FPDF):
    def __init__(self, org_name: str, audit_timestamp: str):
        super().__init__()
        self.org_name = org_name
        self.audit_timestamp = audit_timestamp
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()

    def header(self):
        self.set_fill_color(5, 5, 8)
        self.rect(0, 0, 210, 20, "F")
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(34, 197, 94)
        self.set_y(6)
        self.cell(0, 8, "GWS Security Auditor", align="L", new_x="RIGHT", new_y="TOP")
        self.set_text_color(180, 180, 190)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 8, f"{self.org_name}  |  {self.audit_timestamp[:10]}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 100, 120)
        self.cell(0, 8, f"Page {self.page_no()} - Generated {datetime.utcnow().strftime('%Y-%m-%d')}", align="C")

    def title_section(self, text: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(34, 197, 94)
        self.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(34, 197, 94)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def section_heading(self, text: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(226, 232, 240)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")

    def score_row(self, category: str, score: int):
        self.set_font("Helvetica", "", 10)
        r, g, b = _score_color(score)
        self.set_text_color(200, 200, 210)
        self.cell(120, 7, category, new_x="RIGHT", new_y="TOP")
        self.set_text_color(r, g, b)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, f"{score}%", new_x="LMARGIN", new_y="NEXT")

    def finding_row(self, finding: dict):
        sev = finding["severity"]
        if sev == "Pass":
            return
        r, g, b = SEVERITY_COLORS.get(sev, (200, 200, 200))
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(r, g, b)
        self.cell(22, 6, f"[{sev}]", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(220, 220, 230)
        self.cell(50, 6, finding["category"], new_x="RIGHT", new_y="TOP")
        desc = finding["description"]
        if len(desc) > 65:
            desc = desc[:62] + "..."
        self.multi_cell(0, 6, desc, new_x="LMARGIN", new_y="NEXT")

    def recommendation_row(self, finding: dict):
        if finding["severity"] == "Pass" or not finding["recommended_action"]:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 165)
        self.set_x(20)
        action = finding["recommended_action"]
        if len(action) > 90:
            action = action[:87] + "..."
        self.multi_cell(0, 5, f"  Action: {action}", new_x="LMARGIN", new_y="NEXT")


def _score_color(score: int):
    if score >= 90:
        return (34, 197, 94)
    if score >= 70:
        return (234, 179, 8)
    return (239, 68, 68)


def generate_pdf(data: dict, findings: list, scores: dict) -> bytes:
    pdf = AuditReport(
        org_name=data.get("org_name", "Unknown Org"),
        audit_timestamp=data.get("audit_timestamp", ""),
    )

    # Cover section
    pdf.title_section("Security Audit Report")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(180, 180, 195)
    pdf.cell(0, 6, f"Organization: {data.get('org_name', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Total Users Audited: {data.get('total_users', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Audit Date: {data.get('audit_timestamp', '')[:10]}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Summary scores
    pdf.section_heading("Compliance Scores")
    overall = scores.get("overall", 0)
    r, g, b = _score_color(overall)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 12, f"Overall Score: {overall}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    for cat, score in scores.get("by_category", {}).items():
        pdf.score_row(cat, score)

    pdf.ln(4)

    # Findings by severity
    for sev in ["Critical", "High", "Medium", "Low"]:
        group = [f for f in findings if f["severity"] == sev and not f["compliant"]]
        if not group:
            continue
        pdf.section_heading(f"{sev} Findings ({len(group)})")
        for finding in group:
            pdf.finding_row(finding)
            pdf.recommendation_row(finding)
        pdf.ln(2)

    return bytes(pdf.output())
