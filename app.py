import streamlit as st

st.set_page_config(
    page_title="GWS Security Auditor",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils import apply_styles, sidebar_demo_toggle, get_data, get_findings, get_scores
from engine.scorer import top_critical_findings

apply_styles()
sidebar_demo_toggle()

data = get_data()
findings = get_findings()
scores = get_scores()

st.markdown("# GWS Security Auditor")

mode_label = "Demo (Apex Labs)" if st.session_state.get("demo_mode", True) else data.get("org_name", "Live")
st.markdown(
    f"**Org:** {data.get('org_name', 'N/A')} &nbsp;|&nbsp; "
    f"**Users:** {data.get('total_users', 'N/A')} &nbsp;|&nbsp; "
    f"**Audited:** {data.get('audit_timestamp', '')[:10]}",
    unsafe_allow_html=True,
)

st.markdown("---")

# Metrics row
failing = [f for f in findings if not f["compliant"]]
critical_count = sum(1 for f in failing if f["severity"] == "Critical")
high_count = sum(1 for f in failing if f["severity"] == "High")
overall = scores.get("overall", 0)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Overall Score", f"{overall}%")
col2.metric("Total Findings", len(failing))
col3.metric("Critical", critical_count)
col4.metric("High", high_count)

st.markdown("---")

# Category scores bar chart
import plotly.graph_objects as go

by_cat = scores.get("by_category", {})
categories = list(by_cat.keys())
cat_scores = list(by_cat.values())
bar_colors = [
    "#22c55e" if s >= 90 else "#eab308" if s >= 70 else "#ef4444"
    for s in cat_scores
]

fig = go.Figure(
    go.Bar(
        x=categories,
        y=cat_scores,
        marker_color=bar_colors,
        text=[f"{s}%" for s in cat_scores],
        textposition="outside",
        textfont=dict(color="#e2e8f0", family="IBM Plex Mono"),
    )
)
fig.update_layout(
    title="Readiness by Category",
    plot_bgcolor="#050508",
    paper_bgcolor="#050508",
    font=dict(color="#e2e8f0", family="IBM Plex Mono"),
    yaxis=dict(range=[0, 110], gridcolor="#1e1e2e", zeroline=False),
    xaxis=dict(gridcolor="#1e1e2e"),
    margin=dict(t=50, b=40, l=10, r=10),
    height=350,
)
fig.add_hline(y=90, line_dash="dot", line_color="#22c55e", annotation_text="90% target")

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Top critical findings
st.markdown("### Top Priority Findings")
top = top_critical_findings(findings, n=5)
if not top:
    st.success("No critical or high findings. Well done.")
else:
    for f in top:
        sev = f["severity"]
        color_map = {
            "Critical": "#ef4444",
            "High": "#f97316",
            "Medium": "#eab308",
            "Low": "#22c55e",
        }
        color = color_map.get(sev, "#64748b")
        st.markdown(
            f'<div style="background:#0d0d12;border-left:3px solid {color};'
            f'padding:10px 14px;margin-bottom:8px;border-radius:0 4px 4px 0;">'
            f'<span style="color:{color};font-weight:600;">[{sev}]</span> '
            f'<span style="color:#94a3b8;font-size:0.85em;">{f["category"]}</span><br>'
            f'<span style="color:#e2e8f0;">{f["description"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown(
    '<span style="color:#64748b;font-size:0.8em;">Navigate pages via the sidebar to drill into each audit dimension.</span>',
    unsafe_allow_html=True,
)
