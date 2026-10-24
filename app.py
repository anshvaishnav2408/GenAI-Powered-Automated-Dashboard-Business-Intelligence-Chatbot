"""
Enterprise Business Intelligence & Decision Studio
Multi-table ingestion, messy data auto-cleaning, and conversational analytics.
"""

import os
import re
import streamlit as st
import pandas as pd

from core.data_loader import load_dataset, DataLoaderError
from core.data_cleaner import DataCleaner
from core.domain_classifier import classify_domain
from core.kpi_engine import KPIEngine
from core.sql_engine import SafeSQLEngine
from core.llm_interface import LLMClient
from core.insights_generator import InsightsGenerator

from components.ui_helpers import apply_custom_styles
from components.overview_tab import render_overview_tab
from components.explorer_tab import render_explorer_tab
from components.insights_tab import render_insights_tab
from components.chatbot_tab import render_chatbot_tab
from components.export_tab import render_export_tab


# Page Configuration
st.set_page_config(
    page_title="Executive Analytics Studio | Multi-Table Automated BI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply bespoke enterprise styling
apply_custom_styles()


def reset_app_state():
    """Clear cached computations when dataset changes."""
    for key in ["all_datasets", "active_dataset_key", "cached_insights", "chat_messages", "active_session_signature"]:
        if key in st.session_state:
            del st.session_state[key]


# --- Sidebar: Configuration & Data Ingestion ---
with st.sidebar:
    st.markdown("### Data Studio Control")
    st.caption("Enterprise Analytics & Multi-Table Intelligence")
    st.markdown("---")

    st.markdown("##### 1. Data Ingestion")
    data_source_mode = st.radio(
        "Ingestion Source:",
        ["Sample Business Datasets", "Upload Files (CSV / Excel)"],
        index=0,
        key="data_source_mode"
    )

    uploaded_files = []
    sample_file_paths = []

    if data_source_mode == "Upload Files (CSV / Excel)":
        uploaded_files = st.file_uploader(
            "Upload one or more CSV / Excel datasets",
            type=["csv", "xlsx", "xls", "tsv"],
            accept_multiple_files=True,
            help="Upload multiple files (up to 100MB each). All tables will be available for cross-table SQL joins and individual dashboards."
        )
    else:
        sample_choice = st.selectbox(
            "Select Industry Dataset:",
            [
                "Retail Sales & Profitability (Single Table)",
                "SaaS Subscriptions & Churn (Single Table)",
                "HR Workforce & Retention (Single Table)",
                "Multi-Table Enterprise Suite (Retail + SaaS + HR)"
            ]
        )
        sample_map = {
            "Retail Sales & Profitability (Single Table)": ["sample_data/retail_sales_bi.csv"],
            "SaaS Subscriptions & Churn (Single Table)": ["sample_data/saas_churn_bi.csv"],
            "HR Workforce & Retention (Single Table)": ["sample_data/hr_analytics_bi.csv"],
            "Multi-Table Enterprise Suite (Retail + SaaS + HR)": [
                "sample_data/retail_sales_bi.csv",
                "sample_data/saas_churn_bi.csv",
                "sample_data/hr_analytics_bi.csv"
            ]
        }
        sample_file_paths = sample_map[sample_choice]

    st.markdown("---")

    # --- Intelligence Engine Selection ---
    st.markdown("##### 2. Analytics Engine")
    ai_provider = st.selectbox(
        "Intelligence Provider:",
        [
            "Deterministic BI Analyst (Offline / Fast)",
            "Local Ollama (Private On-Premises)",
            "Google Gemini API",
            "OpenAI / Compatible API"
        ],
        index=0
    )

    llm_config = {}
    provider_key = "heuristic"

    if "Deterministic" in ai_provider:
        provider_key = "heuristic"
        st.info("Verified In-Memory Execution: Powered by DuckDB analytical engine with deterministic KPI formulation and zero network latency.")
    elif "Ollama" in ai_provider:
        provider_key = "ollama"
        ollama_host = st.text_input("Ollama Host URL:", value="http://localhost:11434")
        ollama_model = st.text_input("Ollama Model:", value="llama3:latest")
        llm_config = {"ollama_host": ollama_host, "ollama_model": ollama_model}
    elif "Gemini" in ai_provider:
        provider_key = "gemini"
        gemini_api_key = st.text_input("Gemini API Key:", type="password")
        gemini_model = st.selectbox("Gemini Model:", ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"])
        llm_config = {"gemini_api_key": gemini_api_key, "gemini_model": gemini_model}
    elif "OpenAI" in ai_provider:
        provider_key = "openai"
        openai_key = st.text_input("API Key:", type="password")
        openai_base = st.text_input("Base URL:", value="https://api.openai.com/v1")
        openai_model = st.text_input("Model Name:", value="gpt-4o-mini")
        llm_config = {"openai_api_key": openai_key, "openai_base_url": openai_base, "openai_model": openai_model}

    st.markdown("---")

    # --- Cleaning & Preprocessing Settings ---
    st.markdown("##### 3. Preprocessing Controls")
    auto_impute = st.checkbox("Automated Missing Value Imputation", value=True, help="Fills missing numeric values with median/mean and categorical with mode.")
    auto_dedup = st.checkbox("Exact Deduplication", value=True, help="Removes duplicate rows while recording counts in the audit trail.")

    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.72rem; color: #64748B; line-height: 1.4;">
            <strong>Data Security & Privacy</strong>: In-memory execution via DuckDB. Zero row data is persisted or transferred externally without user configuration.
        </div>
        """,
        unsafe_allow_html=True
    )


# --- Determine Active Input Sources ---
active_sources = uploaded_files if uploaded_files else sample_file_paths

if not active_sources:
    st.markdown(
        """
        <div style="text-align: center; padding: 50px 20px;">
            <h1 style="font-size: 2.6rem; font-weight: 800; color: #F8FAFC; margin-bottom: 10px;">
                Enterprise Business Intelligence Studio
            </h1>
            <p style="font-size: 1.15rem; color: #94A3B8; max-width: 700px; margin: 0 auto 30px auto;">
                Transform single or multi-table tabular datasets into interactive executive dashboards, anomaly reports, and conversational decision intelligence.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.info("Select a sample dataset or upload your own CSV/Excel files in the sidebar to begin analysis.")
    st.stop()


# Generate a unique signature for the active upload batch
current_signature = "_".join([getattr(f, "name", str(f)) for f in active_sources])

if st.session_state.get("active_session_signature") != current_signature:
    reset_app_state()
    st.session_state.active_session_signature = current_signature

# --- Ingestion & Processing Pipeline ---
if "all_datasets" not in st.session_state:
    all_datasets = {}
    try:
        with st.spinner("Ingesting, cleaning, and profiling uploaded datasets..."):
            for item in active_sources:
                fname = getattr(item, "name", os.path.basename(str(item)))
                clean_key = re.sub(r"[^a-zA-Z0-9_]", "_", os.path.splitext(fname)[0]).lower()
                if not clean_key or clean_key[0].isdigit():
                    clean_key = f"tbl_{clean_key}"

                raw_df, load_meta = load_dataset(item, fname)
                cleaner = DataCleaner(raw_df)
                clean_df, cleaning_meta = cleaner.clean_pipeline(impute=auto_impute, deduplicate=auto_dedup)
                domain_info = classify_domain(clean_df)
                kpi_engine = KPIEngine(clean_df, domain_info["domain_key"], cleaning_meta["column_types"])
                kpis = kpi_engine.calculate_kpis()

                all_datasets[clean_key] = {
                    "raw_df": raw_df,
                    "clean_df": clean_df,
                    "meta": load_meta,
                    "cleaning_meta": cleaning_meta,
                    "domain_info": domain_info,
                    "kpis": kpis
                }

        st.session_state.all_datasets = all_datasets
        st.session_state.active_dataset_key = list(all_datasets.keys())[0]

    except DataLoaderError as de:
        st.error(f"Data Ingestion Error: {str(de)}")
        st.stop()
    except Exception as e:
        st.error(f"Pipeline Execution Error: {str(e)}")
        st.stop()


all_datasets = st.session_state.all_datasets
if not all_datasets:
    st.stop()

# --- Active Dataset Selector (for Multi-Table Ingestion) ---
active_key = st.session_state.get("active_dataset_key", list(all_datasets.keys())[0])

if len(all_datasets) > 1:
    col_sel, col_stat = st.columns([1.8, 2.2])
    with col_sel:
        selected_key = st.selectbox(
            "Active Dataset Focus:",
            options=list(all_datasets.keys()),
            index=list(all_datasets.keys()).index(active_key) if active_key in all_datasets else 0,
            format_func=lambda k: f"📄 {all_datasets[k]['meta']['filename']} ({len(all_datasets[k]['clean_df']):,} rows)"
        )
        if selected_key != active_key:
            st.session_state.active_dataset_key = selected_key
            st.session_state.cached_insights = None
            st.rerun()
    with col_stat:
        st.write("")
        st.caption(f"Multi-Table Mode: **{len(all_datasets)} tables registered in DuckDB**. All tables available for cross-table SQL joins in Decision Assistant.")

current_data = all_datasets[st.session_state.active_dataset_key]
clean_df = current_data["clean_df"]
raw_df = current_data["raw_df"]
cleaning_meta = current_data["cleaning_meta"]
domain_info = current_data["domain_info"]
kpis = current_data["kpis"]

# --- Initialize SQL Engine with ALL Tables ---
all_clean_tables = {k: d["clean_df"] for k, d in all_datasets.items()}
sql_engine = SafeSQLEngine(all_clean_tables, active_key=st.session_state.active_dataset_key)
llm_client = LLMClient(provider_key, llm_config, clean_df, domain_info["domain_key"])
insights_gen = InsightsGenerator(clean_df, domain_info, cleaning_meta["column_types"], kpis, llm_client)


# --- Platform Header ---
head_col1, head_col2 = st.columns([3, 1])
with head_col1:
    st.markdown(f"## {domain_info['domain_title']}")
    score = cleaning_meta["quality_report"]["overall_score"]
    st.markdown(
        f"""
        <span class="status-pill pill-primary">Domain: {domain_info['domain_title']}</span>
        <span class="status-pill pill-success">Data Quality: {score}%</span>
        <span class="status-pill pill-warning">{len(clean_df):,} Rows &middot; {len(clean_df.columns)} Columns</span>
        <span style="font-size: 0.8rem; color: #64748B; margin-left: 6px;">Active File: <code>{current_data['meta']['filename']}</code></span>
        """,
        unsafe_allow_html=True
    )

with head_col2:
    st.write("")
    if st.button("Re-run Pipeline", use_container_width=True):
        reset_app_state()
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


# --- Navigation Tabs ---
tab_overview, tab_explorer, tab_insights, tab_chatbot, tab_export = st.tabs([
    "Executive Dashboard",
    "Data Health & Audit",
    "Strategic Intelligence",
    "Decision Assistant",
    "Executive Report & Exports"
])

with tab_overview:
    render_overview_tab(clean_df, cleaning_meta["column_types"], domain_info)

with tab_explorer:
    render_explorer_tab(clean_df, raw_df, cleaning_meta)

with tab_insights:
    render_insights_tab(insights_gen, llm_client)

with tab_chatbot:
    render_chatbot_tab(clean_df, cleaning_meta["column_types"], domain_info, sql_engine, llm_client)

with tab_export:
    domain_info["active_filename"] = current_data["meta"]["filename"]
    cached_ins = st.session_state.get("cached_insights")
    if not cached_ins:
        cached_ins = insights_gen.generate_full_insights()
        st.session_state.cached_insights = cached_ins
    render_export_tab(clean_df, domain_info, kpis, cached_ins, cleaning_meta)
