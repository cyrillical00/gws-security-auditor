import streamlit as st
import pandas as pd
import sys, os

st.set_page_config(page_title="Vault Retention - GWS Auditor", page_icon="📦", layout="wide")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import apply_styles, sidebar_demo_toggle, get_data

apply_styles()
sidebar_demo_toggle()

data = get_data()
vault = data.get("vault", {})
suspended_users = data.get("suspended_users", [])

st.markdown("## Vault Retention Policies")
st.markdown("Retention rule coverage by Organizational Unit and suspended user access findings.")
st.markdown("---")

rules = vault.get("rules", [])
all_ous = vault.get("all_ous", [])
ous_without_rule = vault.get("ous_without_rule", [])
litigation_holds = vault.get("litigation_holds_count", 0)

ous_with_rule_count = len(all_ous) - len(ous_without_rule)

c1, c2, c3, c4 = st.columns(4)
c1.metric("OUs With Explicit Rule", ous_with_rule_count)
c2.metric("OUs Without Rule", len(ous_without_rule), delta=f"{len(ous_without_rule)} to remediate" if ous_without_rule else None, delta_color="inverse")
c3.metric("Active Litigation Holds", litigation_holds)
c4.metric("Suspended Users (Total)", len(suspended_users))

st.markdown("---")

# Retention rules table
st.markdown("### Retention Rules by OU")
if not rules:
    st.info("No Vault retention data available. Live mode requires Vault API access.")
else:
    rules_df = pd.DataFrame(rules)
    rules_df["retention_years"] = (rules_df["retention_days"] / 365).round(1)
    rules_df["explicit"] = rules_df["explicit"].map({True: "Yes", False: "No (Default)"})
    rules_df = rules_df.rename(columns={
        "ou": "OU",
        "service": "Service",
        "retention_days": "Retention (Days)",
        "retention_years": "Retention (Years)",
        "explicit": "Explicit Rule",
    })
    st.dataframe(rules_df, use_container_width=True, hide_index=True)

# OUs without rule
if ous_without_rule:
    st.markdown("---")
    st.markdown("### OUs Without Explicit Retention Rule")
    st.warning(
        f"{len(ous_without_rule)} OU(s) rely on the default policy with no explicit rule defined. "
        "Explicit rules ensure consistent, auditable coverage during litigation or compliance reviews."
    )
    gap_df = pd.DataFrame([{"OU": ou, "Status": "No Explicit Rule", "Severity": "Medium"} for ou in ous_without_rule])

    def color_sev(val):
        return "color: #eab308; font-weight: 600"

    styled_gap = gap_df.style.applymap(color_sev, subset=["Severity"])
    st.dataframe(styled_gap, use_container_width=True, hide_index=True)

st.markdown("---")

# Litigation holds status
st.markdown("### Litigation Hold Status")
if litigation_holds == 0:
    st.info("No active litigation holds. This is informational only and is not a finding.")
else:
    st.success(f"{litigation_holds} active litigation hold(s) in place.")

st.markdown("---")

# Suspended users - cross-category finding
st.markdown("### Suspended Users With Active Access (Cross-Category)")
st.markdown(
    "Suspended accounts that still hold group memberships or Drive edit access pose "
    "a data integrity and compliance risk."
)

group_members = [u for u in suspended_users if u["group_memberships"] > 0]
drive_access = [u for u in suspended_users if u["drive_edit_access"] > 0]

col1, col2 = st.columns(2)
col1.metric("Suspended - Active Group Memberships", len(group_members))
col2.metric("Suspended - Drive Edit Access", len(drive_access))

if suspended_users:
    sus_df = pd.DataFrame(suspended_users)
    sus_df = sus_df.rename(columns={
        "email": "Email",
        "group_memberships": "Active Group Memberships",
        "drive_edit_access": "Shared Drive Edit Access",
    })

    def highlight_nonzero(val):
        if isinstance(val, int) and val > 0:
            return "color: #f97316; font-weight: 600"
        return ""

    styled_sus = sus_df.style.applymap(highlight_nonzero, subset=["Active Group Memberships", "Shared Drive Edit Access"])
    st.dataframe(styled_sus, use_container_width=True, hide_index=True)
else:
    st.success("No suspended users found with active access.")

st.markdown("---")
st.markdown(
    '<span style="color:#64748b;font-size:0.82em;">'
    "Best Practice: Define explicit Vault retention rules for every OU handling regulated data. "
    "Run a suspended user cleanup quarterly to remove stale group memberships and Drive permissions."
    "</span>",
    unsafe_allow_html=True,
)
