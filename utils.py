"""Shared helpers for all pages."""

import streamlit as st


CATEGORY_ICONS = {
    "External Sharing": "🔗",
    "Admin Roles": "👤",
    "MFA Enforcement": "🔐",
    "DLP Coverage": "🛡",
    "Vault Retention": "📦",
}

SEVERITY_COLOR_CSS = {
    "Critical": "#ef4444",
    "High": "#f97316",
    "Medium": "#eab308",
    "Low": "#22c55e",
    "Pass": "#64748b",
}

PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'IBM Plex Mono', monospace !important;
    background-color: #050508 !important;
    color: #e2e8f0 !important;
}

section[data-testid="stSidebar"] {
    background-color: #0d0d12 !important;
}

.stButton > button {
    background-color: #0d0d12;
    border: 1px solid #22c55e;
    color: #22c55e;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    border-radius: 4px;
    padding: 6px 14px;
}
.stButton > button:hover {
    background-color: #22c55e;
    color: #050508;
}

div[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2rem !important;
}

.badge-critical { color: #ef4444; font-weight: 600; }
.badge-high     { color: #f97316; font-weight: 600; }
.badge-medium   { color: #eab308; font-weight: 600; }
.badge-low      { color: #22c55e; font-weight: 600; }
.badge-pass     { color: #64748b; }

.finding-row {
    background: #0d0d12;
    border-left: 3px solid #22c55e;
    padding: 8px 12px;
    margin-bottom: 6px;
    border-radius: 0 4px 4px 0;
}
</style>
"""


def apply_styles():
    st.markdown(PAGE_CSS, unsafe_allow_html=True)


def get_data() -> dict:
    """Load audit data into session state if not already present."""
    if "data" not in st.session_state or st.session_state.data is None:
        _load_data()
    return st.session_state.data


def _load_data():
    demo_mode = st.session_state.get("demo_mode", True)
    if demo_mode:
        from connectors.demo_data import load_all
    else:
        from connectors.gws_connector import load_all

    with st.spinner("Loading audit data..."):
        try:
            st.session_state.data = load_all()
        except Exception as exc:
            st.error(f"Failed to load data: {exc}")
            st.session_state.data = None
            st.stop()


def get_findings() -> list:
    from engine.scorer import score_all
    data = get_data()
    if "findings" not in st.session_state or st.session_state.findings is None:
        st.session_state.findings = score_all(data)
    return st.session_state.findings


def get_scores() -> dict:
    from engine.scorer import compute_scores
    findings = get_findings()
    if "scores" not in st.session_state or st.session_state.scores is None:
        st.session_state.scores = compute_scores(findings)
    return st.session_state.scores


def severity_badge(severity: str) -> str:
    css = f"badge-{severity.lower()}"
    return f'<span class="{css}">{severity}</span>'


def reset_cache():
    for key in ("data", "findings", "scores"):
        st.session_state.pop(key, None)


def sidebar_demo_toggle():
    if "demo_mode" not in st.session_state:
        st.session_state.demo_mode = True

    with st.sidebar:
        st.markdown("### GWS Security Auditor")
        st.markdown("---")
        current = st.session_state.demo_mode
        toggled = st.toggle("Demo Mode (Apex Labs)", value=current)
        if toggled != current:
            st.session_state.demo_mode = toggled
            reset_cache()
            st.rerun()
        if st.session_state.demo_mode:
            st.info("Synthetic data - no credentials required")
        else:
            st.warning("Live mode: configure secrets.toml")
        st.markdown("---")
