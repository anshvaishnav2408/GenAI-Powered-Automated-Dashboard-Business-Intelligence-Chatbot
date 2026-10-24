# 📈 GenAI-Powered Automated BI Dashboard & Conversational Analyst

A complete, production-grade Business Intelligence application that converts any uploaded CSV or Excel dataset into an automated, interactive analytics dashboard, executive insights briefing, and natural language data chatbot.

Built with **Streamlit**, **Pandas**, **Plotly**, **DuckDB**, and a modular **GenAI LLM architecture** (supporting local Ollama, Google Gemini, OpenAI/Groq/DeepSeek, and an offline Built-in Heuristic Analyst).

---

## 🌟 Key Features

### 1. Multi-File Ingestion & Automatic Delimiter Detection
- **Multi-File Upload**: Upload multiple `.csv`, `.tsv`, `.xlsx`, or `.xls` files simultaneously.
- **Cross-Table DuckDB Registration**: All uploaded files are registered in in-memory DuckDB, enabling both individual dataset switching and cross-table `JOIN` queries.
- **Delimiter Sniffing**: Automatically detects `,`, `;`, `\t`, or `|` delimiters with encoding detection (`utf-8`, `latin-1`, `cp1252`).

### 2. Deep Sanitization for Messy Real-World Data
- **Dirty Null Conversion**: Automatically recognizes and maps text representations like `"N/A"`, `"-"`, `"None"`, `"null"`, `"?"`, `"missing"`, and `"#N/A"` into standardized system nulls.
- **Accounting Parentheses Parsing**: Accurately converts accounting negative numbers such as `"(450.25)"` into `-450.25`.
- **Currency & Formatted Number Stripping**: Cleans currency symbols (`$`, `€`, `£`, `₹`), percentage signs, and thousands separator commas into true numeric columns.
- **Header Normalization**: Strips rogue whitespace, newlines (`\n`), and tabs from column headers.
- **Mixed Date Engine**: Parses mixed-format dates (`2024-01-10`, `15/02/2024`, `March 5, 2024`) seamlessly.
- **Transparent Audit Trail**: Every cleaning action is recorded in the **Cleaning Audit Log**.
- **Data Quality Score**: Computes an objective 0–100 quality health score based on completeness, uniqueness, and consistency.
- **Outlier Inspector**: Detects anomalies using both **IQR (Interquartile Range)** and **Z-Score ($|z| > 3$)** methods, complete with interactive box plots.
- **No Silent Data Loss**: Safe defaults ensure important columns and rows are never dropped silently.

### 3. Automatic Dashboard & KPI Generation
- **Domain Auto-Classification**: Automatically detects whether the dataset belongs to **Sales & Retail**, **SaaS/Subscription**, **Human Resources**, **Finance**, **Marketing**, or **General Analytics**.
- **Context-Aware KPIs**: Formulates the top 4–6 domain metrics (e.g. Total Revenue, Profit, Margin %, AOV, Headcount, Churn Rate, MRR, Tenure) with period-over-period trend deltas.
- **Interactive Visualizations (Plotly)**:
  - 📈 **Time-Series Trend**: Area/line charts aggregated by Month/Week/Day.
  - 📊 **Category Comparison**: Ranked horizontal bar charts.
  - 🍩 **Composition Share**: Donut charts with percentage slices.
  - 📉 **Distribution & Spread**: Histograms with marginal box plots.
  - 🔍 **Multi-variable Scatter**: Interactive correlation explorer with trendlines.
- **Global Dynamic Cross-Filtering**: Date range pickers and multi-select category filters dynamically slice metrics and charts across the dashboard.

### 4. GenAI Business Insights (Grounded in Verified Facts)
- **Executive Briefing**: High-level synthesis for leadership and management meetings.
- **Key Business Findings**: Fact-grounded insights citing exact values and shares.
- **Risks & Anomalies**: Identifies margin leakages (negative profit orders), revenue concentration, or churn vulnerabilities.
- **Strategic Recommendations**: Actionable, prioritized next steps.
- **Hypothesis Accountability**: Assumptions and non-causal observations are clearly labeled with `[Hypothesis]` to ensure correlation is never confused with causation.
- **Zero Hallucination Guarantee**: All numbers are pre-computed deterministically before being presented or passed to the LLM.

### 5. AI Business Chatbot (Powered by Safe DuckDB SQL)
- **Natural Language to SQL**: Converts plain-English questions into read-only DuckDB SQL queries against the dataset in memory.
- **Deterministic Arithmetic**: Calculations are executed directly by the SQL engine in milliseconds rather than relying on LLM memory arithmetic.
- **Security Guardrails**:
  - Rejects any query containing modifying or unsafe tokens (`DROP`, `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `ATTACH`, `EXEC`, `PRAGMA`, etc.).
  - Strictly enforces `SELECT` or `WITH` queries.
- **Rich Multi-Modal Responses**: Returns natural language answers with exact figures, transparent SQL query inspection, interactive result data tables, and auto-generated Plotly charts.
- **Pre-Built Suggested Questions**: One-click quick questions tailored to the loaded domain.

### 6. Export Center
- **Cleaned Data**: Download cleaned datasets in **CSV** or **Excel (.xlsx)** format.
- **Audit Log**: Download the complete transformation log in CSV.
- **Executive Presentation Report**: Export standalone **HTML** and **Markdown** reports ready for stakeholder distribution and printing.

---

## 🏗️ System Architecture

```
├── app.py                      # Streamlit application entrypoint & routing
├── requirements.txt            # Project dependencies
├── test_app.py                 # Automated test suite
├── core/
│   ├── data_loader.py          # Safe CSV/Excel loading and validation
│   ├── data_cleaner.py         # Automated profiling, outlier detection & audit log
│   ├── domain_classifier.py    # Business domain classification & KPI recommendations
│   ├── kpi_engine.py           # Domain KPI formulation & trend delta calculation
│   ├── sql_engine.py           # Safe in-memory DuckDB query engine with security guardrails
│   ├── visualization.py        # Automated responsive Plotly chart generation
│   ├── llm_interface.py        # Modular LLM clients (Ollama, Gemini, OpenAI, Heuristic)
│   └── insights_generator.py   # Grounded executive summary & recommendations
├── components/
│   ├── ui_helpers.py           # Custom CSS, KPI cards, and visual badges
│   ├── overview_tab.py         # Tab 1: KPI cards, dynamic filters, and charts
│   ├── explorer_tab.py         # Tab 2: Data preview, quality score, outlier inspector
│   ├── insights_tab.py         # Tab 3: GenAI Executive summary & strategic actions
│   ├── chatbot_tab.py          # Tab 4: Conversational DuckDB SQL assistant
│   └── export_tab.py           # Tab 5: Cleaned CSV/Excel & HTML report export
└── sample_data/                # Built-in realistic sample datasets
    ├── retail_sales_bi.csv     # Superstore retail transactions & profit
    ├── saas_churn_bi.csv       # SaaS subscription & churn analytics
    └── hr_analytics_bi.csv     # Employee retention & workforce analytics
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, 3.13)

### 2. Installation
Clone or navigate to the project directory:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Launch the Streamlit web application:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Running the Test Suite
Verify that all core pipeline components, cleaning steps, and security guardrails pass:
```bash
python test_app.py
```

---

## 🤖 Supported AI Providers

You can select your AI provider in the sidebar:
1. **⚡ Built-in Heuristic Analyst (Default & Offline)**:
   - Works immediately out-of-the-box with **zero API keys** and **no setup**.
   - Employs deterministic analytical algorithms and business heuristics.
2. **🦙 Local Ollama (100% Private)**:
   - Connects to your local Ollama instance (`http://localhost:11434`) running models such as `llama3`, `mistral`, or `qwen2.5`.
3. **🔮 Google Gemini API**:
   - Uses `gemini-2.5-flash` or `gemini-1.5-flash` via the `google-genai` SDK or REST fallback.
4. **🤖 OpenAI & Compatible APIs**:
   - Supports OpenAI (`gpt-4o-mini`), Groq, DeepSeek, OpenRouter, or local LM Studio endpoints.

---

## 🔒 Reliability & Security Standards

- **Strict Read-Only SQL**: DuckDB executes in-memory. Modifying commands (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `EXEC`) are blocked before execution.
- **Privacy Protection**: Calculations are performed locally. When an external LLM is selected, only aggregated metadata and SQL schemas are transmitted.
- **Deterministic Math**: Arithmetic is computed by DuckDB or Pandas; LLMs are never asked to perform mental math on table rows.
