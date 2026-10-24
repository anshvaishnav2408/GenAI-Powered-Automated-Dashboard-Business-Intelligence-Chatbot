"""
Data Explorer Tab Component
Inspect raw and cleaned data, column types, missing values,
statistical distributions, outlier records, and compliance audit trail.
"""

from typing import Dict, List, Any
import streamlit as st
import pandas as pd
import plotly.express as px
from components.ui_helpers import render_metric_card


def render_explorer_tab(
    clean_df: pd.DataFrame,
    raw_df: pd.DataFrame,
    cleaning_metadata: Dict[str, Any]
):
    st.markdown("### Data Health & Technical Profiling")
    st.caption("Comprehensive data health audit, schema inference diagnostics, and statistical profiling.")

    quality_rep = cleaning_metadata.get("quality_report", {})
    audit_log = cleaning_metadata.get("audit_log", [])
    outlier_info = cleaning_metadata.get("outlier_info", {})
    col_types = cleaning_metadata.get("column_types", {})

    # --- Quality Score Cards ---
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        score = quality_rep.get("overall_score", 100.0)
        render_metric_card("Data Health Score", f"{score}%", help_text="Composite score of completeness, uniqueness, and consistency")
    with q2:
        comp = quality_rep.get("completeness_pct", 100.0)
        render_metric_card("Completeness", f"{comp}%", help_text="Percentage of non-missing values across all cells")
    with q3:
        uniq = quality_rep.get("Uniqueness", f"{quality_rep.get('uniqueness_pct', 100.0)}%")
        render_metric_card("Uniqueness", f"{quality_rep.get('uniqueness_pct', 100.0)}%", help_text="Percentage of non-duplicate records")
    with q4:
        tot_outliers = quality_rep.get("total_outliers", 0)
        render_metric_card("Outliers Flagged", f"{tot_outliers:,}", help_text="Total data points exceeding 1.5 * IQR bounds")

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    # --- Sub-navigation Tabs ---
    exp_tabs = st.tabs([
        "Data Preview",
        "Column Health & Types",
        "Statistical Profiling",
        "Outlier Inspector",
        "Sanitization Audit Trail"
    ])

    # 1. Data Preview
    with exp_tabs[0]:
        st.markdown(f"**Dimensions:** `{clean_df.shape[0]:,}` rows × `{clean_df.shape[1]}` columns | **Memory Footprint:** `{clean_df.memory_usage(deep=True).sum() / 1024:.1f} KB`")
        
        # Search & Column Filter
        p_c1, p_c2 = st.columns([1.5, 2.5])
        with p_c1:
            search_query = st.text_input("Filter preview (search any text):", "", placeholder="Type keywords...")
        with p_c2:
            visible_cols = st.multiselect("Visible Columns:", list(clean_df.columns), default=list(clean_df.columns)[:8])

        preview_data = clean_df[visible_cols] if visible_cols else clean_df
        if search_query:
            mask = clean_df.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False).any(), axis=1)
            preview_data = preview_data[mask]
            st.caption(f"Showing {len(preview_data)} matching records.")

        st.dataframe(preview_data.head(100), use_container_width=True, height=400)
        st.caption("Displaying first 100 rows. Use the Presentation & Reports tab to download the entire cleaned dataset.")

    # 2. Column Health & Types
    with exp_tabs[1]:
        st.markdown("#### Schema & Data Integrity Profile")
        col_health = quality_rep.get("column_health", [])
        if col_health:
            health_df = pd.DataFrame(col_health)
            st.dataframe(health_df, use_container_width=True, height=350)
        else:
            st.info("No column health data generated.")

    # 3. Statistical Profiling
    with exp_tabs[2]:
        st.markdown("#### Numerical Summary Statistics")
        num_cols = [c for c, t in col_types.items() if t == "numeric"]
        if num_cols:
            stats_df = clean_df[num_cols].describe().T
            stats_df["skewness"] = clean_df[num_cols].skew()
            stats_df = stats_df.round(2)
            st.dataframe(stats_df, use_container_width=True, height=350)
        else:
            st.info("No numerical columns found to compute statistics.")

    # 4. Outlier Inspector
    with exp_tabs[3]:
        st.markdown("#### Outlier Inspector & Boundary Analysis")
        numeric_cols = [c for c, t in col_types.items() if t == "numeric"]

        if not numeric_cols:
            st.info("No numerical columns available for outlier detection.")
        else:
            selected_num = st.selectbox("Select Numerical Feature:", numeric_cols, index=0)
            if selected_num and selected_num in outlier_info:
                info = outlier_info[selected_num]
                
                o_c1, o_c2, o_c3, o_c4 = st.columns(4)
                with o_c1:
                    st.metric("Outlier Points (IQR)", f"{info['outlier_count_iqr']} ({info['outlier_pct_iqr']}%)")
                with o_c2:
                    st.metric("Acceptable IQR Span", f"[{info['lower_bound']:.2f}, {info['upper_bound']:.2f}]")
                with o_c3:
                    st.metric("Median (Q2)", f"{clean_df[selected_num].median():.2f}")
                with o_c4:
                    st.metric("Severe Outliers (|z| > 3)", f"{info['outlier_count_zscore']}")

                # Plot Box Plot
                fig = px.box(
                    clean_df,
                    y=selected_num,
                    points="outliers",
                    title=f"Box Plot & Outlier Spread: {selected_num.replace('_', ' ').title()}",
                    color_discrete_sequence=["#2563EB"]
                )
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

                # Show outlier records
                outlier_rows = clean_df[(clean_df[selected_num] < info['lower_bound']) | (clean_df[selected_num] > info['upper_bound'])]
                if not outlier_rows.empty:
                    st.markdown(f"##### Outlier Transactions ({len(outlier_rows):,} records)")
                    outlier_csv = outlier_rows.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label=f"💾 Download Outliers for {selected_num} (CSV)",
                        data=outlier_csv,
                        file_name=f"outliers_{selected_num}.csv",
                        mime="text/csv"
                    )
                    st.dataframe(outlier_rows.head(50), use_container_width=True, height=250)

    # 5. Transparent Audit Log
    with exp_tabs[4]:
        st.markdown("#### Automated Sanitization & Preprocessing Audit Log")
        st.caption("Detailed log of every data cleaning, type inference, null imputation, and deduplication action.")
        
        if audit_log:
            audit_df = pd.DataFrame(audit_log)
            st.dataframe(audit_df, use_container_width=True, height=350)
        else:
            st.success("No automated corrections were needed. The dataset met all health thresholds.")
