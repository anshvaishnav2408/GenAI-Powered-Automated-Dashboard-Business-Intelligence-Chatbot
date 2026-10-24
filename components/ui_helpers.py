"""
UI Helpers Module
Enterprise-grade Design System: Clean Slate Typography, Seamless Modern Cards (Zero Harsh/White Lines),
and Strategic Callout Banners designed to look like a bespoke commercial SaaS product.
"""

import streamlit as st


ENTERPRISE_CSS = """
<style>
/* 1. Global Typography & Clean Base Styling */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    letter-spacing: -0.01em;
}

code, kbd, samp, pre {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.84rem;
}

/* Remove default Streamlit top padding to look like a full-screen SaaS platform */
.block-container {
    padding-top: 1.8rem;
    padding-bottom: 3.5rem;
    max-width: 95% !important;
}

/* Header bar styling */
header[data-testid="stHeader"] {
    background: transparent;
}

/* 2. Professional Enterprise Metric Cards - NO WHITE LINES */
.metric-container {
    background: #111827;
    border: none !important;
    outline: none !important;
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 14px;
    position: relative;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.metric-container:hover {
    background: #162033;
    border: none !important;
    outline: none !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
    transform: translateY(-2px);
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    border: none !important;
}

.metric-title {
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94A3B8;
    border: none !important;
}

.metric-val {
    font-size: 1.95rem;
    font-weight: 800;
    color: #F8FAFC;
    line-height: 1.15;
    letter-spacing: -0.02em;
    border: none !important;
}

.metric-footer {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    font-size: 0.8rem;
    border: none !important;
}

.delta-badge-pos {
    background: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: none !important;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.75rem;
}

.delta-badge-neg {
    background: rgba(239, 68, 68, 0.15);
    color: #F87171;
    border: none !important;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.75rem;
}

.metric-subtext {
    color: #64748B;
    font-size: 0.76rem;
    border: none !important;
}

/* 3. Executive Strategic Banners - Modern seamless gradient cards with no harsh borders */
.exec-banner {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.16) 0%, #111827 100%);
    border: none !important;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 22px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
}

.exec-banner-warning {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.16) 0%, #171114 100%);
    border: none !important;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 22px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
}

.exec-banner-success {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.16) 0%, #0E1815 100%);
    border: none !important;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 22px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
}

.banner-title {
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
    border: none !important;
}

.banner-text {
    font-size: 0.92rem;
    color: #CBD5E1;
    line-height: 1.5;
    margin: 0;
    border: none !important;
}

/* 4. Domain & Health Badges - Seamless */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 8px;
    border: none !important;
}

.pill-primary {
    background: #1E293B;
    color: #93C5FD;
    border: none !important;
}

.pill-success {
    background: rgba(16, 185, 129, 0.15);
    color: #6EE7B7;
    border: none !important;
}

.pill-warning {
    background: rgba(245, 158, 11, 0.15);
    color: #FCD34D;
    border: none !important;
}

/* 5. Clean Custom Navigation Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding-bottom: 4px;
    margin-bottom: 24px;
}

.stTabs [data-baseweb="tab"] {
    height: 40px;
    white-space: pre;
    font-size: 0.88rem;
    font-weight: 600;
    color: #94A3B8;
    background-color: transparent;
    border-radius: 6px;
    padding: 8px 16px;
    border: none !important;
    transition: all 0.15s ease;
}

.stTabs [aria-selected="true"] {
    color: #FFFFFF !important;
    background-color: #1E293B !important;
    border: none !important;
}

/* 6. Professional Chatbox message bubbles */
.chat-response-card {
    background: #111827;
    border: none !important;
    border-radius: 12px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    padding: 20px;
    margin-top: 10px;
    margin-bottom: 18px;
}

/* 7. Streamlit Card & Expander Overrides - Completely removes white lines and harsh borders */
details[data-testid="stExpander"],
div[data-testid="stExpander"] {
    border: none !important;
    background: #111827 !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2) !important;
    overflow: hidden !important;
}

details[data-testid="stExpander"] summary {
    border: none !important;
    border-bottom: none !important;
    background: transparent !important;
    font-weight: 600;
    color: #E2E8F0 !important;
}

details[data-testid="stExpander"][open] summary {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}

details[data-testid="stExpander"] > div {
    border: none !important;
    border-top: none !important;
}

/* Remove white lines on Streamlit native metrics or containers */
[data-testid="stMetric"],
div[data-testid="metric-container"],
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stVerticalBlock"] > div[style*="border"] {
    border: none !important;
    outline: none !important;
}

/* Clean, subtle horizontal divider - no harsh white lines */
hr {
    border: none !important;
    height: 1px !important;
    background: rgba(255, 255, 255, 0.08) !important;
    margin: 22px 0 !important;
}

.metric-container hr,
details[data-testid="stExpander"] hr {
    display: none !important;
}

/* Buttons */
.stButton > button {
    font-weight: 600;
    border-radius: 8px;
    font-size: 0.85rem;
    padding: 6px 16px;
    border: none !important;
    background: #1E293B;
    color: #F8FAFC;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    background: #2563EB;
    color: #FFFFFF;
    border: none !important;
}

/* Dataframe clean styling without harsh border lines */
[data-testid="stDataFrame"] {
    border: none !important;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
}

[data-testid="stPlotlyChart"] {
    border: none !important;
    outline: none !important;
}
</style>
"""


def apply_custom_styles():
    """Inject enterprise corporate CSS design system."""
    st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)


def render_metric_card(
    label: str,
    value: str,
    delta: str = None,
    help_text: str = None,
    subtext: str = None
):
    """
    Render a clean enterprise KPI card with comparison delta badge and subtext.
    Completely seamless with no white lines or harsh borders.
    """
    delta_html = ""
    if delta:
        is_pos = delta.startswith("+")
        badge_cls = "delta-badge-pos" if is_pos else "delta-badge-neg"
        arrow = "↑" if is_pos else "↓"
        delta_html = f'<span class="{badge_cls}">{arrow} {delta}</span>'

    subtext_html = f'<span class="metric-subtext">{subtext or ""}</span>' if subtext else ""

    html = f"""
    <div class="metric-container" title="{help_text or ''}">
        <div class="metric-header">
            <span class="metric-title">{label}</span>
        </div>
        <div class="metric-val">{value}</div>
        <div class="metric-footer">
            {delta_html}
            {subtext_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_executive_alert(alert_type: str, title: str, message: str):
    """
    Render a clean corporate executive alert banner with smooth background tint.
    alert_type: 'info' | 'warning' | 'success'
    """
    cls_map = {
        "info": ("exec-banner", "#60A5FA"),
        "warning": ("exec-banner-warning", "#F87171"),
        "success": ("exec-banner-success", "#34D399")
    }
    cls, color = cls_map.get(alert_type, ("exec-banner", "#60A5FA"))

    html = f"""
    <div class="{cls}">
        <div class="banner-title" style="color: {color};">{title}</div>
        <p class="banner-text">{message}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
