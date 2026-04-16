import streamlit as st
import pandas as pd
import sys, os

st.set_page_config(page_title="Admin Roles - GWS Auditor", page_icon="👤", layout="wide")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import apply_styles, sidebar_demo_toggle, get_data

apply_styles()
sidebar_demo_toggle()

data = get_data()
admins = data.get("admin_roles", [])

st.markdown("## Admin Role Assignments")
st.markdown("Review privileged accounts, inactive delegated admins, and service account escalations.")
st.markdown("---")

# Metrics
super_admins = [a for a in admins if a["role"] == "Super Admin"]
service_account_super = [a for a in super_admins if "Service Account" in a.get("ou", "")]
inactive_flagged = [a for a in admins if a["severity"] == "High"]
critical_flagged = [a for a in admins if a["severity"] == "Critical"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Super Admin Count", len(super_admins), help="Recommended maximum: 2")
c2.metric("Service Account Super Admins", len(service_account_super), delta=f"{len(service_account_super)} Critical" if service_account_super else None, delta_color="inverse")
c3.metric("Inactive Delegated Admins (90d)", len(inactive_flagged))
c4.metric("Total Flagged", len([a for a in admins if a["severity"]]))

st.markdown("---")

# Super admin count context
recommended = 2
if len(super_admins) > recommended:
    st.warning(
        f"{len(super_admins)} Super Admin accounts active. Best practice is {recommended} or fewer. "
        f"Review and remove Super Admin privileges from accounts that do not require full access."
    )
else:
    st.success(f"Super Admin count ({len(super_admins)}) is within the recommended limit.")

if service_account_super:
    st.error(
        f"CRITICAL: {len(service_account_super)} service account(s) hold the Super Admin role. "
        "This violates least-privilege principles and creates significant security risk."
    )

st.markdown("---")

# Table
df = pd.DataFrame(admins)
df = df.rename(columns={
    "email": "Email",
    "role": "Role",
    "last_login": "Last Login",
    "ou": "OU",
    "flag_reason": "Flag Reason",
    "severity": "Severity",
})

def color_severity(val):
    colors = {
        "Critical": "color: #ef4444; font-weight: 600; background-color: #1a0505",
        "High": "color: #f97316; font-weight: 600",
        "Medium": "color: #eab308; font-weight: 600",
        "Low": "color: #22c55e; font-weight: 600",
    }
    return colors.get(val, "")

styled = df.style.applymap(color_severity, subset=["Severity"])

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.markdown(
    '<span style="color:#64748b;font-size:0.82em;">'
    "Best Practice: Limit Super Admins to 2 named individuals. "
    "Disable or deprovision delegated admin accounts inactive for 90+ days. "
    "Never assign Super Admin to service accounts."
    "</span>",
    unsafe_allow_html=True,
)
