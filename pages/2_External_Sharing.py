import streamlit as st
import pandas as pd
import sys, os

st.set_page_config(page_title="External Sharing - GWS Auditor", page_icon="🔗", layout="wide")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import apply_styles, sidebar_demo_toggle, get_data

apply_styles()
sidebar_demo_toggle()

data = get_data()
records = data.get("external_sharing", [])

st.markdown("## External Sharing Audit")
st.markdown("Drive items shared outside the organization or with unrestricted link access.")
st.markdown("---")

# Summary metrics
anyone_count = sum(1 for r in records if r["share_type"] == "anyone_with_link")
external_count = sum(1 for r in records if r["share_type"] == "external_member")
gmail_count = sum(1 for r in records if r["share_type"] == "personal_gmail")

c1, c2, c3 = st.columns(3)
c1.metric("Anyone With Link", anyone_count, delta=f"-{anyone_count} to remediate", delta_color="inverse")
c2.metric("External Member Access", external_count)
c3.metric("Personal Gmail Access", gmail_count, delta=f"-{gmail_count} to remediate", delta_color="inverse")

st.markdown("---")

# Filter
share_type_labels = {
    "All": None,
    "Anyone With Link": "anyone_with_link",
    "External Member": "external_member",
    "Personal Gmail": "personal_gmail",
}

selected_label = st.selectbox("Filter by Share Type", list(share_type_labels.keys()))
filter_val = share_type_labels[selected_label]

filtered = records if filter_val is None else [r for r in records if r["share_type"] == filter_val]

# Display table
if not filtered:
    st.info("No records match the selected filter.")
else:
    df = pd.DataFrame(filtered)
    df["share_type"] = df["share_type"].map({
        "anyone_with_link": "Anyone With Link",
        "external_member": "External Member",
        "personal_gmail": "Personal Gmail",
    })
    df = df.rename(columns={
        "file_name": "File / Drive",
        "owner_ou": "Owner OU",
        "share_type": "Share Type",
        "last_modified": "Last Modified",
        "severity": "Severity",
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

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Last Modified": st.column_config.DateColumn("Last Modified", format="YYYY-MM-DD"),
        },
    )

    # CSV export
    csv = df.to_csv(index=False)
    st.download_button(
        label="Export CSV",
        data=csv,
        file_name="external_sharing_findings.csv",
        mime="text/csv",
    )

st.markdown("---")
st.markdown(
    '<span style="color:#64748b;font-size:0.82em;">'
    "Best Practice: Restrict all Drive sharing to domain users. "
    "Disable 'Anyone with the link' sharing at the domain level unless explicitly required."
    "</span>",
    unsafe_allow_html=True,
)
