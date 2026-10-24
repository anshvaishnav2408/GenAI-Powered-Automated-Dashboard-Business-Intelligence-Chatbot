"""
Visualization Module
Commercial-grade Plotly data visualization with moving averages, benchmark annotations,
statistical correlation indicators, and modern corporate aesthetics.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


# Enterprise Corporate Palette (Stripe/Tableau/Bloomberg inspired)
PALETTE = [
    "#2563EB",  # Electric Navy
    "#0EA5E9",  # Sky Cyan
    "#10B981",  # Mint Emerald
    "#F59E0B",  # Warm Amber
    "#8B5CF6",  # Modern Purple
    "#EC4899",  # Rose Pink
    "#64748B",  # Slate
    "#06B6D4",  # Deep Teal
    "#F97316"   # Coral Orange
]

ENTERPRISE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", size=12, color="#94A3B8"),
    margin=dict(l=15, r=15, t=45, b=25),
    hoverlabel=dict(
        bgcolor="#0F172A",
        bordercolor="#334155",
        font_size=12,
        font_color="#F8FAFC",
        font_family="Plus Jakarta Sans, sans-serif"
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=11, color="#CBD5E1")
    )
)


class ChartGenerator:
    def __init__(self, df: pd.DataFrame, column_types: Dict[str, str], domain_key: str):
        self.df = df
        self.column_types = column_types
        self.domain_key = domain_key

    def _get_cols(self, col_type: str) -> List[str]:
        return [c for c, t in self.column_types.items() if t == col_type]

    def create_trend_chart(self, date_col: Optional[str] = None, metric_col: Optional[str] = None) -> Optional[go.Figure]:
        """Create executive time-series chart with trend area and moving average."""
        date_cols = self._get_cols("datetime")
        num_cols = self._get_cols("numeric")

        d_col = date_col or (date_cols[0] if date_cols else None)
        if not d_col or d_col not in self.df.columns:
            return None

        # Pick primary metric
        m_col = metric_col
        if not m_col and num_cols:
            for candidate in ["sales", "revenue", "profit", "mrr", "total_charges", "annual_salary", "spend"]:
                match = [c for c in num_cols if candidate in c.lower()]
                if match:
                    m_col = match[0]
                    break
            if not m_col:
                m_col = num_cols[0]

        if not m_col or m_col not in self.df.columns:
            return None

        valid = self.df.dropna(subset=[d_col, m_col]).copy()
        if len(valid) == 0:
            return None

        valid = valid.sort_values(by=d_col)
        span_days = (valid[d_col].max() - valid[d_col].min()).days
        freq = "ME" if span_days > 90 else "W" if span_days > 30 else "D"
        freq_label = "Monthly" if freq == "ME" else "Weekly" if freq == "W" else "Daily"

        grouped = valid.set_index(d_col)[m_col].resample(freq).sum().reset_index()
        if len(grouped) == 0:
            return None

        metric_title = m_col.replace("_", " ").title()

        fig = go.Figure()

        # Primary Area fill
        fig.add_trace(go.Scatter(
            x=grouped[d_col],
            y=grouped[m_col],
            name=f"{freq_label} Total",
            mode="lines+markers",
            line=dict(color="#2563EB", width=2.5),
            marker=dict(size=5, color="#3B82F6"),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.10)",
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Total: %{y:$,.2f}<extra></extra>" if "sales" in m_col.lower() or "revenue" in m_col.lower() or "profit" in m_col.lower() else "<b>%{x|%b %d, %Y}</b><br>Total: %{y:,.0f}<extra></extra>"
        ))

        # Add 3-period Rolling Moving Average if sufficient points exist
        if len(grouped) >= 5:
            grouped["MA"] = grouped[m_col].rolling(window=3, min_periods=1).mean()
            fig.add_trace(go.Scatter(
                x=grouped[d_col],
                y=grouped["MA"],
                name="3-Period Moving Avg",
                mode="lines",
                line=dict(color="#10B981", width=2, dash="dot"),
                hovertemplate="Moving Avg: %{y:$,.2f}<extra></extra>" if "sales" in m_col.lower() or "profit" in m_col.lower() else "Moving Avg: %{y:,.1f}<extra></extra>"
            ))

        fig.update_layout(
            **ENTERPRISE_LAYOUT,
            title=dict(
                text=f"<b>Performance Trajectory: {metric_title}</b> <span style='font-size:12px;color:#64748B;'>({freq_label} Aggregation)</span>",
                x=0.01,
                font=dict(size=14, color="#F8FAFC")
            )
        )
        fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", zeroline=False)
        return fig

    def create_category_bar(self, cat_col: Optional[str] = None, metric_col: Optional[str] = None, top_n: int = 10, agg_func: str = "sum") -> Optional[go.Figure]:
        """Create ranked horizontal bar chart with rounded corners and value formatting."""
        cat_cols = self._get_cols("categorical")
        num_cols = self._get_cols("numeric")

        c_col = cat_col or (cat_cols[0] if cat_cols else None)
        if not c_col or c_col not in self.df.columns:
            return None

        m_col = metric_col
        if not m_col and num_cols:
            for candidate in ["profit", "sales", "revenue", "mrr", "annual_salary"]:
                match = [c for c in num_cols if candidate in c.lower()]
                if match:
                    m_col = match[0]
                    break
            if not m_col:
                m_col = num_cols[0]

        if not m_col:
            grouped = self.df[c_col].value_counts().head(top_n).reset_index()
            grouped.columns = [c_col, "Count"]
            val_col = "Count"
        else:
            if agg_func.lower() == "mean":
                grouped = self.df.groupby(c_col)[m_col].mean().sort_values(ascending=False).head(top_n).reset_index()
            else:
                grouped = self.df.groupby(c_col)[m_col].sum().sort_values(ascending=False).head(top_n).reset_index()
            val_col = m_col

        grouped = grouped.sort_values(by=val_col, ascending=True)

        is_currency = any(k in val_col.lower() for k in ["sales", "revenue", "profit", "salary", "mrr", "cost", "charge", "price"])
        text_template = "$%{x:,.2s}" if is_currency else "%{x:,.2s}"
        agg_label = "Average" if agg_func.lower() == "mean" else "Total"

        fig = go.Figure(go.Bar(
            x=grouped[val_col],
            y=grouped[c_col],
            orientation="h",
            marker=dict(
                color=grouped[val_col],
                colorscale="Blues",
                line=dict(width=0)
            ),
            text=grouped[val_col],
            texttemplate=text_template,
            textposition="outside",
            hovertemplate=f"<b>%{{y}}</b><br>{agg_label} {val_col.replace('_', ' ').title()}: " + ("$%{x:,.2f}" if is_currency else "%{x:,.1f}") + "<extra></extra>"
        ))

        fig.update_layout(
            **ENTERPRISE_LAYOUT,
            title=dict(
                text=f"<b>Top {c_col.replace('_', ' ').title()} by {agg_label} {val_col.replace('_', ' ').title()}</b>",
                x=0.01,
                font=dict(size=14, color="#F8FAFC")
            ),
            xaxis=dict(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False)
        )
        return fig

    def create_heatmap_matrix(self, row_col: Optional[str] = None, col_col: Optional[str] = None, metric_col: Optional[str] = None, agg_func: str = "sum") -> Optional[go.Figure]:
        """Create cross-dimensional pivot heatmap matrix."""
        cat_cols = self._get_cols("categorical")
        num_cols = self._get_cols("numeric")

        if len(cat_cols) < 2 or not num_cols:
            return None

        r_col = row_col or cat_cols[0]
        c_col = col_col or (cat_cols[1] if len(cat_cols) > 1 else cat_cols[0])
        m_col = metric_col or num_cols[0]

        if r_col not in self.df.columns or c_col not in self.df.columns or m_col not in self.df.columns or r_col == c_col:
            return None

        top_r = self.df[r_col].value_counts().head(8).index
        top_c = self.df[c_col].value_counts().head(6).index
        subset = self.df[self.df[r_col].isin(top_r) & self.df[c_col].isin(top_c)]
        if subset.empty:
            return None

        pivot = subset.pivot_table(index=r_col, columns=c_col, values=m_col, aggfunc="mean" if agg_func == "mean" else "sum", fill_value=0)
        
        fig = px.imshow(
            pivot,
            labels=dict(x=c_col.replace('_', ' ').title(), y=r_col.replace('_', ' ').title(), color=m_col.replace('_', ' ').title()),
            color_continuous_scale="Blues",
            text_auto=True,
            aspect="auto"
        )
        agg_label = "Avg" if agg_func == "mean" else "Total"
        fig.update_layout(
            **ENTERPRISE_LAYOUT,
            title=dict(
                text=f"<b>Cross-Dimensional Matrix: {r_col.replace('_', ' ').title()} vs {c_col.replace('_', ' ').title()}</b> <span style='font-size:12px;color:#94A3B8;'>({agg_label} {m_col.replace('_', ' ').title()})</span>",
                x=0.01,
                font=dict(size=14, color="#F8FAFC")
            )
        )
        return fig

    def create_donut_chart(self, cat_col: Optional[str] = None, metric_col: Optional[str] = None) -> Optional[go.Figure]:
        """Create modern thin-ring donut chart with portfolio distribution."""
        cat_cols = self._get_cols("categorical")
        num_cols = self._get_cols("numeric")

        c_col = cat_col
        if not c_col:
            if len(cat_cols) > 1:
                for pref in ["region", "segment", "tier", "plan", "department", "type"]:
                    m = [c for c in cat_cols if pref in c.lower()]
                    if m:
                        c_col = m[0]
                        break
            if not c_col and cat_cols:
                c_col = cat_cols[-1]

        if not c_col or c_col not in self.df.columns:
            return None

        m_col = metric_col
        if not m_col and num_cols:
            for candidate in ["sales", "revenue", "mrr", "annual_salary"]:
                m = [c for c in num_cols if candidate in c.lower()]
                if m:
                    m_col = m[0]
                    break
            if not m_col:
                m_col = num_cols[0]

        if m_col:
            grouped = self.df.groupby(c_col)[m_col].sum().reset_index()
            val_col = m_col
        else:
            grouped = self.df[c_col].value_counts().reset_index()
            grouped.columns = [c_col, "Count"]
            val_col = "Count"

        # Limit to top 6 + other
        if len(grouped) > 6:
            sorted_g = grouped.sort_values(by=val_col, ascending=False)
            top = sorted_g.iloc[:5]
            other_sum = sorted_g.iloc[5:][val_col].sum()
            other_df = pd.DataFrame([{c_col: "Other", val_col: other_sum}])
            grouped = pd.concat([top, other_df], ignore_index=True)

        is_currency = any(k in val_col.lower() for k in ["sales", "revenue", "profit", "salary", "mrr"])

        fig = go.Figure(data=[go.Pie(
            labels=grouped[c_col],
            values=grouped[val_col],
            hole=0.64,
            marker=dict(colors=PALETTE, line=dict(color="#0F172A", width=2)),
            textinfo="percent",
            hovertemplate=f"<b>%{{label}}</b><br>Share: %{{percent}}<br>Value: " + ("$%{value:,.2f}" if is_currency else "%{value:,.0f}") + "<extra></extra>"
        )])

        fig.update_layout(
            **ENTERPRISE_LAYOUT,
            title=dict(
                text=f"<b>Portfolio Allocation: {c_col.replace('_', ' ').title()}</b>",
                x=0.01,
                font=dict(size=14, color="#F8FAFC")
            )
        )
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
        )
        return fig

    def create_distribution_chart(self, num_col: Optional[str] = None) -> Optional[go.Figure]:
        """Create distribution histogram with statistical mean/median benchmarks."""
        num_cols = self._get_cols("numeric")
        n_col = num_col or (num_cols[0] if num_cols else None)
        if not n_col or n_col not in self.df.columns:
            return None

        series = self.df[n_col].dropna()
        if len(series) == 0:
            return None

        mean_val = series.mean()
        median_val = series.median()

        fig = px.histogram(
            self.df,
            x=n_col,
            nbins=32,
            marginal="box",
            color_discrete_sequence=["#0EA5E9"],
            opacity=0.85
        )

        # Add vertical line for mean
        fig.add_vline(
            x=mean_val,
            line_dash="dash",
            line_color="#F59E0B",
            annotation_text=f"Mean: {mean_val:,.1f}",
            annotation_position="top right"
        )

        fig.update_layout(
            **ENTERPRISE_LAYOUT,
            title=dict(
                text=f"<b>Distribution & Statistical Spread: {n_col.replace('_', ' ').title()}</b>",
                x=0.01,
                font=dict(size=14, color="#F8FAFC")
            )
        )
        fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", zeroline=False)
        return fig

    def create_scatter_correlation(self, x_col: Optional[str] = None, y_col: Optional[str] = None, color_col: Optional[str] = None) -> Optional[go.Figure]:
        """Create correlation scatter with Pearson correlation coefficient."""
        num_cols = self._get_cols("numeric")
        cat_cols = self._get_cols("categorical")

        if len(num_cols) < 2:
            return None

        xc = x_col or num_cols[0]
        yc = y_col or num_cols[1]
        cc = color_col or (cat_cols[0] if cat_cols else None)

        # Compute correlation
        corr_val = self.df[[xc, yc]].dropna().corr().iloc[0, 1]
        corr_label = f"r = {corr_val:.2f}" if not pd.isna(corr_val) else ""

        try:
            fig = px.scatter(
                self.df,
                x=xc,
                y=yc,
                color=cc if cc and cc in self.df.columns else None,
                color_discrete_sequence=PALETTE,
                trendline="ols" if len(self.df) < 5000 else None,
                opacity=0.75
            )
        except Exception:
            fig = px.scatter(
                self.df,
                x=xc,
                y=yc,
                color=cc if cc and cc in self.df.columns else None,
                color_discrete_sequence=PALETTE,
                trendline=None,
                opacity=0.75
            )

        fig.update_layout(
            **ENTERPRISE_LAYOUT,
            title=dict(
                text=f"<b>Bivariate Relationship: {xc.replace('_', ' ').title()} vs {yc.replace('_', ' ').title()}</b> <span style='font-size:12px;color:#F59E0B;'>({corr_label})</span>",
                x=0.01,
                font=dict(size=14, color="#F8FAFC")
            )
        )
        fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", zeroline=False)
        return fig

    def smart_chart_from_df(self, query_df: pd.DataFrame, title: str = "Query Results") -> Optional[go.Figure]:
        """Infers the cleanest commercial chart for ad-hoc SQL query results."""
        if query_df.empty or len(query_df.columns) < 2:
            return None

        cols = list(query_df.columns)
        num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(query_df[c])]
        non_num_cols = [c for c in cols if not pd.api.types.is_numeric_dtype(query_df[c])]

        if len(non_num_cols) == 1 and len(num_cols) >= 1:
            cat_c = non_num_cols[0]
            val_c = num_cols[0]

            is_date = False
            cat_name = str(cat_c).lower()
            if any(k in cat_name for k in ["date", "time", "month", "year", "day"]):
                try:
                    dt_series = pd.to_datetime(query_df[cat_c], format="mixed", errors="coerce")
                    if dt_series.notna().sum() > 0:
                        is_date = True
                except Exception:
                    pass

            if is_date:
                fig = px.line(query_df, x=cat_c, y=val_c, markers=True, color_discrete_sequence=[PALETTE[0]])
            elif len(query_df) <= 10:
                fig = px.bar(query_df, x=cat_c, y=val_c, color=val_c, color_continuous_scale="Blues", text=val_c)
                fig.update_traces(texttemplate="%{text:,.2s}", textposition="outside")
                fig.update_layout(coloraxis_showscale=False)
            else:
                fig = px.bar(query_df.head(15), y=cat_c, x=val_c, orientation="h", color_discrete_sequence=[PALETTE[0]])
                fig.update_layout(yaxis=dict(autorange="reversed"))

            fig.update_layout(
                **ENTERPRISE_LAYOUT,
                title=dict(text=f"<b>{title}</b>", x=0.01, font=dict(size=13, color="#F8FAFC"))
            )
            fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)")
            fig.update_yaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)")
            return fig

        elif len(num_cols) >= 2:
            fig = px.scatter(
                query_df,
                x=num_cols[0],
                y=num_cols[1],
                color=non_num_cols[0] if non_num_cols else None,
                color_discrete_sequence=PALETTE
            )
            fig.update_layout(
                **ENTERPRISE_LAYOUT,
                title=dict(text=f"<b>{title}</b>", x=0.01, font=dict(size=13, color="#F8FAFC"))
            )
            return fig

        return None
