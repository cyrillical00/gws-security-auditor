import streamlit as st
import pandas as pd
import sys, os

st.set_page_config(page_title="DLP Coverage - GWS Auditor", page_icon="🛡", layout="wide")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import apply_styles, sidebar_demo_toggle, get_data

apply_styles()
sidebar_demo_toggle()

data = get_data()
dlp = data.get("dlp", {})

st.markdown("## DLP Coverage")
st.markdown("Data Loss Prevention rule inventory and organizational unit coverage gaps.")
st.markdown("---")

rules = dlp.get("rules", [])
all_ous = dlp.get("all_ous", [])
uncovered_ous = dlp.get("uncovered_ous", [])
audit_only_rules = dlp.get("audit_only_rules", [])

enforcing_count = sum(1 for r in rules if r.get("mode") == "enforcing")
audit_only_count = len(audit_only_rules)
uncovered_count = len(uncovered_ous)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Active DLP Rules", len(rules))
c2.metric("Enforcing", enforcing_count)
c3.metric("Audit-Only (Not Blocking)", audit_only_count)
c4.metric("OUs With No Coverage", uncovered_count)

st.markdown("---")

# Rule inventory
st.markdown("### DLP Rule Inventory")
if not rules:
    st.info("No DLP rules found. This may indicate DLP is not configured or live mode data is unavailable.")
else:
    for rule in rules:
        mode = rule.get("mode", "unknown")
        is_audit = mode == "audit_only"
        border_color = "#eab308" if is_audit else "#22c55e"
        mode_label = "AUDIT ONLY" if is_audit else "ENFORCING"
        mode_color = "#eab308" if is_audit else "#22c55e"
        ous_covered = ", ".join(rule.get("ous_covered", []))

        st.markdown(
            f'<div style="background:#0d0d12;border-left:3px solid {border_color};'
            f'padding:10px 14px;margin-bottom:8px;border-radius:0 4px 4px 0;">'
            f'<b style="color:#e2e8f0;">{rule["name"]}</b> '
            f'<span style="color:{mode_color};font-weight:600;font-size:0.85em;">[{mode_label}]</span><br>'
            f'<span style="color:#94a3b8;font-size:0.82em;">OUs Covered: {ous_covered or "None"}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("---")

# OU coverage gap table
st.markdown("### OU Coverage Gaps")
if not all_ous:
    st.info("No OU data available.")
else:
    coverage_rows = []
    covered_set = set()
    for rule in rules:
        for ou in rule.get("ous_covered", []):
            covered_set.add(ou)

    for ou in all_ous:
        covered = ou in covered_set
        coverage_rows.append({
            "OU": ou,
            "Covered": "Yes" if covered else "No",
            "Status": "Compliant" if covered else "Gap - No DLP Coverage",
        })

    cov_df = pd.DataFrame(coverage_rows)

    def color_status(val):
        if val == "Compliant":
            return "color: #22c55e"
        return "color: #f97316; font-weight: 600"

    styled = cov_df.style.applymap(color_status, subset=["Status"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

st.markdown("---")

# Audit-only rules warning
if audit_only_rules:
    st.markdown("### Audit-Only Rules Requiring Attention")
    for rule in audit_only_rules:
        st.warning(
            f"**{rule['name']}** is in audit-only mode and is not actively blocking policy violations.\n\n"
            f"Recommendation: {rule['recommendation']}"
        )

st.markdown("---")
st.markdown(
    '<span style="color:#64748b;font-size:0.82em;">'
    "Best Practice: Ensure all OUs with access to regulated data (PCI, PII, IP) are covered by "
    "at least one enforcing DLP rule. Audit-only mode should be used only during initial rollout."
    "</span>",
    unsafe_allow_html=True,
)
