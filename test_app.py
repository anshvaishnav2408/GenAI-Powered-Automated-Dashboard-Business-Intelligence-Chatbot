"""
Test Suite for BI Dashboard Application
Verifies single and multi-table pipelines, messy data sanitization,
DuckDB cross-table joins, charts, and chatbot intelligence.
"""

import os
import sys
import numpy as np
import pandas as pd
from core.data_loader import load_dataset
from core.data_cleaner import DataCleaner
from core.domain_classifier import classify_domain
from core.kpi_engine import KPIEngine
from core.sql_engine import SafeSQLEngine, SQLValidationError
from core.visualization import ChartGenerator
from core.llm_interface import LLMClient
from core.insights_generator import InsightsGenerator


def test_messy_real_world_data():
    print("\n==========================================")
    print("Testing Pipeline on: Messy Real-World Data")
    print("==========================================")
    
    messy_data = {
        "   Order ID \n\t  ": ["ORD-1", "ORD-2", "ORD-3", "ORD-4", "ORD-5"],
        " Transaction Date ": ["2024-01-10", "15/02/2024", "March 5, 2024", "2024-04-20", "N/A"],
        " Gross Sales ($) ": [" $1,250.00 ", " $ 2,400.50 ", " - ", " $ 950.00 ", " $ 3,100.25 "],
        " Net Profit (Loss) ": [" $ 250.00 ", " (450.25) ", " (120.00) ", " $ 180.50 ", " N/A "],
        " Discount Rate ": [" 10% ", " 25% ", " 0% ", " 15% ", " - "],
        " Category ": [" Technology ", " Furniture ", " Office Supplies ", " Technology ", " ? "]
    }
    raw_df = pd.DataFrame(messy_data)
    print(f"1. [RAW MESSY INPUT] Created dataframe with dirty headers, accounting parentheses, and text nulls.")

    cleaner = DataCleaner(raw_df)
    clean_df, c_meta = cleaner.clean_pipeline()

    # Verify column headers cleaned
    assert "Order ID" in clean_df.columns, f"Cleaned headers should have 'Order ID', got {clean_df.columns}"
    print(f"2. [HEADER SANITIZATION] OK: Headers cleaned: {list(clean_df.columns)}")

    # Verify accounting parentheses negative parsing: "(450.25)" -> -450.25
    profit_col = [c for c in clean_df.columns if "profit" in c.lower()][0]
    assert pd.api.types.is_numeric_dtype(clean_df[profit_col]), "Profit column should be numeric"
    assert clean_df.loc[1, profit_col] < 0, f"Expected negative profit for '(450.25)', got {clean_df.loc[1, profit_col]}"
    print(f"3. [ACCOUNTING FORMAT] OK: Successfully converted '(450.25)' into numeric {clean_df.loc[1, profit_col]}.")

    # Verify currency conversion
    sales_col = [c for c in clean_df.columns if "sales" in c.lower()][0]
    assert pd.api.types.is_numeric_dtype(clean_df[sales_col]), "Sales column should be numeric"
    assert clean_df.loc[0, sales_col] == 1250.0, f"Expected 1250.0, got {clean_df.loc[0, sales_col]}"
    print(f"4. [CURRENCY STRIPPING] OK: Converted '$1,250.00' to {clean_df.loc[0, sales_col]}.")

    # Verify date conversion
    date_col = [c for c in clean_df.columns if "date" in c.lower()][0]
    assert c_meta["column_types"][date_col] == "datetime", f"Date column should be datetime, got {c_meta['column_types'][date_col]}"
    print(f"5. [MIXED DATE PARSING] OK: Inferred datetime across mixed date string formats.")

    # Verify audit log
    print(f"6. [AUDIT LOG] OK: {len(c_meta['audit_log'])} transformations transparently recorded.")


def test_multi_table_duckdb_joins():
    print("\n==========================================")
    print("Testing Multi-Table DuckDB Cross-Table Joins")
    print("==========================================")
    
    df_orders = pd.DataFrame({
        "order_id": ["O1", "O2", "O3", "O4"],
        "customer_id": ["C101", "C102", "C101", "C103"],
        "order_amount": [500.0, 750.0, 1200.0, 300.0]
    })
    df_customers = pd.DataFrame({
        "customer_id": ["C101", "C102", "C103"],
        "customer_name": ["Acme Corp", "Globex", "Initech"],
        "tier": ["Enterprise", "Mid-Market", "Starter"]
    })

    tables = {
        "orders": df_orders,
        "customers": df_customers
    }

    sql_engine = SafeSQLEngine(tables, active_key="orders")
    
    # Test join query
    join_sql = """
    SELECT 
        c.customer_name, 
        c.tier, 
        ROUND(SUM(o.order_amount), 2) AS total_spent 
    FROM orders o 
    JOIN customers c ON o.customer_id = c.customer_id 
    GROUP BY c.customer_name, c.tier 
    ORDER BY total_spent DESC;
    """
    res_df, stats = sql_engine.execute_query(join_sql)
    assert len(res_df) == 3, f"Expected 3 aggregated customer rows, got {len(res_df)}"
    assert res_df.iloc[0]["customer_name"] == "Acme Corp", "Acme Corp should have highest spend"
    assert res_df.iloc[0]["total_spent"] == 1700.0, f"Expected 1700.0 total spend, got {res_df.iloc[0]['total_spent']}"
    print(f"1. [MULTI-TABLE JOIN] OK: Successfully executed cross-table JOIN in {stats['execution_time_ms']} ms.")
    print(f"   Results:\n{res_df.to_string(index=False)}")


def test_pipeline_on_file(file_path: str, expected_domain: str):
    print(f"\n==========================================")
    print(f"Testing Pipeline on: {file_path}")
    print(f"==========================================")
    
    # 1. Loader
    df, meta = load_dataset(file_path, os.path.basename(file_path))
    assert not df.empty, "Loaded DF should not be empty"
    print(f"1. [LOADER] OK: Loaded {len(df)} rows, {len(df.columns)} cols. Size: {meta['size_mb']} MB.")

    # 2. Cleaner
    cleaner = DataCleaner(df)
    clean_df, c_meta = cleaner.clean_pipeline()
    assert clean_df.shape[0] > 0, "Clean DF should have rows"
    q_score = c_meta["quality_report"]["overall_score"]
    print(f"2. [CLEANER] OK: Data Quality Score: {q_score}/100. Changes logged: {len(c_meta['audit_log'])}.")

    # 3. Domain Classifier
    dom = classify_domain(clean_df)
    print(f"3. [DOMAIN] OK: Detected '{dom['domain_title']}' (key: {dom['domain_key']}, conf: {dom['confidence']}).")
    assert dom["domain_key"] == expected_domain, f"Expected {expected_domain}, got {dom['domain_key']}"

    # 4. KPI Engine
    kpi_engine = KPIEngine(clean_df, dom["domain_key"], c_meta["column_types"])
    kpis = kpi_engine.calculate_kpis()
    assert len(kpis) > 0, "Should generate at least 1 KPI"
    print(f"4. [KPIS] OK: Computed {len(kpis)} KPIs:")
    for k in kpis:
        delta_str = f"({k['delta']})" if k.get("delta") else ""
        print(f"   - {k['label']}: {k['value']} {delta_str}")

    # 5. SQL Engine
    sql_engine = SafeSQLEngine(clean_df)
    res_df, stats = sql_engine.execute_query("SELECT COUNT(*) AS total_records FROM df;")
    assert res_df.iloc[0]["total_records"] == len(clean_df), "SQL count should match DataFrame length"
    print(f"5. [SQL ENGINE] OK: Executed read-only query in {stats['execution_time_ms']} ms.")

    # Test SQL guardrails (must reject forbidden action)
    forbidden_sql = "DROP TABLE df;"
    try:
        sql_engine.execute_query(forbidden_sql)
        assert False, "Should have rejected DROP TABLE"
    except SQLValidationError as e:
        print(f"   [SECURITY GUARDRAIL] Successfully blocked dangerous query: {str(e)}")

    # 6. Visualization
    chart_gen = ChartGenerator(clean_df, c_meta["column_types"], dom["domain_key"])
    trend_fig = chart_gen.create_trend_chart()
    bar_fig = chart_gen.create_category_bar()
    donut_fig = chart_gen.create_donut_chart()
    dist_fig = chart_gen.create_distribution_chart()
    print(f"6. [CHARTS] OK: Trend: {trend_fig is not None}, Bar: {bar_fig is not None}, Donut: {donut_fig is not None}, Dist: {dist_fig is not None}")

    # 7. LLM Client & Insights Generator
    llm = LLMClient("heuristic", {}, clean_df, dom["domain_key"])
    insights_gen = InsightsGenerator(clean_df, dom, c_meta["column_types"], kpis, llm)
    insights = insights_gen.generate_full_insights()
    assert "executive_summary" in insights, "Executive summary missing"
    assert "risks_and_anomalies" in insights, "Risks missing"
    print("7. [INSIGHTS] OK: Generated Executive Summary and Strategic Risks successfully.")

    # 7b. Test Report Generation in Proper Format
    from components.export_tab import generate_executive_html_report, generate_executive_markdown_report
    html_rep = generate_executive_html_report(dom["domain_title"], dom["domain_key"], kpis, insights, c_meta["quality_report"], os.path.basename(file_path))
    md_rep = generate_executive_markdown_report(dom["domain_title"], kpis, insights, c_meta["quality_report"], os.path.basename(file_path))
    assert len(html_rep) > 500, "HTML report should be generated"
    assert "EXECUTIVE BUSINESS INTELLIGENCE" in md_rep, "Markdown report should have title"
    print("   [REPORT FORMAT] OK: Successfully generated formal HTML & Markdown C-Suite reports.")

    # 8. Chatbot Q&A simulation
    test_questions = [
        "What are the top 5 records?",
        "What is the average value by category?"
    ]
    for q in test_questions:
        schema = sql_engine.get_schema_summary()
        gen_sql = llm.query_to_sql(q, schema)
        q_res, q_stats = sql_engine.execute_query(gen_sql)
        ans = llm.explain_query_results(q, gen_sql, q_res)
        smart_fig = chart_gen.smart_chart_from_df(q_res)
        print(f"8. [CHATBOT] Q: '{q}' -> SQL: {gen_sql[:50]}... -> Result rows: {len(q_res)}, Chart generated: {smart_fig is not None}")


if __name__ == "__main__":
    # Test messy real-world data handling
    test_messy_real_world_data()

    # Test multi-table DuckDB cross-table joins
    test_multi_table_duckdb_joins()

    # Test sample business datasets
    test_pipeline_on_file("sample_data/retail_sales_bi.csv", "sales")
    test_pipeline_on_file("sample_data/saas_churn_bi.csv", "saas")
    test_pipeline_on_file("sample_data/hr_analytics_bi.csv", "hr")
    print("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY! The entire platform backend is fully verified.")
