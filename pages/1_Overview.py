import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Overview - GWS Auditor", page_icon="📊", layout="wide")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import apply_styles, sidebar_demo_toggle, get_data, get_findings, get_scores
from engine.scorer import top_critical_findings

apply_styles()
sidebar_demo_toggle()

data = get_data()
findings = get_findings()
scores = get_scores()

st.markdown("## Overview")
st.markdown(
    f"**{data.get('org_name')}** &nbsp;|&nbsp; "
    f"{data.get('total_users')} users &nbsp;|&nbsp; "
    f"Audited {data.get('audit_timestamp', '')[:10]}",
    unsafe_allow_html=True,
)
st.markdown("---")

failing = [f for f in findings if not f["compliant"]]
critical_count = sum(1 for f in failing if f["severity"] == "Critical")
high_count = sum(1 for f in failing if f["severity"] == "High")
medium_count = sum(1 for f in failing if f["severity"] == "Medium")
low_count = sum(1 for f in failing if f["severity"] == "Low")
overall = scores.get("overall", 0)

# Metric row
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Overall Score", f"{overall}%")
c2.metric("Total Findings", len(failing))
c3.metric("Critical", critical_count)
c4.metric("High", high_count)
c5.metric("Medium / Low", f"{medium_count} / {low_count}")

st.markdown("---")

# Category readiness bar chart
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
    title="Readiness Score by Category",
    plot_bgcolor="#050508",
    paper_bgcolor="#050508",
    font=dict(color="#e2e8f0", family="IBM Plex Mono"),
    yaxis=dict(range=[0, 115], gridcolor="#1e1e2e", zeroline=False),
    xaxis=dict(gridcolor="#1e1e2e"),
    margin=dict(t=50, b=40, l=10, r=10),
    height=370,
)
fig.add_hline(y=90, line_dash="dot", line_color="#22c55e", annotation_text="90% target")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Severity breakdown donut
sev_labels = ["Critical", "High", "Medium", "Low"]
sev_values = [critical_count, high_count, medium_count, low_count]
sev_colors = ["#ef4444", "#f97316", "#eab308", "#22c55e"]

fig2 = go.Figure(
    go.Pie(
        labels=sev_labels,
        values=sev_values,
        hole=0.5,
        marker_colors=sev_colors,
        textfont=dict(family="IBM Plex Mono", color="#e2e8f0"),
        hovertemplate="%{label}: %{value} findings<extra></extra>",
    )
)
fig2.update_layout(
    title="Findings by Severity",
    plot_bgcolor="#050508",
    paper_bgcolor="#050508",
    font=dict(color="#e2e8f0", family="IBM Plex Mono"),
    margin=dict(t=50, b=10, l=10, r=10),
    height=320,
    legend=dict(font=dict(color="#e2e8f0")),
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Top 5 findings
st.markdown("### Top Priority Findings")
top = top_critical_findings(findings, n=5)
if not top:
    st.success("No critical or high findings.")
else:
    color_map = {
        "Critical": "#ef4444",
        "High": "#f97316",
        "Medium": "#eab308",
        "Low": "#22c55e",
    }
    for f in top:
        color = color_map.get(f["severity"], "#64748b")
        st.markdown(
            f'<div style="background:#0d0d12;border-left:3px solid {color};'
            f'padding:10px 14px;margin-bottom:8px;border-radius:0 4px 4px 0;">'
            f'<span style="color:{color};font-weight:600;">[{f["severity"]}]</span> '
            f'<span style="color:#94a3b8;font-size:0.85em;">{f["category"]}</span><br>'
            f'<span style="color:#e2e8f0;">{f["description"]}</span><br>'
            f'<span style="color:#64748b;font-size:0.82em;">Action: {f["recommended_action"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
