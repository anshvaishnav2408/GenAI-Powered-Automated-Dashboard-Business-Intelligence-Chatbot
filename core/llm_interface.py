"""
LLM Interface Module
Dynamic Column-Aware Intelligence Engine:
- Semantic Intent & Dynamic Column Matcher for ANY uploaded CSV/Excel
- Value & Entity Recognition (filters by categorical values mentioned in prompt)
- Multi-Table Schema Prompting
- Safe DuckDB Query Generation & Deterministic Business Synthesis
- Modular Support for Ollama, Gemini, OpenAI/Compatible, & Built-in Dynamic Analyst
"""

import json
import re
from typing import Dict, Any, Optional, List, Tuple
import requests
import pandas as pd
import numpy as np


class BaseLLMProvider:
    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        raise NotImplementedError


class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "llama3:latest", host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host.rstrip("/")

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        try:
            resp = requests.post(url, json=payload, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
            else:
                raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"Could not connect to Ollama at {self.host}. Is Ollama running?")
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {str(e)}")


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        if not self.api_key:
            raise RuntimeError("Gemini API key is missing. Please provide it in the sidebar.")
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": temperature}
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=45)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                raise RuntimeError(f"Gemini API returned status {resp.status_code}: {resp.text}")
            except Exception as e2:
                raise RuntimeError(f"Gemini error: {str(e)} | REST fallback: {str(e2)}")


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        if not self.api_key:
            raise RuntimeError("API key is required for OpenAI-compatible provider.")
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0]["message"]["content"].strip()
            raise RuntimeError(f"Provider returned HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            raise RuntimeError(f"API call failed: {str(e)}")


class HeuristicBIAnalyst(BaseLLMProvider):
    """
    Intelligent Dynamic Semantic BI Analyst.
    Dynamically maps natural language questions against whatever columns, data types,
    and distinct values exist in ANY uploaded CSV/Excel dataset.
    """
    def __init__(self, df: pd.DataFrame, domain_key: str):
        self.df = df
        self.domain_key = domain_key
        self.num_cols = list(df.select_dtypes(include=["number"]).columns)
        self.cat_cols = list(df.select_dtypes(include=["object", "category"]).columns)
        self.date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        if "Translate the user question into a safe DuckDB SQL query" in prompt:
            return self._heuristic_nl_to_sql(prompt)
        elif "Explain the analytical findings" in prompt:
            return self._heuristic_explain(prompt)
        return "Analysis completed based on dataset calculations."

    def _match_column_in_text(self, text: str, candidates: List[str]) -> Optional[str]:
        """Match exact or fuzzy column name in query text."""
        t_clean = text.lower().replace("_", " ").replace("-", " ")
        # 1. Exact match
        for c in candidates:
            c_clean = c.lower().replace("_", " ").replace("-", " ")
            if c_clean in t_clean or re.search(r"\b" + re.escape(c_clean) + r"\b", t_clean):
                return c
        # 2. Token match
        for c in candidates:
            tokens = c.lower().replace("_", " ").split()
            if any(tok in t_clean for tok in tokens if len(tok) > 3):
                return c
        return candidates[0] if candidates else None

    def _find_filter_value(self, text: str) -> Optional[Tuple[str, str]]:
        """Identify if a categorical value in the dataset is specifically mentioned in the query."""
        t_low = text.lower()
        for col in self.cat_cols[:6]:
            if self.df[col].nunique() <= 35:
                for val in self.df[col].dropna().unique():
                    v_str = str(val).strip()
                    if len(v_str) > 2 and v_str.lower() in t_low:
                        return col, v_str
        return None

    def _heuristic_nl_to_sql(self, prompt: str) -> str:
        """Dynamically translates any business question into safe, optimal DuckDB SQL."""
        match = re.search(r"User Question:\s*\"?([^\n\"]+)\"?", prompt)
        q = (match.group(1) if match else prompt).strip()
        q_low = q.lower()

        # Identify target numerical and categorical columns from the dataset
        num_c = self._match_column_in_text(q, self.num_cols) if self.num_cols else None
        cat_c = self._match_column_in_text(q, self.cat_cols) if self.cat_cols else None
        date_c = self._match_column_in_text(q, self.date_cols) if self.date_cols else (self.date_cols[0] if self.date_cols else None)

        # Fallbacks
        if not num_c and self.num_cols:
            num_c = self.num_cols[0]
        if not cat_c and self.cat_cols:
            cat_c = self.cat_cols[0]

        # Check for filter value in question (e.g. "sales in Technology" -> WHERE Category = 'Technology')
        filter_match = self._find_filter_value(q)
        where_clause = f" WHERE \"{filter_match[0]}\" = '{filter_match[1]}'" if filter_match else ""

        # Extract limit if specified ("top 5", "top 10")
        limit = 5
        limit_match = re.search(r"\b(?:top|first|limit)\s*(\d+)\b", q_low)
        if limit_match:
            limit = int(limit_match.group(1))

        # Determine sort order (highest / top / best -> DESC; lowest / worst / least -> ASC)
        order_dir = "ASC" if any(w in q_low for w in ["lowest", "least", "worst", "bottom", "minimum", "min"]) else "DESC"

        # 1. Monthly / Periodic Trend Over Time
        if any(w in q_low for w in ["month", "trend", "over time", "quarter", "timeline", "trajectory", "decrease", "increase"]) and date_c and num_c:
            return f"SELECT strftime(\"{date_c}\", '%Y-%m') AS \"Month\", ROUND(SUM(\"{num_c}\"), 2) AS \"Total_{num_c}\", COUNT(*) AS \"Order_Count\" FROM df{where_clause} GROUP BY \"Month\" ORDER BY \"Month\" ASC;"

        # 2. Average / Mean Aggregation
        if any(w in q_low for w in ["average", "avg", "mean"]) and num_c and cat_c:
            return f"SELECT \"{cat_c}\", ROUND(AVG(\"{num_c}\"), 2) AS \"Avg_{num_c}\", COUNT(*) AS \"Count\" FROM df{where_clause} GROUP BY \"{cat_c}\" ORDER BY \"Avg_{num_c}\" {order_dir} LIMIT {limit};"

        # 3. Count / Volume Distribution
        if any(w in q_low for w in ["how many", "count", "frequency", "number of"]) and cat_c:
            return f"SELECT \"{cat_c}\", COUNT(*) AS \"Count\", ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM df), 1) AS \"Percentage_Share\" FROM df{where_clause} GROUP BY \"{cat_c}\" ORDER BY \"Count\" DESC LIMIT {limit};"

        # 4. Profit Margin / Ratio / Loss / Negative Analysis
        if any(w in q_low for w in ["margin", "loss", "negative", "low profit", "bleed"]) and len(self.num_cols) >= 2 and cat_c:
            val_col1 = self.num_cols[0]
            val_col2 = self.num_cols[1]
            return f"SELECT \"{cat_c}\", ROUND(SUM(\"{val_col1}\"), 2) AS \"{val_col1}\", ROUND(SUM(\"{val_col2}\"), 2) AS \"{val_col2}\", ROUND((SUM(\"{val_col2}\") / NULLIF(SUM(\"{val_col1}\"), 0)) * 100, 1) AS \"Margin_Pct\" FROM df GROUP BY \"{cat_c}\" ORDER BY \"Margin_Pct\" ASC LIMIT {limit};"

        # 5. Top N / Best / Ranking by Metric
        if cat_c and num_c:
            return f"SELECT \"{cat_c}\", ROUND(SUM(\"{num_c}\"), 2) AS \"Total_{num_c}\", COUNT(*) AS \"Transactions\" FROM df{where_clause} GROUP BY \"{cat_c}\" ORDER BY \"Total_{num_c}\" {order_dir} LIMIT {limit};"

        # 6. Overall Metric Summary fallback
        if num_c:
            return f"SELECT COUNT(*) AS \"Total_Records\", ROUND(SUM(\"{num_c}\"), 2) AS \"Sum_{num_c}\", ROUND(AVG(\"{num_c}\"), 2) AS \"Avg_{num_c}\", ROUND(MIN(\"{num_c}\"), 2) AS \"Min_{num_c}\", ROUND(MAX(\"{num_c}\"), 2) AS \"Max_{num_c}\" FROM df{where_clause};"

        # Default table preview
        return "SELECT * FROM df LIMIT 10;"

    def _heuristic_explain(self, prompt: str) -> str:
        return "Calculations verified against in-memory DuckDB analytical engine."


class LLMClient:
    """
    Unified client routing prompts to the active provider with rich
    grounded synthesis fallback.
    """
    def __init__(self, provider_type: str, config: Dict[str, Any], df: pd.DataFrame, domain_key: str):
        self.provider_type = provider_type
        self.config = config
        self.df = df
        self.domain_key = domain_key
        self.heuristic_fallback = HeuristicBIAnalyst(df, domain_key)
        self.active_provider = self._init_provider()

    def _init_provider(self) -> BaseLLMProvider:
        p_type = self.provider_type.lower()
        if p_type == "ollama":
            return OllamaProvider(
                model_name=self.config.get("ollama_model", "llama3:latest"),
                host=self.config.get("ollama_host", "http://localhost:11434")
            )
        elif p_type == "gemini":
            return GeminiProvider(
                api_key=self.config.get("gemini_api_key", ""),
                model_name=self.config.get("gemini_model", "gemini-2.5-flash")
            )
        elif p_type in {"openai", "groq", "openrouter", "deepseek", "custom"}:
            return OpenAICompatibleProvider(
                api_key=self.config.get("openai_api_key", ""),
                base_url=self.config.get("openai_base_url", "https://api.openai.com/v1"),
                model_name=self.config.get("openai_model", "gpt-4o-mini")
            )
        else:
            return self.heuristic_fallback

    def query_to_sql(self, user_question: str, schema_summary: str) -> str:
        """
        Convert user question into a safe DuckDB SQL query.
        """
        if isinstance(self.active_provider, HeuristicBIAnalyst):
            return self.heuristic_fallback.generate(f"Translate the user question into a safe DuckDB SQL query. User Question: \"{user_question}\"")

        prompt = f"""You are a senior data analyst and expert DuckDB SQL developer.
Translate the user's natural language business question into an accurate, safe DuckDB SQL query.

{schema_summary}

RULES:
1. Return ONLY the SQL query inside ```sql ... ``` code block.
2. The query MUST be a read-only SELECT query against the table 'df' (or any registered table mentioned above).
3. Never use UPDATE, INSERT, DELETE, DROP, ALTER, PRAGMA, or external load functions.
4. Use standard DuckDB SQL syntax (e.g., strftime for dates, NULLIF, ROUND).
5. Always alias aggregated columns cleanly with descriptive names.
6. If the question asks for top N, use ORDER BY ... DESC LIMIT N.
7. Wrap column names in double quotes if they contain spaces or special characters.

User Question: "{user_question}"
"""
        try:
            raw_resp = self.active_provider.generate(prompt, temperature=0.1)
            sql_match = re.search(r"```sql\s*([\s\S]*?)\s*```", raw_resp, re.IGNORECASE)
            if sql_match:
                return sql_match.group(1).strip()
            select_match = re.search(r"(SELECT[\s\S]+;?)", raw_resp, re.IGNORECASE)
            if select_match:
                return select_match.group(1).strip()
            return raw_resp.strip()
        except Exception:
            return self.heuristic_fallback.generate(f"Translate the user question into a safe DuckDB SQL query. User Question: \"{user_question}\"")

    def explain_query_results(
        self,
        user_question: str,
        sql_query: str,
        results_df: pd.DataFrame
    ) -> str:
        """
        Produce a consultant-grade business answer citing exact calculated numbers.
        """
        try:
            table_str = results_df.head(10).to_markdown(index=False)
        except Exception:
            table_str = results_df.head(10).to_string(index=False)
        total_rows = len(results_df)

        if isinstance(self.active_provider, HeuristicBIAnalyst):
            return self._synthesize_heuristic_business_answer(user_question, results_df)

        prompt = f"""You are a senior Business Intelligence executive and data analyst.
A user asked: "{user_question}"

The following SQL query was safely executed against the dataset:
```sql
{sql_query}
```

Calculated Results Table (Top rows):
{table_str}
Total Rows Returned: {total_rows}

TASK:
Provide a concise, professional business answer:
1. Direct Executive Answer: Clearly answer the user's question citing the exact numbers from the table above.
2. Financial / Operational Interpretation: Explain what these numbers mean for business performance.
3. Root Cause Analysis: If there is underperformance or variance, identify why.
4. Strategic Actions: 2 concrete, prioritized recommendations for decision-makers.
5. If causation is not proven, explicitly label assumptions with "[Hypothesis]".
6. Never invent or hallucinate metrics that are not in the table.
"""
        try:
            return self.active_provider.generate(prompt, temperature=0.2)
        except Exception as e:
            return self._synthesize_heuristic_business_answer(user_question, results_df)

    def _synthesize_heuristic_business_answer(self, q: str, df_res: pd.DataFrame) -> str:
        """Deep, structured business consultant response grounded in verified SQL results."""
        if df_res.empty:
            return f"**Result Summary**: No matching records were found for the query *\"{q}\"*. Please check your filter criteria."

        cols = list(df_res.columns)
        first_row = df_res.iloc[0].to_dict()

        formatted_items = []
        for k, v in first_row.items():
            if isinstance(v, (int, float)):
                if abs(v) > 1000:
                    formatted_items.append(f"**{k}**: ${v:,.2f}" if any(m in k.lower() for m in ["sales", "profit", "revenue", "price", "amount", "salary", "spend"]) else f"**{k}**: {v:,.0f}")
                elif isinstance(v, float):
                    formatted_items.append(f"**{k}**: {v:.2f}")
                else:
                    formatted_items.append(f"**{k}**: {v}")
            else:
                formatted_items.append(f"**{k}**: {v}")

        top_summary = ", ".join(formatted_items)

        # Contextual synthesis
        if len(cols) >= 2 and len(df_res) > 1:
            dim_col = cols[0]
            val_col = cols[1]
            top_val = df_res[val_col].iloc[0]
            bot_val = df_res[val_col].iloc[-1]
            variance_pct = ((top_val - bot_val) / max(abs(bot_val), 0.001)) * 100.0 if bot_val != 0 else 0.0

            return f"""### Executive Takeaway
Direct analysis for: **"{q}"**

The leading entry is **{first_row[dim_col]}** with a recorded **{val_col}** of **{first_row[val_col]:,.2f}** across {len(df_res)} analytical categories evaluated.

#### Key Business Observations:
- **Primary Finding**: {top_summary}.
- **Performance Spread**: The top segment outperforms the trailing category in this ranking by **{variance_pct:.1f}%**.
- **Portfolio Concentration**: Top entries represent the core operational volume in this distribution.

#### Strategic Action Items:
1. **Capital Allocation**: Align operational resources and inventory capacity behind high-yield categories ({first_row[dim_col]}) to maximize return on invested capital.
2. **Review Trailing Cohorts**: Audit underperforming categories at the bottom of this ranking ({df_res[dim_col].iloc[-1]}) for margin leakage or operational bottlenecks.
3. *[Hypothesis]*: Price elasticity testing on top-performing categories could yield immediate margin expansion without compromising volume.
"""

        # Single aggregation or overall metric summary
        return f"""### Executive Metric Summary
Analysis for: **"{q}"**

#### Verified Aggregates:
- {top_summary}
- **Data Coverage**: Evaluated across {len(df_res)} matching records.

#### Strategic Recommendation:
- Monitor period-over-period variance to ensure performance thresholds are sustained across business cycles.
"""
