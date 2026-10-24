"""
Business Chatbot Tab Component
Natural language BI assistant that converts business questions into safe DuckDB SQL queries,
executes calculations deterministically, and renders explanations, tables, and charts.
"""

from typing import Dict, List, Any
import streamlit as st
import pandas as pd
from core.sql_engine import SafeSQLEngine, SQLValidationError
from core.llm_interface import LLMClient
from core.visualization import ChartGenerator


DOMAIN_SAMPLE_QUESTIONS = {
    "sales": [
        "What are the top 5 products by revenue?",
        "Which region generates the highest profit?",
        "Which customer segment is the most valuable?",
        "Which products have high sales but negative or low profit?",
        "Why did sales decrease in a particular month?",
        "What should the business do to improve profitability?",
        "What are the major business risks in this dataset?",
        "What additional data would help improve these business decisions?"
    ],
    "saas": [
        "What is the churn rate by plan tier?",
        "Which contract type generates the highest MRR?",
        "Compare average tenure across subscription plans.",
        "Show accounts with high support tickets and low NPS.",
        "What should the business do to improve customer retention?",
        "What are the major revenue risks in this dataset?",
        "What additional data would help improve churn predictions?"
    ],
    "hr": [
        "Which department has the highest attrition rate?",
        "What is the average salary by job role?",
        "Is attrition higher among employees working overtime?",
        "Show employee distribution across performance ratings.",
        "What should the company do to reduce employee turnover?",
        "What are the major workforce risks in this dataset?"
    ],
    "general": [
        "What are the top 5 categories by total value?",
        "Show the monthly or periodic distribution of records.",
        "Summarize key metrics by category.",
        "Which records have the highest variance or risk?"
    ]
}


def render_chatbot_tab(
    df: pd.DataFrame,
    column_types: Dict[str, str],
    domain_info: Dict[str, Any],
    sql_engine: SafeSQLEngine,
    llm_client: LLMClient
):
    st.markdown("### Decision Intelligence Assistant")
    st.caption("Ask strategic or operational questions in plain language. Answers are computed deterministically via in-memory DuckDB queries.")

    # Multi-table notification
    if len(sql_engine.tables) > 1:
        tbl_names = [f"`{t}`" for t in sql_engine.tables.keys() if t not in ("df", "data")]
        st.info(f"🔗 **Multi-Table Querying Active**: {len(tbl_names)} tables loaded into DuckDB ({', '.join(tbl_names)}). You can query the active table (`df`) or perform multi-table SQL joins across any table.")

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    domain_key = domain_info.get("domain_key", "general")
    starter_questions = DOMAIN_SAMPLE_QUESTIONS.get(domain_key, DOMAIN_SAMPLE_QUESTIONS["general"])

    st.markdown("##### Strategic Query Shortcuts:")
    
    # Display in 2 clean rows of buttons
    half = (len(starter_questions) + 1) // 2
    row1_cols = st.columns(half)
    row2_cols = st.columns(len(starter_questions) - half)

    selected_starter = None

    for i in range(half):
        with row1_cols[i]:
            sq = starter_questions[i]
            if st.button(sq, key=f"sq_btn_r1_{i}", use_container_width=True):
                selected_starter = sq

    for j in range(half, len(starter_questions)):
        with row2_cols[j - half]:
            sq = starter_questions[j]
            if st.button(sq, key=f"sq_btn_r2_{j}", use_container_width=True):
                selected_starter = sq

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Show verified SQL if available
            if msg.get("sql"):
                with st.expander("Audit: Verified SQL & Execution Telemetry", expanded=False):
                    st.code(msg["sql"], language="sql")
                    if msg.get("stats"):
                        stats = msg["stats"]
                        st.caption(f"Rows: {stats.get('row_count')} | Latency: {stats.get('execution_time_ms')} ms")

            # Show data table if available
            if msg.get("table") is not None and not msg["table"].empty:
                st.dataframe(msg["table"], use_container_width=True)

            # Show generated chart if available
            if msg.get("figure") is not None:
                st.plotly_chart(msg["figure"], use_container_width=True)

    # Chat Input
    user_prompt = st.chat_input("Ask any business question about your dataset...")
    active_question = user_prompt or selected_starter

    if active_question:
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": active_question})
        with st.chat_message("user"):
            st.markdown(active_question)

        # Process Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing dataset & executing verification query..."):
                schema_summary = sql_engine.get_schema_summary()
                sql_query = llm_client.query_to_sql(active_question, schema_summary)
                
                try:
                    result_df, stats = sql_engine.execute_query(sql_query)
                    
                    # Generate natural language explanation grounded in result_df
                    explanation = llm_client.explain_query_results(
                        active_question,
                        sql_query,
                        result_df
                    )

                    # Generate dynamic chart if suitable
                    chart_gen = ChartGenerator(df, column_types, domain_key)
                    fig = chart_gen.smart_chart_from_df(result_df, title=active_question)

                    # Render to UI
                    st.markdown(explanation)
                    
                    with st.expander("Audit: Verified SQL & Execution Telemetry", expanded=False):
                        st.code(sql_query, language="sql")
                        st.caption(f"Rows Returned: {stats['row_count']} | Query Latency: {stats['execution_time_ms']} ms")

                    if not result_df.empty:
                        st.dataframe(result_df, use_container_width=True)

                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                    # Save to chat history
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": explanation,
                        "sql": sql_query,
                        "stats": stats,
                        "table": result_df,
                        "figure": fig
                    })

                except SQLValidationError as ve:
                    err_msg = f"**Query Security Notice**: {str(ve)}\n\nPlease refine your request to a read-only analytical query."
                    st.error(err_msg)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": err_msg,
                        "sql": sql_query
                    })
                except Exception as e:
                    err_msg = f"Unable to complete query execution: {str(e)}"
                    st.error(err_msg)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": err_msg,
                        "sql": sql_query
                    })

    # Clear chat option
    if st.session_state.chat_messages:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Clear Conversation History"):
            st.session_state.chat_messages = []
            st.rerun()
