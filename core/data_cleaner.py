"""
Data Cleaner and Profiler Module
Enterprise-grade data sanitization for messy real-world CSVs and Excels:
- Accounting currency format parsing: ($1,234.50) -> -1234.50
- Dirty null strings: 'n/a', '-', 'null', 'none', '?', 'missing' -> np.nan
- Mixed-format datetime parsing
- Column header normalization
- Outlier detection (IQR & Z-Score)
- Safe, auditable imputation and deduplication
"""

import re
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd


DIRTY_NULL_STRINGS = {
    "na", "n/a", "null", "none", "nan", "-", "--", "missing", "?", "nil",
    "unknown", "n.a.", "#n/a", "#na", "undefined", "empty", "blank", "none."
}


class DataCleaner:
    def __init__(self, df: pd.DataFrame):
        self.original_df = df.copy()
        self.df = df.copy()
        self.audit_log: List[Dict[str, str]] = []
        self.column_types: Dict[str, str] = {}
        self.outlier_info: Dict[str, Dict[str, Any]] = {}
        self.quality_report: Dict[str, Any] = {}

    def log_change(self, category: str, column: str, description: str, impact: str = "Informational"):
        """Record an explicit transformation in the compliance audit log."""
        self.audit_log.append({
            "category": category,
            "column": column,
            "description": description,
            "impact": impact
        })

    def clean_messy_structures(self) -> pd.DataFrame:
        """
        Pre-process raw dirty data:
        1. Clean column headers (remove newlines, excessive whitespace).
        2. Standardize dirty null representations ('N/A', '-', 'None') to real NaNs.
        3. Strip trailing and leading whitespace across all text columns.
        """
        # 1. Column header normalization
        new_cols = []
        cols_changed = 0
        for col in self.df.columns:
            clean_c = re.sub(r"[\r\n\t]+", " ", str(col)).strip()
            clean_c = re.sub(r"\s+", " ", clean_c)
            if clean_c != str(col):
                cols_changed += 1
            new_cols.append(clean_c)
        self.df.columns = new_cols
        if cols_changed > 0:
            self.log_change(
                "Header Normalization",
                "Headers",
                f"Sanitized whitespace and control characters across {cols_changed} column headers.",
                "Structure"
            )

        # 2. Clean dirty null strings and trim strings
        nulls_cleaned_total = 0
        for col in self.df.columns:
            if self.df[col].dtype == "object":
                # Strip string whitespace
                s_trimmed = self.df[col].astype(str).str.strip()
                # Check for dirty null tokens
                mask_null = s_trimmed.str.lower().isin(DIRTY_NULL_STRINGS)
                null_count = int(mask_null.sum())
                if null_count > 0:
                    nulls_cleaned_total += null_count
                    self.df.loc[mask_null, col] = np.nan
                # Restore actual string values with trimmed whitespace
                self.df[col] = self.df[col].apply(lambda x: str(x).strip() if pd.notna(x) and not (isinstance(x, str) and x.strip().lower() in DIRTY_NULL_STRINGS) else np.nan)

        if nulls_cleaned_total > 0:
            self.log_change(
                "Null Standardization",
                "Multiple",
                f"Standardized {nulls_cleaned_total} dirty text representations of missing data ('N/A', '-', 'None') to system nulls.",
                "Data Integrity"
            )

        return self.df

    def infer_and_convert_types(self) -> pd.DataFrame:
        """
        Intelligently infer and cast column types:
        - Date/datetime detection with mixed format support
        - Accounting parenthesis negative numbers: ($500.00) -> -500.00
        - Clean currency / percentage strings to numeric
        - Categorical vs identifier vs text classification
        """
        for col in self.df.columns:
            series = self.df[col]
            clean_col_name = col.lower().replace("_", "").replace(" ", "")

            # 1. Skip if already datetime
            if pd.api.types.is_datetime64_any_dtype(series):
                self.column_types[col] = "datetime"
                continue

            # 2. Skip if already boolean
            if pd.api.types.is_bool_dtype(series):
                self.column_types[col] = "boolean"
                continue

            # 3. Numeric check
            if pd.api.types.is_numeric_dtype(series):
                non_na = series.dropna()
                if set(non_na.unique()).issubset({0, 1}) and len(non_na.unique()) <= 2:
                    self.column_types[col] = "boolean"
                else:
                    self.column_types[col] = "numeric"
                continue

            # 4. If string/object, attempt conversions
            if series.dtype == "object":
                non_na = series.dropna().astype(str).str.strip()
                if len(non_na) == 0:
                    self.column_types[col] = "empty"
                    continue

                sample = non_na.head(50)

                # Check if it's a date/time column
                is_date_candidate = any(k in clean_col_name for k in ["date", "time", "year", "month", "day", "created", "timestamp", "signup", "hire"])
                if is_date_candidate or self._looks_like_date(sample):
                    try:
                        converted = pd.to_datetime(series, errors="coerce", format="mixed")
                        valid_count = converted.notna().sum()
                        if valid_count > 0 and (valid_count / len(non_na)) >= 0.65:
                            self.df[col] = converted
                            self.column_types[col] = "datetime"
                            self.log_change(
                                "Type Conversion",
                                col,
                                f"Parsed '{col}' as datetime ({valid_count}/{len(non_na)} valid dates parsed via mixed-format engine).",
                                "Enhancement"
                            )
                            continue
                    except Exception:
                        pass

                # Try numeric conversion (handle currency, percentage, accounting parentheses)
                if self._looks_like_currency_or_number(sample):
                    try:
                        cleaned_str = non_na.apply(self._clean_number_string)
                        num_series = pd.to_numeric(cleaned_str, errors="coerce")
                        valid_num_count = num_series.notna().sum()
                        if valid_num_count > 0 and (valid_num_count / len(non_na)) >= 0.75:
                            # Apply to full column
                            full_cleaned = series.astype(str).apply(self._clean_number_string)
                            self.df[col] = pd.to_numeric(full_cleaned, errors="coerce")
                            self.column_types[col] = "numeric"
                            self.log_change(
                                "Type Conversion",
                                col,
                                f"Stripped currency, accounting parentheses, and percentage formatting; cast '{col}' to numeric.",
                                "Enhancement"
                            )
                            continue
                    except Exception:
                        pass

                # Check cardinality for Categorical vs Identifier vs Text
                unique_count = non_na.nunique()
                total_count = len(non_na)
                ratio = unique_count / max(total_count, 1)

                if any(k in clean_col_name for k in ["id", "code", "key", "uuid", "hash"]) and ratio > 0.5:
                    self.column_types[col] = "identifier"
                elif unique_count <= 60 or ratio < 0.25:
                    self.column_types[col] = "categorical"
                else:
                    self.column_types[col] = "text"

        return self.df

    def _clean_number_string(self, val: Any) -> str:
        """Parse currency, commas, and accounting parenthesis negatives: (1,200) -> -1200."""
        if pd.isna(val):
            return ""
        s = str(val).strip()
        # Accounting negative: ($1,234.50) or (1234.50)
        if s.startswith("(") and s.endswith(")"):
            s = "-" + s[1:-1]
        # Remove currency symbols and formatting
        s = re.sub(r"[\$,€,£,¥,₹]", "", s)
        s = s.replace("%", "").replace(",", "").strip()
        return s

    def _looks_like_date(self, sample_series: pd.Series) -> bool:
        """Check if sample strings look like date strings."""
        if len(sample_series) == 0:
            return False
        date_pattern = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}|^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|^[A-Za-z]{3,9}\s+\d{1,2},\s*\d{4}")
        matches = sum(bool(date_pattern.search(str(val).strip())) for val in sample_series)
        return (matches / len(sample_series)) >= 0.55

    def _looks_like_currency_or_number(self, sample_series: pd.Series) -> bool:
        """Check if sample strings look like formatted numbers/currency/percentages."""
        if len(sample_series) == 0:
            return False
        matches = 0
        for val in sample_series:
            cleaned = self._clean_number_string(val)
            if not cleaned:
                continue
            try:
                float(cleaned)
                matches += 1
            except ValueError:
                pass
        return (matches / len(sample_series)) >= 0.50

    def detect_outliers(self) -> Dict[str, Dict[str, Any]]:
        """
        Detect outliers in numerical columns using IQR and Z-Score methods.
        Does NOT remove them; records thresholds and counts.
        """
        numeric_cols = [c for c, t in self.column_types.items() if t == "numeric"]
        outlier_data = {}

        for col in numeric_cols:
            series = self.df[col].dropna()
            if len(series) < 10:
                continue

            q25 = series.quantile(0.25)
            q75 = series.quantile(0.75)
            iqr = q75 - q25
            lower_bound = q25 - (1.5 * iqr)
            upper_bound = q75 + (1.5 * iqr)

            iqr_outliers = series[(series < lower_bound) | (series > upper_bound)]
            
            # Z-Score
            mean = series.mean()
            std = series.std()
            z_outliers_count = 0
            if std > 0:
                z_scores = np.abs((series - mean) / std)
                z_outliers_count = int((z_scores > 3).sum())

            outlier_data[col] = {
                "q25": round(float(q25), 3),
                "q75": round(float(q75), 3),
                "iqr": round(float(iqr), 3),
                "lower_bound": round(float(lower_bound), 3),
                "upper_bound": round(float(upper_bound), 3),
                "outlier_count_iqr": int(len(iqr_outliers)),
                "outlier_pct_iqr": round(float(len(iqr_outliers) / len(series) * 100), 2),
                "outlier_count_zscore": z_outliers_count
            }

            if len(iqr_outliers) > 0:
                self.log_change(
                    "Outlier Detection",
                    col,
                    f"Identified {len(iqr_outliers)} potential outliers ({outlier_data[col]['outlier_pct_iqr']}%) outside [{lower_bound:.2f}, {upper_bound:.2f}].",
                    "Informational"
                )

        self.outlier_info = outlier_data
        return outlier_data

    def handle_missing_values(self, strategy: str = "smart_impute") -> pd.DataFrame:
        """
        Safely handle missing values with clear audit logging.
        """
        total_rows = len(self.df)
        empty_rows = self.df.isna().all(axis=1).sum()
        if empty_rows > 0:
            self.df = self.df.dropna(how="all").reset_index(drop=True)
            self.log_change("Row Cleaning", "All", f"Removed {empty_rows} rows that were completely empty.", "Data Integrity")

        for col in self.df.columns:
            missing_count = self.df[col].isna().sum()
            if missing_count == 0:
                continue

            pct = (missing_count / total_rows) * 100
            col_type = self.column_types.get(col, "unknown")

            if strategy == "smart_impute":
                if col_type == "numeric":
                    skew = self.df[col].skew()
                    if abs(skew) > 1.0:
                        fill_val = self.df[col].median()
                        fill_desc = f"median ({fill_val:.2f})"
                    else:
                        fill_val = self.df[col].mean()
                        fill_desc = f"mean ({fill_val:.2f})"
                    self.df[col] = self.df[col].fillna(fill_val)
                    self.log_change(
                        "Imputation",
                        col,
                        f"Imputed {missing_count} missing values ({pct:.1f}%) using {fill_desc}.",
                        "Safe Fill"
                    )
                elif col_type in {"categorical", "text"}:
                    modes = self.df[col].mode()
                    fill_val = modes[0] if not modes.empty else "Unknown"
                    self.df[col] = self.df[col].fillna(fill_val)
                    self.log_change(
                        "Imputation",
                        col,
                        f"Imputed {missing_count} missing values ({pct:.1f}%) using mode ('{fill_val}').",
                        "Safe Fill"
                    )
                elif col_type == "datetime":
                    self.df[col] = self.df[col].ffill().bfill()
                    self.log_change(
                        "Imputation",
                        col,
                        f"Interpolated/Forward-filled {missing_count} missing dates ({pct:.1f}%).",
                        "Safe Fill"
                    )
            else:
                self.log_change(
                    "Missing Values",
                    col,
                    f"Retained {missing_count} missing values ({pct:.1f}%) per user settings.",
                    "Preserved"
                )

        return self.df

    def remove_duplicates(self, keep: str = "first") -> pd.DataFrame:
        """Safely remove exact duplicate records and log the count."""
        dup_count = int(self.df.duplicated().sum())
        if dup_count > 0:
            self.df = self.df.drop_duplicates(keep=keep).reset_index(drop=True)
            self.log_change(
                "Deduplication",
                "Entire Row",
                f"Removed {dup_count} exact duplicate rows (kept {keep} occurrence).",
                "Data Integrity"
            )
        else:
            self.log_change("Deduplication", "Entire Row", "No duplicate records found.", "Verified Clean")
        return self.df

    def compute_data_quality_report(self) -> Dict[str, Any]:
        """
        Compute an objective data quality score (0-100) and comprehensive health metrics.
        """
        total_cells = self.df.shape[0] * self.df.shape[1]
        missing_cells = int(self.original_df.isna().sum().sum())
        total_rows = len(self.original_df)
        duplicate_rows = int(self.original_df.duplicated().sum())

        completeness_pct = 100.0 * (1.0 - (missing_cells / max(total_cells, 1)))
        uniqueness_pct = 100.0 * (1.0 - (duplicate_rows / max(total_rows, 1)))
        
        total_num_points = sum(len(self.df[c].dropna()) for c, t in self.column_types.items() if t == "numeric")
        total_outliers = sum(info["outlier_count_iqr"] for info in self.outlier_info.values())
        outlier_health_pct = 100.0 * (1.0 - (total_outliers / max(total_num_points, 1)))

        score = (0.50 * completeness_pct) + (0.35 * uniqueness_pct) + (0.15 * outlier_health_pct)
        score = round(max(0.0, min(100.0, score)), 1)

        col_health = []
        for col in self.original_df.columns:
            clean_c = col.strip()
            # Find in self.df
            target_series = self.original_df[col]
            m_count = int(target_series.isna().sum())
            u_count = int(target_series.nunique())
            col_health.append({
                "Column": clean_c,
                "Inferred Type": self.column_types.get(clean_c, self.column_types.get(col, "unknown")),
                "Missing Values": m_count,
                "Missing %": round((m_count / total_rows) * 100, 2),
                "Unique Values": u_count,
                "Outliers (IQR)": self.outlier_info.get(clean_c, {}).get("outlier_count_iqr", 0)
            })

        self.quality_report = {
            "overall_score": score,
            "completeness_pct": round(completeness_pct, 1),
            "uniqueness_pct": round(uniqueness_pct, 1),
            "outlier_health_pct": round(outlier_health_pct, 1),
            "total_rows": total_rows,
            "total_cols": len(self.df.columns),
            "missing_cells": missing_cells,
            "duplicate_rows": duplicate_rows,
            "total_outliers": total_outliers,
            "column_health": col_health
        }
        return self.quality_report

    def clean_pipeline(self, impute: bool = True, deduplicate: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Execute end-to-end cleaning pipeline safely."""
        self.clean_messy_structures()
        self.infer_and_convert_types()
        self.detect_outliers()
        if deduplicate:
            self.remove_duplicates()
        if impute:
            self.handle_missing_values(strategy="smart_impute")
        else:
            self.handle_missing_values(strategy="keep")
        self.compute_data_quality_report()
        return self.df, {
            "audit_log": self.audit_log,
            "column_types": self.column_types,
            "outlier_info": self.outlier_info,
            "quality_report": self.quality_report
        }
