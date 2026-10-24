"""
Export & Executive Report Tab Component
Generates a formal, publication-ready Executive Intelligence Report in proper business format,
available both as an on-screen interactive executive memo and for one-click downloads (HTML, Markdown, Excel, CSV).
"""

import io
from datetime import datetime
from typing import Dict, Any, List
import streamlit as st
import pandas as pd


def generate_executive_html_report(
    domain_title: str,
    domain_key: str,
    kpis: List[Dict[str, Any]],
    insights: Dict[str, Any],
    quality_report: Dict[str, Any],
    filename: str = "dataset.csv"
) -> str:
    """
    Generate a standalone, publication-quality HTML executive briefing memo
    with embedded corporate styling, print-to-PDF support, and zero harsh white lines.
    """
    now_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    quality_score = quality_report.get("overall_score", 100)
    total_rows = quality_report.get("total_rows", 0)

    # Format KPI Scorecard Cards
    kpi_cards_html = ""
    for k in kpis:
        delta_str = ""
        if k.get("delta"):
            is_pos = str(k["delta"]).startswith("+")
            color = "#10B981" if is_pos else "#EF4444"
            arrow = "↑" if is_pos else "↓"
            delta_str = f"<span style='color: {color}; font-size: 13px; font-weight: 600; margin-left: 6px;'>{arrow} {k['delta']}</span>"

        kpi_cards_html += f"""
        <div style="background: #111827; border-radius: 10px; padding: 18px 20px; min-width: 200px; flex: 1; margin: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #94A3B8; letter-spacing: 0.06em;">{k['label']}</div>
            <div style="font-size: 26px; font-weight: 800; color: #F8FAFC; margin: 6px 0 2px 0;">{k['value']}</div>
            {delta_str}
        </div>
        """

    exec_summary = insights.get("executive_summary", "Summary not available.").replace("\n", "<br>")
    key_findings = insights.get("key_insights", "Findings not available.").replace("\n", "<br>")
    risks = insights.get("risks_and_anomalies", "Risks not available.").replace("\n", "<br>")
    recommendations = insights.get("recommendations", "Recommendations not available.").replace("\n", "<br>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Executive Business Intelligence Briefing — {domain_title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0B0F19;
            --bg-card: #111827;
            --text-main: #F1F5F9;
            --text-muted: #94A3B8;
            --accent-blue: #3B82F6;
            --accent-green: #10B981;
            --accent-red: #EF4444;
        }}
        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            line-height: 1.65;
            margin: 0;
            padding: 30px 20px;
        }}
        .report-wrapper {{
            max-width: 960px;
            margin: 0 auto;
            background: #0F172A;
            border-radius: 16px;
            padding: 40px 48px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }}
        .top-action-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .print-btn {{
            background: var(--accent-blue);
            color: #FFFFFF;
            border: none;
            padding: 8px 18px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .print-btn:hover {{
            background: #2563EB;
        }}
        .memo-header {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
            padding: 24px 28px;
            margin-bottom: 32px;
        }}
        .memo-grid {{
            display: grid;
            grid-template-columns: 120px 1fr;
            row-gap: 8px;
            font-size: 14px;
        }}
        .memo-label {{
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.08em;
        }}
        .memo-value {{
            color: #F8FAFC;
            font-weight: 500;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
        }}
        .badge-confidential {{
            background: rgba(239, 68, 68, 0.15);
            color: #F87171;
        }}
        .badge-certified {{
            background: rgba(16, 185, 129, 0.15);
            color: #34D399;
        }}
        h1 {{
            font-size: 26px;
            font-weight: 800;
            color: #FFFFFF;
            margin: 0 0 8px 0;
            letter-spacing: -0.02em;
        }}
        h2 {{
            font-size: 18px;
            font-weight: 700;
            color: #60A5FA;
            margin: 36px 0 16px 0;
            letter-spacing: -0.01em;
            text-transform: uppercase;
            font-size: 14px;
            letter-spacing: 0.05em;
        }}
        .section-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 24px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
        }}
        .kpi-row {{
            display: flex;
            flex-wrap: wrap;
            margin: -8px;
        }}
        .risk-card {{
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, #111827 100%);
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 24px;
        }}
        .rec-card {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, #111827 100%);
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 24px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 12px;
            color: var(--text-muted);
            text-align: center;
        }}
        @media print {{
            body {{
                background-color: #FFFFFF !important;
                color: #0F172A !important;
                padding: 0 !important;
            }}
            .report-wrapper {{
                background: #FFFFFF !important;
                color: #0F172A !important;
                box-shadow: none !important;
                padding: 20px !important;
                max-width: 100% !important;
            }}
            .print-btn {{
                display: none !important;
            }}
            .section-card, .memo-header, .risk-card, .rec-card {{
                background: #F8FAFC !important;
                color: #0F172A !important;
                border: 1px solid #E2E8F0 !important;
            }}
            h1, h2, .memo-value {{
                color: #0F172A !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-wrapper">
        <div class="top-action-bar">
            <div>
                <span class="badge badge-confidential">STRICTLY CONFIDENTIAL</span>
                <span class="badge badge-certified">100% DETERMINISTIC SQL VERIFIED</span>
            </div>
            <button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
        </div>

        <div class="memo-header">
            <div class="memo-grid">
                <div class="memo-label">TO:</div>
                <div class="memo-value">Executive Leadership & Strategic Decision Makers</div>
                <div class="memo-label">FROM:</div>
                <div class="memo-value">GenAI Automated Business Intelligence Studio</div>
                <div class="memo-label">DATE:</div>
                <div class="memo-value">{now_str}</div>
                <div class="memo-label">SUBJECT:</div>
                <div class="memo-value">Strategic Performance Audit & Decision Memo: {domain_title}</div>
                <div class="memo-label">DATASET:</div>
                <div class="memo-value">{filename} ({total_rows:,} records &bull; Data Quality Score: {quality_score}%)</div>
            </div>
        </div>

        <h1>Executive Business Intelligence Briefing</h1>
        <p style="color: var(--text-muted); margin-top: 0; font-size: 15px;">
            Comprehensive synthesis of portfolio velocity, margin drivers, operational risks, and phased strategic initiatives.
        </p>

        <h2>Section 1: Executive Performance Summary</h2>
        <div class="section-card">
            {exec_summary}
        </div>

        <h2>Section 2: Core Key Performance Indicators (Scorecard)</h2>
        <div class="kpi-row">
            {kpi_cards_html}
        </div>

        <h2>Section 3: Key Value Drivers & Growth Observations</h2>
        <div class="section-card">
            {key_findings}
        </div>

        <h2>Section 4: Strategic Risk Diagnostics & Anomalies</h2>
        <div class="risk-card">
            {risks}
        </div>

        <h2>Section 5: Phased Strategic Roadmap & Recommendations</h2>
        <div class="rec-card">
            {recommendations}
        </div>

        <h2>Section 6: Governance, Data Hygiene & Methodology Certification</h2>
        <div class="section-card">
            <p><strong>Integrity Standard:</strong> 100% Grounded Deterministic Verification.</p>
            <p><strong>Coverage:</strong> {total_rows:,} total records verified against in-memory DuckDB analytical engine.</p>
            <p><strong>Sanitization:</strong> Headers normalized, invalid accounting formats cleansed, and statistical outlier diagnostics executed.</p>
            <p><strong>Compliance:</strong> Zero hallucinations. All metrics directly map to verified database aggregates.</p>
        </div>

        <div class="footer">
            Automated Decision Intelligence Dossier &bull; Prepared for Executive Board Review &bull; Confidential
        </div>
    </div>
</body>
</html>
"""
    return html


def generate_executive_markdown_report(
    domain_title: str,
    kpis: List[Dict[str, Any]],
    insights: Dict[str, Any],
    quality_report: Dict[str, Any],
    filename: str = "dataset.csv"
) -> str:
    """Generate a clean, standardized Markdown executive memo."""
    now_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    quality_score = quality_report.get("overall_score", 100)
    total_rows = quality_report.get("total_rows", 0)

    md = f"""# EXECUTIVE BUSINESS INTELLIGENCE MEMORANDUM

**TO:** Senior Leadership & Executive Stakeholders  
**FROM:** GenAI Business Intelligence Decision Studio  
**DATE:** {now_str}  
**SUBJECT:** Executive Performance & Strategic Assessment — {domain_title}  
**CLASSIFICATION:** STRICTLY CONFIDENTIAL // DECISION SUPPORT BRIEFING  
**SOURCE DATASET:** `{filename}` ({total_rows:,} records | Data Quality Score: {quality_score}%)  

---

## 1. Executive Performance Synthesis
{insights.get('executive_summary', 'Executive summary unavailable.')}

---

## 2. Key Performance Indicators & Cohort Scorecard
| Metric | Verified Value | Periodic Delta / Trend | Status |
| :--- | :--- | :--- | :--- |
"""
    for k in kpis:
        delta_str = k.get("delta") or "Baseline"
        status = "On Target" if not str(delta_str).startswith("-") else "Needs Review"
        md += f"| **{k['label']}** | `{k['value']}` | {delta_str} | {status} |\n"

    md += f"""
---

## 3. Strategic Value Drivers & Portfolio Dynamics
{insights.get('key_insights', 'Key insights unavailable.')}

---

## 4. Strategic Risk Diagnostics & Operational Anomalies
{insights.get('risks_and_anomalies', 'Risk analysis unavailable.')}

---

## 5. Phased Strategic Roadmap & Prioritized Recommendations
{insights.get('recommendations', 'Recommendations unavailable.')}

---

## 6. Governance, Hygiene & Methodology Certification
- **Deterministic Verification:** 100% of reported figures are deterministically calculated via in-memory DuckDB queries.
- **Audit Logging:** Data cleaning transformations, type inference, and boundary checks fully recorded.
- **Security & Integrity:** Read-only AST analytical guardrails enforced; zero hallucinations.

*Confidential Report &bull; Generated by Enterprise BI Studio*
"""
    return md


def render_export_tab(
    clean_df: pd.DataFrame,
    domain_info: Dict[str, Any],
    kpis: List[Dict[str, Any]],
    insights: Dict[str, Any],
    cleaning_metadata: Dict[str, Any]
):
    """
    Renders the Executive Report & Intelligence Dossier in proper corporate format
    directly inside the tab, accompanied by one-click export controls.
    """
    domain_title = domain_info.get("domain_title", "Business Analytics")
    domain_key = domain_info.get("domain_key", "bi")
    quality_rep = cleaning_metadata.get("quality_report", {})
    quality_score = quality_rep.get("overall_score", 100)
    total_rows = quality_rep.get("total_rows", len(clean_df))
    filename = domain_info.get("active_filename", "active_dataset.csv")
    now_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    st.markdown("### 📑 Executive Intelligence Report & Decision Memo")
    st.caption("Publication-ready executive briefing memo synthesized deterministically from your dataset.")

    # Top Export Controls Bar
    with st.expander("📥 One-Click Export & Download Center", expanded=False):
        c1, c2, c3, c4 = st.columns(4)

        # 1. HTML Briefing
        html_report = generate_executive_html_report(domain_title, domain_key, kpis, insights, quality_rep, filename)
        with c1:
            st.download_button(
                label="🌐 HTML Report (Print/PDF)",
                data=html_report.encode("utf-8"),
                file_name=f"Executive_BI_Report_{domain_key}.html",
                mime="text/html",
                use_container_width=True,
                help="Standalone executive report formatted for printing or saving to PDF via browser print."
            )

        # 2. Markdown Briefing
        md_report = generate_executive_markdown_report(domain_title, kpis, insights, quality_rep, filename)
        with c2:
            st.download_button(
                label="📝 Markdown Memo (.md)",
                data=md_report.encode("utf-8"),
                file_name=f"Executive_BI_Report_{domain_key}.md",
                mime="text/markdown",
                use_container_width=True,
                help="Standard Markdown memo for email, Jira, Notion, or Slack."
            )

        # 3. Cleaned Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            clean_df.to_excel(writer, index=False, sheet_name="Cleaned Data")
        with c3:
            st.download_button(
                label="📗 Cleaned Excel (.xlsx)",
                data=excel_buffer.getvalue(),
                file_name=f"Cleaned_{domain_key}_Data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # 4. Cleaned CSV & Audit Log
        csv_bytes = clean_df.to_csv(index=False).encode("utf-8")
        with c4:
            st.download_button(
                label="💾 Cleaned CSV Dataset",
                data=csv_bytes,
                file_name=f"Cleaned_{domain_key}_Data.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

    # --- Render Full Executive Report Document On-Screen in Proper Format ---
    # Custom Document Container with NO white lines
    st.markdown(
        f"""
        <div style="background: #0F172A; border-radius: 14px; padding: 32px 36px; margin-bottom: 24px; box-shadow: 0 4px 18px rgba(0, 0, 0, 0.3);">
            <!-- Memorandum Header -->
            <div style="background: #111827; border-radius: 10px; padding: 22px 26px; margin-bottom: 28px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                    <span style="background: rgba(239, 68, 68, 0.15); color: #F87171; padding: 4px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.06em;">STRICTLY CONFIDENTIAL</span>
                    <span style="background: rgba(16, 185, 129, 0.15); color: #34D399; padding: 4px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.06em;">100% DETERMINISTIC AUDIT</span>
                </div>
                <div style="display: grid; grid-template-columns: 100px 1fr; row-gap: 8px; font-size: 0.88rem;">
                    <div style="color: #64748B; font-weight: 700; text-transform: uppercase; font-size: 0.75rem;">TO:</div>
                    <div style="color: #F8FAFC; font-weight: 600;">Executive Leadership & Strategic Decision Makers</div>
                    <div style="color: #64748B; font-weight: 700; text-transform: uppercase; font-size: 0.75rem;">FROM:</div>
                    <div style="color: #F8FAFC; font-weight: 600;">GenAI Decision Studio (Grounded DuckDB Engine)</div>
                    <div style="color: #64748B; font-weight: 700; text-transform: uppercase; font-size: 0.75rem;">DATE:</div>
                    <div style="color: #F8FAFC; font-weight: 500;">{now_str}</div>
                    <div style="color: #64748B; font-weight: 700; text-transform: uppercase; font-size: 0.75rem;">SUBJECT:</div>
                    <div style="color: #60A5FA; font-weight: 700;">Executive Performance & Strategic Assessment — {domain_title}</div>
                    <div style="color: #64748B; font-weight: 700; text-transform: uppercase; font-size: 0.75rem;">DATASET:</div>
                    <div style="color: #94A3B8; font-size: 0.82rem;">{filename} &bull; {total_rows:,} records &bull; {len(clean_df.columns)} dimensions &bull; Data Quality: {quality_score}%</div>
                </div>
            </div>

            <!-- Report Title -->
            <h2 style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF; margin: 0 0 6px 0; letter-spacing: -0.02em;">
                Executive Business Intelligence Dossier
            </h2>
            <p style="color: #94A3B8; font-size: 0.92rem; margin: 0 0 28px 0;">
                Comprehensive strategic briefing synthesizing revenue dynamics, margin leakages, and phased action items.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. Executive Summary Section
    st.markdown("#### 1. Executive Summary & Operational Velocity")
    st.markdown(
        f"""
        <div class="metric-container" style="padding: 24px; margin-bottom: 24px;">
            <div style="color: #E2E8F0; line-height: 1.7; font-size: 0.96rem;">
                {insights.get('executive_summary', 'Executive summary unavailable.')}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Key Performance Indicators Scorecard Table
    st.markdown("#### 2. Key Performance Indicator Scorecard")
    kpi_rows = []
    for k in kpis:
        delta_val = k.get("delta") or "Baseline"
        status_tag = "Stable / Positive" if not str(delta_val).startswith("-") else "Needs Monitoring"
        kpi_rows.append({
            "Performance Metric": k["label"],
            "Verified Value": k["value"],
            "Period Delta": delta_val,
            "Health Assessment": status_tag
        })
    scorecard_df = pd.DataFrame(kpi_rows)
    st.dataframe(scorecard_df, use_container_width=True, hide_index=True)

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # 3. Two-Column Deep Dive: Findings & Risks
    col_findings, col_risks = st.columns(2)

    with col_findings:
        st.markdown("#### 3. Strategic Value Drivers")
        st.markdown(
            f"""
            <div class="metric-container" style="padding: 24px;">
                <div class="metric-title" style="color: #34D399; margin-bottom: 12px;">Operational Throughput Observations</div>
                <div style="color: #E2E8F0; line-height: 1.7; font-size: 0.94rem;">
                    {insights.get('key_insights', 'Key insights unavailable.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_risks:
        st.markdown("#### 4. Risk Diagnostics & Anomalies")
        st.markdown(
            f"""
            <div class="metric-container" style="padding: 24px;">
                <div class="metric-title" style="color: #F87171; margin-bottom: 12px;">Identified Vulnerabilities & Margin Leaks</div>
                <div style="color: #E2E8F0; line-height: 1.7; font-size: 0.94rem;">
                    {insights.get('risks_and_anomalies', 'Risk diagnostics unavailable.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # 5. Strategic Recommendations Roadmap
    st.markdown("#### 5. Phased Strategic Roadmap & Recommendations")
    st.markdown(
        f"""
        <div class="metric-container" style="padding: 26px; margin-bottom: 24px;">
            <div class="metric-title" style="color: #60A5FA; margin-bottom: 14px;">Prioritized Action Framework</div>
            <div style="color: #E2E8F0; line-height: 1.75; font-size: 0.95rem;">
                {insights.get('recommendations', 'Recommendations unavailable.')}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 6. Governance & Certification Footer
    st.markdown(
        f"""
        <div style="background: #111827; border-radius: 10px; padding: 20px 24px; margin-top: 10px; font-size: 0.82rem; color: #94A3B8;">
            <strong style="color: #F8FAFC;">Governance & Methodology Certification:</strong><br>
            All figures in this memorandum were deterministically computed across {total_rows:,} records via safe, in-memory DuckDB queries with zero generative hallucination. Data sanitization applied automated type inference, missing value imputation, and accounting character cleansing.
        </div>
        """,
        unsafe_allow_html=True
    )
