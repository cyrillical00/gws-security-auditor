import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

st.set_page_config(page_title="MFA Enforcement - GWS Auditor", page_icon="🔐", layout="wide")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import apply_styles, sidebar_demo_toggle, get_data

apply_styles()
sidebar_demo_toggle()

data = get_data()
mfa = data.get("mfa", {})

st.markdown("## MFA / 2SV Enforcement")
st.markdown("2-Step Verification enrollment by Organizational Unit against the 95% compliance threshold.")
st.markdown("---")

overall_pct = mfa.get("overall_enrollment_pct", 0)
threshold = mfa.get("threshold_pct", 95.0)
total_users = mfa.get("total_users", 0)
enrolled_users = mfa.get("enrolled_users", 0)
unenrolled_users = mfa.get("unenrolled_users", [])
undocumented = [u for u in unenrolled_users if not u.get("exception_documented", False)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Overall 2SV Enrollment", f"{overall_pct:.1f}%", help=f"Threshold: {threshold:.0f}%")
c2.metric("Enrolled Users", enrolled_users)
c3.metric("Not Enrolled", total_users - enrolled_users)
c4.metric("No Exception Documented", len(undocumented))

if overall_pct < threshold:
    st.warning(
        f"Overall enrollment ({overall_pct:.1f}%) is below the {threshold:.0f}% compliance threshold. "
        f"{total_users - enrolled_users} users still need to enroll."
    )
else:
    st.success(f"Overall 2SV enrollment ({overall_pct:.1f}%) meets the {threshold:.0f}% threshold.")

st.markdown("---")

# OU bar chart
by_ou = mfa.get("by_ou", [])
ou_names = [ou["ou"] for ou in by_ou]
ou_pcts = [ou["pct"] for ou in by_ou]
ou_colors = [
    "#22c55e" if p >= threshold else "#f97316" if p >= 80 else "#ef4444"
    for p in ou_pcts
]

fig = go.Figure(
    go.Bar(
        x=ou_names,
        y=ou_pcts,
        marker_color=ou_colors,
        text=[f"{p:.1f}%" for p in ou_pcts],
        textposition="outside",
        textfont=dict(color="#e2e8f0", family="IBM Plex Mono"),
    )
)
fig.add_hline(
    y=threshold,
    line_dash="dot",
    line_color="#22c55e",
    annotation_text=f"{threshold:.0f}% threshold",
    annotation_font_color="#22c55e",
)
fig.update_layout(
    title="2SV Enrollment by OU",
    plot_bgcolor="#050508",
    paper_bgcolor="#050508",
    font=dict(color="#e2e8f0", family="IBM Plex Mono"),
    yaxis=dict(range=[0, 115], gridcolor="#1e1e2e", zeroline=False, ticksuffix="%"),
    xaxis=dict(gridcolor="#1e1e2e"),
    margin=dict(t=50, b=40, l=10, r=10),
    height=380,
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# OU detail table
st.markdown("### Enrollment by OU")
ou_df = pd.DataFrame(by_ou)
ou_df["Status"] = ou_df["pct"].apply(
    lambda p: "Compliant" if p >= threshold else "Below 80%" if p < 80 else "Below Threshold"
)
ou_df = ou_df.rename(columns={
    "ou": "OU",
    "enrolled": "Enrolled",
    "total": "Total",
    "pct": "Enrollment %",
})

def color_status(val):
    if val == "Compliant":
        return "color: #22c55e"
    if val == "Below 80%":
        return "color: #ef4444; font-weight: 600"
    return "color: #eab308; font-weight: 600"

styled_ou = ou_df.style.applymap(color_status, subset=["Status"])
st.dataframe(styled_ou, use_container_width=True, hide_index=True)

st.markdown("---")

# Users without 2SV
st.markdown("### Users Without 2SV")
if not unenrolled_users:
    st.success("All users are enrolled in 2SV.")
else:
    unenrolled_df = pd.DataFrame(unenrolled_users)
    unenrolled_df["exception_documented"] = unenrolled_df["exception_documented"].map(
        {True: "Yes", False: "No"}
    )
    unenrolled_df = unenrolled_df.rename(columns={
        "email": "Email",
        "ou": "OU",
        "exception_documented": "Exception Documented",
    })

    def color_exception(val):
        return "color: #22c55e" if val == "Yes" else "color: #f97316; font-weight: 600"

    styled_unenrolled = unenrolled_df.style.applymap(color_exception, subset=["Exception Documented"])
    st.dataframe(styled_unenrolled, use_container_width=True, hide_index=True)

    csv = unenrolled_df.to_csv(index=False)
    st.download_button(
        label="Export Unenrolled Users CSV",
        data=csv,
        file_name="mfa_unenrolled_users.csv",
        mime="text/csv",
    )

st.markdown("---")
st.markdown(
    '<span style="color:#64748b;font-size:0.82em;">'
    "Best Practice: Enforce 2SV for all OUs via Admin console Security settings. "
    "Set a grace period (e.g., 1 week) and send enrollment reminders before hard enforcement."
    "</span>",
    unsafe_allow_html=True,
)
