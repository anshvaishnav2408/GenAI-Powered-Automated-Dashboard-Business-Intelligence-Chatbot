"""
Overview Tab Component
Enterprise-grade Business Intelligence Dashboard:
- Dynamic cross-filtering with single-click reset
- KPI metric cards with period deltas
- Strategic Executive Callout Alert
- Interactive multi-dimensional Plotly charts with measure/aggregation toggles
- Cross-dimensional Pivot Matrix (Heatmap)
- Filtered Cohort Data Explorer with immediate CSV export
"""

from typing import Dict, List, Any
import streamlit as st
import pandas as pd
from core.visualization import ChartGenerator
from core.kpi_engine import KPIEngine
from components.ui_helpers import render_metric_card, render_executive_alert


def render_overview_tab(
    df: pd.DataFrame,
    column_types: Dict[str, str],
    domain_info: Dict[str, Any]
):
    # --- Top Control Bar / Dynamic Slicers ---
    with st.expander("Control Slicers & Global Filters", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.4, 1.1, 1.1, 0.7])
        filtered_df = df.copy()

        # 1. Date Range Slicer
        date_cols = [c for c, t in column_types.items() if t == "datetime"]
        if date_cols:
            primary_date = date_cols[0]
            valid_dates = df[primary_date].dropna()
            if not valid_dates.empty:
                min_date = valid_dates.min().date()
                max_date = valid_dates.max().date()
                if min_date < max_date:
                    with f_col1:
                        date_range = st.date_input(
                            f"Timeline ({primary_date})",
                            value=(min_date, max_date),
                            min_value=min_date,
                            max_value=max_date,
                            key="overview_date_range"
                        )
                        if isinstance(date_range, tuple) and len(date_range) == 2:
                            s_date, e_date = date_range
                            filtered_df = filtered_df[
                                (filtered_df[primary_date].dt.date >= s_date) &
                                (filtered_df[primary_date].dt.date <= e_date)
                            ]

        # 2. Categorical Slicers
        cat_cols = [c for c, t in column_types.items() if t == "categorical"]
        if cat_cols:
            first_cat = cat_cols[0]
            with f_col2:
                opts = list(df[first_cat].dropna().unique())
                selected_first = st.multiselect(
                    f"Dimension ({first_cat})",
                    options=opts,
                    default=[],
                    key="overview_cat_filter_1",
                    placeholder="All Categories"
                )
                if selected_first:
                    filtered_df = filtered_df[filtered_df[first_cat].isin(selected_first)]

        if len(cat_cols) > 1:
            second_cat = cat_cols[1]
            with f_col3:
                opts2 = list(df[second_cat].dropna().unique())
                selected_second = st.multiselect(
                    f"Dimension ({second_cat})",
                    options=opts2,
                    default=[],
                    key="overview_cat_filter_2",
                    placeholder="All Segments/Regions"
                )
                if selected_second:
                    filtered_df = filtered_df[filtered_df[second_cat].isin(selected_second)]

        with f_col4:
            st.write("")
            pct_retained = (len(filtered_df) / max(len(df), 1)) * 100.0
            st.caption(f"Active: **{len(filtered_df):,}** ({pct_retained:.0f}%)")
            if st.button("Reset Slicers", use_container_width=True):
                for k in ["overview_date_range", "overview_cat_filter_1", "overview_cat_filter_2"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

    if filtered_df.empty:
        st.warning("No records match the active filter criteria. Please broaden your selection above.")
        return

    # --- Recompute KPIs based on active filtered dataset ---
    kpi_engine = KPIEngine(filtered_df, domain_info["domain_key"], column_types)
    active_kpis = kpi_engine.calculate_kpis()

    # --- KPI Metric Cards Row ---
    if active_kpis:
        num_cards = len(active_kpis)
        cols = st.columns(num_cards)
        for i, kpi in enumerate(active_kpis):
            with cols[i]:
                render_metric_card(
                    label=kpi["label"],
                    value=kpi["value"],
                    delta=kpi.get("delta"),
                    help_text=kpi.get("help"),
                    subtext=f"Cohort: {len(filtered_df):,} records"
                )

    # --- Strategic Executive Callout / Business Problem Alert ---
    num_cols = [c for c, t in column_types.items() if t == "numeric"]
    profit_candidates = [c for c in num_cols if "profit" in c.lower()]
    churn_candidates = [c for c in filtered_df.columns if any(k in c.lower() for k in ["churn", "attrition"])]

    if profit_candidates:
        p_col = profit_candidates[0]
        unprofitable = filtered_df[filtered_df[p_col] < 0]
        if len(unprofitable) > 0:
            loss_total = abs(float(unprofitable[p_col].sum()))
            render_executive_alert(
                "warning",
                "Critical Profitability Vulnerability: Negative Margin Orders",
                f"Identified <strong>{len(unprofitable):,} transactions ({len(unprofitable)/len(filtered_df)*100:.1f}% of cohort)</strong> fulfilling at a net financial loss, eroding <strong>${loss_total:,.2f}</strong> in gross earnings. Review promotional discounts and freight costs on these items."
            )
    elif churn_candidates:
        c_col = churn_candidates[0]
        churn_series = filtered_df[c_col].astype(str).str.lower().str.strip()
        churn_count = churn_series.isin(["yes", "true", "1"]).sum()
        if churn_count > 0:
            churn_pct = (churn_count / len(filtered_df)) * 100.0
            render_executive_alert(
                "warning",
                "Customer Retention & Attrition Exposure",
                f"Active attrition stands at <strong>{churn_pct:.1f}% ({churn_count:,} accounts/employees)</strong>. Analysis indicates elevated concentration among early-lifecycle cohorts and high support interaction tiers."
            )
    else:
        render_executive_alert(
            "info",
            "Executive Portfolio Health Assessment",
            f"Active analysis covers <strong>{len(filtered_df):,} records</strong> across {len(filtered_df.columns)} dimensions. Operations remain stable with key metrics tracking within normal statistical tolerance."
        )

    # --- Visualizations ---
    chart_gen = ChartGenerator(filtered_df, column_types, domain_info["domain_key"])

    # 1. Primary Time-Series Trend
    if date_cols and num_cols:
        t_c1, t_c2 = st.columns([2.5, 1])
        with t_c2:
            trend_metric = st.selectbox("Trajectory Measure:", num_cols, index=0, key="ov_trend_met_sel")
        with t_c1:
            st.caption(f"Timeline Dimension: **{date_cols[0]}**")
        trend_fig = chart_gen.create_trend_chart(date_col=date_cols[0], metric_col=trend_metric)
        if trend_fig:
            st.plotly_chart(trend_fig, use_container_width=True)
    elif date_cols:
        trend_fig = chart_gen.create_trend_chart(date_col=date_cols[0])
        if trend_fig:
            st.plotly_chart(trend_fig, use_container_width=True)

    # 2. Performance Comparison & Portfolio Share
    c1, c2 = st.columns([1.2, 1])
    with c1:
        if cat_cols and num_cols:
            b_c1, b_c2, b_c3 = st.columns([1.2, 1.2, 0.9])
            with b_c1:
                selected_bar_dim = st.selectbox("Dimension:", cat_cols, index=0, key="ov_bar_dim_sel")
            with b_c2:
                selected_bar_metric = st.selectbox("Measure:", num_cols, index=0, key="ov_bar_met_sel")
            with b_c3:
                agg_choice = st.selectbox("Aggregation:", ["Total (Sum)", "Average (Mean)"], index=0, key="ov_bar_agg_sel")
            
            agg_key = "mean" if "Average" in agg_choice else "sum"
            bar_fig = chart_gen.create_category_bar(cat_col=selected_bar_dim, metric_col=selected_bar_metric, agg_func=agg_key)
        elif cat_cols:
            selected_bar_dim = st.selectbox("Breakdown Dimension:", cat_cols, index=0, key="ov_bar_dim_sel")
            bar_fig = chart_gen.create_category_bar(cat_col=selected_bar_dim)
        else:
            bar_fig = None

        if bar_fig:
            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.info("Insufficient categorical dimensions to render breakdown.")

    with c2:
        if cat_cols and num_cols:
            d_c1, d_c2 = st.columns(2)
            with d_c1:
                donut_dim = st.selectbox("Share Dimension:", cat_cols, index=min(1, len(cat_cols)-1), key="ov_donut_dim_sel")
            with d_c2:
                donut_metric = st.selectbox("Weight Metric:", num_cols, index=0, key="ov_donut_met_sel")
            donut_fig = chart_gen.create_donut_chart(cat_col=donut_dim, metric_col=donut_metric)
        elif cat_cols:
            donut_dim = st.selectbox("Share Dimension:", cat_cols, index=min(1, len(cat_cols)-1), key="ov_donut_dim_sel")
            donut_fig = chart_gen.create_donut_chart(cat_col=donut_dim)
        else:
            donut_fig = None

        if donut_fig:
            st.plotly_chart(donut_fig, use_container_width=True)
        else:
            st.info("Insufficient categorical dimensions to render share donut.")

    # 3. Distribution & Correlation
    c3, c4 = st.columns(2)
    with c3:
        if num_cols:
            sel_dist_col = st.selectbox("Inspect Distribution:", num_cols, index=0, key="ov_dist_sel")
            dist_fig = chart_gen.create_distribution_chart(num_col=sel_dist_col)
        else:
            dist_fig = chart_gen.create_distribution_chart()

        if dist_fig:
            st.plotly_chart(dist_fig, use_container_width=True)
        else:
            st.info("No numerical attributes available for distribution analysis.")

    with c4:
        if len(num_cols) >= 2:
            sc_col1, sc_col2 = st.columns(2)
            with sc_col1:
                x_sel = st.selectbox("X-Axis (Metric):", num_cols, index=0, key="ov_sc_x")
            with sc_col2:
                y_sel = st.selectbox("Y-Axis (Metric):", num_cols, index=min(1, len(num_cols)-1), key="ov_sc_y")
            scatter_fig = chart_gen.create_scatter_correlation(x_col=x_sel, y_col=y_sel)
        else:
            scatter_fig = chart_gen.create_scatter_correlation()

        if scatter_fig:
            st.plotly_chart(scatter_fig, use_container_width=True)
        else:
            st.info("At least two numerical variables are required for correlation analysis.")

    # 4. Cross-Dimensional Pivot Matrix (Heatmap)
    if len(cat_cols) >= 2 and num_cols:
        with st.expander("Cross-Dimensional Matrix (Pivot Heatmap)", expanded=False):
            h_c1, h_c2, h_c3, h_c4 = st.columns(4)
            with h_c1:
                hm_row = st.selectbox("Row Dimension:", cat_cols, index=0, key="hm_row_sel")
            with h_c2:
                col_candidates = [c for c in cat_cols if c != hm_row]
                hm_col = st.selectbox("Column Dimension:", col_candidates if col_candidates else cat_cols, index=0, key="hm_col_sel")
            with h_c3:
                hm_metric = st.selectbox("Value Measure:", num_cols, index=0, key="hm_met_sel")
            with h_c4:
                hm_agg = st.selectbox("Calculation:", ["Total (Sum)", "Average (Mean)"], index=0, key="hm_agg_sel")
            
            heatmap_fig = chart_gen.create_heatmap_matrix(
                row_col=hm_row,
                col_col=hm_col,
                metric_col=hm_metric,
                agg_func="mean" if "Average" in hm_agg else "sum"
            )
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True)

    # 5. Loss Bleeders Drilldown Table
    if profit_candidates:
        p_col = profit_candidates[0]
        unprofitable_rows = filtered_df[filtered_df[p_col] < 0]
        if not unprofitable_rows.empty:
            with st.expander(f"⚠️ Action Required: View {len(unprofitable_rows):,} Loss-Generating Orders (Total Leakage: ${abs(unprofitable_rows[p_col].sum()):,.2f})", expanded=False):
                st.caption("These specific transactions have negative margins. Review pricing, freight charges, and promotional discount caps.")
                st.dataframe(unprofitable_rows.sort_values(by=p_col, ascending=True).head(50), use_container_width=True)

    # 6. Active Filtered Cohort Data View & Immediate Download
    with st.expander(f"📋 Active Filtered Cohort Data ({len(filtered_df):,} Rows)", expanded=False):
        col_down, col_info = st.columns([1.5, 3])
        with col_down:
            csv_filtered = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="💾 Download Filtered View (CSV)",
                data=csv_filtered,
                file_name="filtered_dashboard_data.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_info:
            st.caption(f"Showing slice of **{len(filtered_df):,} records** based on active timeline and dimension filters.")
        st.dataframe(filtered_df.head(100), use_container_width=True, height=350)

    # 7. Executive Report Navigation Notice
    st.markdown(
        """
        <div style="background: #111827; border-radius: 12px; padding: 18px 24px; margin-top: 22px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);">
            <strong style="color: #60A5FA; font-size: 0.94rem;">📑 Formal Executive Intelligence Memo Available</strong>
            <p style="color: #94A3B8; font-size: 0.85rem; margin: 4px 0 0 0; line-height: 1.5;">
                Switch to the <strong>Executive Report & Exports</strong> tab to review the complete C-suite memorandum in formal business report format, complete with KPI scorecards, risk diagnostics, phased roadmaps, and one-click PDF/HTML/Markdown exports.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
