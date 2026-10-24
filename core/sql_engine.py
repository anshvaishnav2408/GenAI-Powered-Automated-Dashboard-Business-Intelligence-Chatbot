"""
Safe DuckDB SQL Engine Module
Provides an in-memory analytical SQL environment supporting single and multi-table queries,
cross-table joins, schema inspection, and strict read-only AST/keyword guardrails.
"""

import re
import time
from typing import Dict, Any, Tuple, Optional, Union
import duckdb
import pandas as pd


FORBIDDEN_KEYWORDS = [
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", r"\bALTER\b",
    r"\bTRUNCATE\b", r"\bCREATE\b", r"\bREPLACE\b", r"\bATTACH\b", r"\bDETACH\b",
    r"\bCOPY\b", r"\bEXPORT\b", r"\bIMPORT\b", r"\bPRAGMA\b", r"\bINSTALL\b",
    r"\bLOAD\b", r"\bEXEC\b", r"\bEXECUTE\b", r"\bSYSTEM\b", r"\bSHELL\b",
    r"\bREAD_CSV\b", r"\bREAD_PARQUET\b", r"\bHTTPFS\b", r"\bWRITE\b",
    r"\bINTO\s+OUTFILE\b", r"\bCALL\b"
]


class SQLValidationError(Exception):
    """Raised when an analytical query violates safety guardrails."""
    pass


class SafeSQLEngine:
    def __init__(self, data_source: Union[pd.DataFrame, Dict[str, pd.DataFrame]], active_key: Optional[str] = None):
        """
        Initialize DuckDB in-memory engine with single or multiple tables.
        
        Args:
            data_source: Either a single pd.DataFrame or a dict of {table_name: pd.DataFrame}.
            active_key: Name of the primary table if multiple tables are passed.
        """
        self.con = duckdb.connect(database=":memory:", read_only=False)
        self.tables: Dict[str, pd.DataFrame] = {}

        if isinstance(data_source, pd.DataFrame):
            self.primary_df = data_source
            self.tables["df"] = data_source
            self.con.register("df", data_source)
            self.con.register("data", data_source)
        elif isinstance(data_source, dict):
            self.tables = data_source
            # Select active table
            primary_name = active_key if (active_key and active_key in data_source) else list(data_source.keys())[0]
            self.primary_df = data_source[primary_name]
            
            # Register default aliases
            self.con.register("df", self.primary_df)
            self.con.register("data", self.primary_df)

            # Register all individual tables by name
            for t_name, t_df in data_source.items():
                sanitized_name = re.sub(r"[^a-zA-Z0-9_]", "_", t_name).lower()
                self.con.register(sanitized_name, t_df)
        else:
            raise SQLValidationError("Invalid data source provided to SafeSQLEngine.")

    def validate_query(self, query: str) -> str:
        """
        Validate that the query is strictly a read-only SELECT or WITH statement.
        """
        cleaned = query.strip().rstrip(";")
        if not cleaned:
            raise SQLValidationError("The query is empty.")

        # Check for multiple queries
        if ";" in cleaned:
            parts = [p.strip() for p in cleaned.split(";") if p.strip()]
            if len(parts) > 1:
                raise SQLValidationError("Multiple SQL statements in a single execution are prohibited for security.")
            cleaned = parts[0]

        # Ensure query begins with SELECT or WITH
        upper_query = cleaned.upper()
        if not (upper_query.startswith("SELECT") or upper_query.startswith("WITH")):
            raise SQLValidationError("Only read-only analytical queries starting with 'SELECT' or 'WITH' are permitted.")

        # Check against forbidden tokens
        for pattern in FORBIDDEN_KEYWORDS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                match = re.search(pattern, cleaned, re.IGNORECASE).group(0)
                raise SQLValidationError(f"Query rejected: Forbidden keyword or action '{match}' detected.")

        return cleaned

    def execute_query(self, query: str, max_rows: int = 1000) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Safely execute an analytical SQL query against registered tables.
        """
        valid_query = self.validate_query(query)
        start_time = time.time()
        
        try:
            rel = self.con.execute(valid_query)
            result_df = rel.df()
            elapsed_ms = (time.time() - start_time) * 1000.0

            stats = {
                "row_count": len(result_df),
                "col_count": len(result_df.columns),
                "execution_time_ms": round(elapsed_ms, 2),
                "query": valid_query,
                "is_truncated": len(result_df) > max_rows
            }

            if len(result_df) > max_rows:
                result_df = result_df.head(max_rows)

            return result_df, stats
        except Exception as e:
            raise SQLValidationError(f"SQL execution error: {str(e)}")

    def get_schema_summary(self) -> str:
        """
        Generate schema description across all registered tables for LLM/analyst prompting.
        """
        lines = []
        lines.append("AVAILABLE TABLES IN DATABASE:")

        for t_name, table_df in self.tables.items():
            lines.append(f"\nTable Name: '{t_name}' (Total Rows: {len(table_df):,})")
            lines.append("Columns:")
            for col in table_df.columns:
                dtype = str(table_df[col].dtype)
                sample_vals = table_df[col].dropna().head(3).tolist()
                sample_str = ", ".join([repr(v) for v in sample_vals])
                
                extra = ""
                if pd.api.types.is_numeric_dtype(table_df[col]):
                    min_v = table_df[col].min()
                    max_v = table_df[col].max()
                    extra = f" (min: {min_v}, max: {max_v})"
                elif table_df[col].nunique() <= 8:
                    uniques = table_df[col].dropna().unique().tolist()
                    extra = f" (allowed: {uniques})"

                lines.append(f"  - \"{col}\" ({dtype}){extra}: sample values [{sample_str}]")

        lines.append("\nNote: 'df' and 'data' are aliases for the currently active primary table.")
        return "\n".join(lines)
