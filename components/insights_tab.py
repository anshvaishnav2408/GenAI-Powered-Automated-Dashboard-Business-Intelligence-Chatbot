"""
Strategic Insights Tab Component
Presents executive briefings, key business observations, risk diagnostics,
and strategic recommendations formatted as an executive management memo.
"""

from typing import Dict, Any
import streamlit as st
from core.insights_generator import InsightsGenerator
from core.llm_interface import LLMClient


def render_insights_tab(
    insights_generator: InsightsGenerator,
    llm_client: LLMClient
):
    st.markdown("### Strategic Intelligence Briefing")
    st.caption("C-suite executive summary and risk diagnostics grounded strictly in verified dataset calculations.")

    # Check if insights are cached in session_state
    if "cached_insights" not in st.session_state or st.session_state.get("insights_need_refresh", False):
        with st.spinner("Synthesizing strategic performance metrics..."):
            st.session_state.cached_insights = insights_generator.generate_full_insights()
            st.session_state.insights_need_refresh = False

    insights = st.session_state.cached_insights

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        if st.button("Refresh Analysis", use_container_width=True):
            st.session_state.insights_need_refresh = True
            st.rerun()
    with col_info:
        provider_name = llm_client.provider_type.title()
        st.caption(f"Verification Mode: **{provider_name} Engine** | Mathematical Grounding: **100% Deterministic**")

    st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)

    # Layout sections in two clean executive columns without harsh border lines
    s1, s2 = st.columns([1.1, 1])

    with s1:
        st.markdown(
            f"""
            <div class="metric-container" style="padding: 24px;">
                <div class="metric-title" style="color: #60A5FA; margin-bottom: 12px;">Executive Performance Synthesis</div>
                <div style="color: #E2E8F0; line-height: 1.6; font-size: 0.95rem;">
                    {insights.get('executive_summary', 'Executive summary unavailable.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="metric-container" style="padding: 24px; margin-top: 16px;">
                <div class="metric-title" style="color: #34D399; margin-bottom: 12px;">Growth Drivers & Observations</div>
                <div style="color: #E2E8F0; line-height: 1.6; font-size: 0.95rem;">
                    {insights.get('key_insights', 'Key insights unavailable.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with s2:
        st.markdown(
            f"""
            <div class="metric-container" style="padding: 24px;">
                <div class="metric-title" style="color: #F87171; margin-bottom: 12px;">Risk Diagnostics & Anomalies</div>
                <div style="color: #E2E8F0; line-height: 1.6; font-size: 0.95rem;">
                    {insights.get('risks_and_anomalies', 'Risk analysis unavailable.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="metric-container" style="padding: 24px; margin-top: 16px;">
                <div class="metric-title" style="color: #34D399; margin-bottom: 12px;">Strategic Roadmap & Actions</div>
                <div style="color: #E2E8F0; line-height: 1.6; font-size: 0.95rem;">
                    {insights.get('recommendations', 'Recommendations unavailable.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
