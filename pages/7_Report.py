import streamlit as st
import pandas as pd
import sys, os

st.set_page_config(page_title="Report - GWS Auditor", page_icon="📄", layout="wide")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import apply_styles, sidebar_demo_toggle, get_data, get_findings, get_scores

apply_styles()
sidebar_demo_toggle()

data = get_data()
findings = get_findings()
scores = get_scores()

st.markdown("## Audit Report")
st.markdown(
    f"Full findings export for **{data.get('org_name')}** - {data.get('audit_timestamp', '')[:10]}"
)
st.markdown("---")

# Summary
overall = scores.get("overall", 0)
failing = [f for f in findings if not f["compliant"]]
critical_count = sum(1 for f in failing if f["severity"] == "Critical")
high_count = sum(1 for f in failing if f["severity"] == "High")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Overall Score", f"{overall}%")
c2.metric("Total Findings", len(failing))
c3.metric("Critical", critical_count)
c4.metric("High", high_count)

st.markdown("---")

# Full findings table (failing only for export)
st.markdown("### All Findings")

severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Pass": 4}
failing_sorted = sorted(failing, key=lambda f: severity_order.get(f["severity"], 99))

if not failing_sorted:
    st.success("No findings to report. All checks passed.")
else:
    df = pd.DataFrame(failing_sorted)[["category", "severity", "description", "recommended_action"]]
    df = df.rename(columns={
        "category": "Category",
        "severity": "Severity",
        "description": "Description",
        "recommended_action": "Recommended Action",
    })

    def color_severity(val):
        colors = {
            "Critical": "color: #ef4444; font-weight: 600",
            "High": "color: #f97316; font-weight: 600",
            "Medium": "color: #eab308; font-weight: 600",
            "Low": "color: #22c55e; font-weight: 600",
        }
        return colors.get(val, "")

    styled = df.style.map(color_severity, subset=["Severity"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Export")

    col_csv, col_pdf = st.columns(2)

    # CSV export
    with col_csv:
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"gws_audit_{data.get('org_name', 'report').replace(' ', '_').lower()}_{data.get('audit_timestamp', '')[:10]}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("One row per finding. Includes category, severity, description, and recommended action.")

    # PDF export
    with col_pdf:
        try:
            from engine.report_generator import generate_pdf
            pdf_bytes = generate_pdf(data, findings, scores)
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"gws_audit_{data.get('org_name', 'report').replace(' ', '_').lower()}_{data.get('audit_timestamp', '')[:10]}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.caption("Formatted report with scores, finding details, and recommendations.")
        except ImportError:
            st.warning("PDF export requires fpdf2. Run: pip install fpdf2")
        except Exception as exc:
            st.error(f"PDF generation error: {exc}")

st.markdown("---")

# Category breakdown table
st.markdown("### Score by Category")
cat_rows = [
    {"Category": cat, "Score": f"{score}%", "Status": "Compliant" if score >= 90 else "Needs Attention"}
    for cat, score in scores.get("by_category", {}).items()
]
cat_df = pd.DataFrame(cat_rows)

def color_cat_status(val):
    if val == "Compliant":
        return "color: #22c55e"
    return "color: #f97316; font-weight: 600"

styled_cat = cat_df.style.map(color_cat_status, subset=["Status"])
st.dataframe(styled_cat, use_container_width=True, hide_index=True)
