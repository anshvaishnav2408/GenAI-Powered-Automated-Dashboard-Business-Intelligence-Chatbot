"""
KPI Engine Module
Automatically selects, calculates, and formats business KPIs with period-over-period trend deltas.
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np


class KPIEngine:
    def __init__(self, df: pd.DataFrame, domain_key: str, column_types: Dict[str, str]):
        self.df = df
        self.domain_key = domain_key
        self.column_types = column_types
        self.date_col = self._find_primary_date_col()

    def _find_primary_date_col(self) -> Optional[str]:
        """Find the most suitable date/datetime column for trend analysis."""
        date_cols = [c for c, t in self.column_types.items() if t == "datetime"]
        if not date_cols:
            return None
        # Prefer columns with 'date', 'order', 'created' in name
        for c in date_cols:
            c_low = c.lower()
            if any(k in c_low for k in ["order", "sale", "trans", "created", "signup"]):
                return c
        return date_cols[0]

    def _find_column_by_keywords(self, keywords: List[str], require_numeric: bool = True) -> Optional[str]:
        """Find a column that matches any keyword in the list."""
        for col in self.df.columns:
            col_clean = col.lower().replace(" ", "_").replace("-", "_")
            if require_numeric and self.column_types.get(col) != "numeric":
                continue
            for kw in keywords:
                if kw == col_clean or kw in col_clean:
                    return col
        return None

    def _calculate_delta(self, metric_func, date_col: str) -> Optional[Tuple[float, str]]:
        """
        Calculate period-over-period percentage change by splitting timeline into prior and current periods.
        """
        if not date_col or date_col not in self.df.columns or self.df[date_col].isna().all():
            return None
        
        valid_df = self.df.dropna(subset=[date_col]).sort_values(by=date_col)
        if len(valid_df) < 4:
            return None

        # Split timeline into two halves
        mid_idx = len(valid_df) // 2
        prior_df = valid_df.iloc[:mid_idx]
        current_df = valid_df.iloc[mid_idx:]

        try:
            val_prior = metric_func(prior_df)
            val_curr = metric_func(current_df)
            if val_prior is None or val_curr is None or val_prior == 0:
                return None
            delta_pct = ((val_curr - val_prior) / abs(val_prior)) * 100.0
            sign = "+" if delta_pct >= 0 else ""
            return delta_pct, f"{sign}{delta_pct:.1f}% vs prior half"
        except Exception:
            return None

    def calculate_kpis(self) -> List[Dict[str, Any]]:
        """
        Calculate the top 4-6 KPIs according to domain and available columns.
        """
        kpis: List[Dict[str, Any]] = []

        if self.domain_key == "sales":
            kpis = self._sales_kpis()
        elif self.domain_key == "saas":
            kpis = self._saas_kpis()
        elif self.domain_key == "hr":
            kpis = self._hr_kpis()
        elif self.domain_key == "finance":
            kpis = self._finance_kpis()
        elif self.domain_key == "marketing":
            kpis = self._marketing_kpis()

        # If domain-specific KPIs couldn't find enough metrics, supplement with general KPIs
        if len(kpis) < 3:
            kpis.extend(self._general_kpis())

        # Deduplicate KPI labels
        seen = set()
        unique_kpis = []
        for k in kpis:
            if k["label"] not in seen:
                seen.add(k["label"])
                unique_kpis.append(k)

        return unique_kpis[:6]

    def _format_number(self, val: float, is_currency: bool = False, is_percent: bool = False) -> str:
        """Format number into human-readable compact notation ($1.2M, $45.2K, etc.)."""
        if pd.isna(val):
            return "N/A"
        prefix = "$" if is_currency else ""
        if is_percent:
            return f"{val:.1f}%"
        abs_v = abs(val)
        sign = "-" if val < 0 else ""
        if abs_v >= 1_000_000:
            return f"{sign}{prefix}{abs_v / 1_000_000:.2f}M"
        elif abs_v >= 1_000:
            return f"{sign}{prefix}{abs_v / 1_000:.1f}K"
        elif isinstance(val, int) or abs_v.is_integer():
            return f"{sign}{prefix}{int(abs_v):,}"
        else:
            return f"{sign}{prefix}{abs_v:.2f}"

    def _sales_kpis(self) -> List[Dict[str, Any]]:
        kpis = []
        rev_col = self._find_column_by_keywords(["sales", "revenue", "gross_sales", "amount"])
        profit_col = self._find_column_by_keywords(["profit", "net_profit", "earnings", "margin_val"])
        qty_col = self._find_column_by_keywords(["quantity", "qty", "units_sold", "volume"])
        order_col = self._find_column_by_keywords(["order_id", "transaction_id", "invoice_id"], require_numeric=False)

        if rev_col:
            total_rev = float(self.df[rev_col].sum())
            delta = self._calculate_delta(lambda d: float(d[rev_col].sum()), self.date_col)
            kpis.append({
                "label": "Total Revenue",
                "value": self._format_number(total_rev, is_currency=True),
                "raw_value": total_rev,
                "delta": delta[1] if delta else None,
                "delta_value": delta[0] if delta else None,
                "help": f"Calculated as sum of {rev_col}"
            })

        if profit_col:
            total_profit = float(self.df[profit_col].sum())
            delta = self._calculate_delta(lambda d: float(d[profit_col].sum()), self.date_col)
            kpis.append({
                "label": "Total Profit",
                "value": self._format_number(total_profit, is_currency=True),
                "raw_value": total_profit,
                "delta": delta[1] if delta else None,
                "delta_value": delta[0] if delta else None,
                "help": f"Calculated as sum of {profit_col}"
            })

        if rev_col and profit_col:
            total_rev = float(self.df[rev_col].sum())
            margin = (float(self.df[profit_col].sum()) / total_rev * 100.0) if total_rev > 0 else 0.0
            kpis.append({
                "label": "Profit Margin",
                "value": f"{margin:.1f}%",
                "raw_value": margin,
                "delta": None,
                "help": "Total Profit divided by Total Revenue"
            })

        # Total Orders / Transactions
        if order_col:
            total_orders = int(self.df[order_col].nunique())
            kpis.append({
                "label": "Total Orders",
                "value": f"{total_orders:,}",
                "raw_value": total_orders,
                "delta": None,
                "help": f"Unique count of {order_col}"
            })
            if rev_col and total_orders > 0:
                aov = self.df[rev_col].sum() / total_orders
                kpis.append({
                    "label": "Avg Order Value (AOV)",
                    "value": self._format_number(aov, is_currency=True),
                    "raw_value": aov,
                    "delta": None,
                    "help": "Revenue divided by Total Orders"
                })
        else:
            # Fallback to row count
            kpis.append({
                "label": "Total Transactions",
                "value": f"{len(self.df):,}",
                "raw_value": len(self.df),
                "delta": None,
                "help": "Total recorded transactions"
            })

        if qty_col:
            total_qty = float(self.df[qty_col].sum())
            kpis.append({
                "label": "Units Sold",
                "value": self._format_number(total_qty),
                "raw_value": total_qty,
                "delta": None,
                "help": f"Sum of {qty_col}"
            })

        return kpis

    def _saas_kpis(self) -> List[Dict[str, Any]]:
        kpis = []
        mrr_col = self._find_column_by_keywords(["monthly_charges", "mrr", "subscription_fee"])
        churn_col = self._find_column_by_keywords(["churn", "churned", "is_churn"], require_numeric=False)
        tenure_col = self._find_column_by_keywords(["tenure", "tenure_months", "months_active"])
        nps_col = self._find_column_by_keywords(["nps", "nps_score", "satisfaction_score"])

        if mrr_col:
            total_mrr = float(self.df[mrr_col].sum())
            delta = self._calculate_delta(lambda d: float(d[mrr_col].sum()), self.date_col)
            kpis.append({
                "label": "Total MRR",
                "value": self._format_number(total_mrr, is_currency=True),
                "raw_value": total_mrr,
                "delta": delta[1] if delta else None,
                "help": f"Monthly Recurring Revenue sum ({mrr_col})"
            })

        if churn_col:
            col_series = self.df[churn_col].astype(str).str.lower().str.strip()
            churn_count = (col_series.isin(["yes", "true", "1", "churned"])).sum()
            churn_rate = (churn_count / max(len(self.df), 1)) * 100.0
            kpis.append({
                "label": "Churn Rate",
                "value": f"{churn_rate:.1f}%",
                "raw_value": churn_rate,
                "delta": None,
                "help": f"Percentage of accounts churned ({churn_count}/{len(self.df)})"
            })

        kpis.append({
            "label": "Total Accounts",
            "value": f"{len(self.df):,}",
            "raw_value": len(self.df),
            "delta": None,
            "help": "Total customer subscriptions"
        })

        if tenure_col:
            avg_tenure = float(self.df[tenure_col].mean())
            kpis.append({
                "label": "Average Tenure",
                "value": f"{avg_tenure:.1f} mos",
                "raw_value": avg_tenure,
                "delta": None,
                "help": f"Average customer lifetime in months ({tenure_col})"
            })

        if nps_col:
            avg_nps = float(self.df[nps_col].mean())
            kpis.append({
                "label": "Avg NPS Score",
                "value": f"{avg_nps:.1f} / 10",
                "raw_value": avg_nps,
                "delta": None,
                "help": f"Average Net Promoter Score ({nps_col})"
            })

        return kpis

    def _hr_kpis(self) -> List[Dict[str, Any]]:
        kpis = []
        salary_col = self._find_column_by_keywords(["salary", "annual_salary", "monthly_income", "compensation"])
        attr_col = self._find_column_by_keywords(["attrition", "left_company", "resigned"], require_numeric=False)
        satisfaction_col = self._find_column_by_keywords(["satisfaction", "job_satisfaction", "engagement"])
        perf_col = self._find_column_by_keywords(["performance", "performance_rating", "rating"])
        overtime_col = self._find_column_by_keywords(["overtime", "over_time"], require_numeric=False)

        kpis.append({
            "label": "Total Headcount",
            "value": f"{len(self.df):,}",
            "raw_value": len(self.df),
            "delta": None,
            "help": "Total active and recorded employees"
        })

        if attr_col:
            col_series = self.df[attr_col].astype(str).str.lower().str.strip()
            attr_count = (col_series.isin(["yes", "true", "1", "left"])).sum()
            attr_rate = (attr_count / max(len(self.df), 1)) * 100.0
            kpis.append({
                "label": "Attrition Rate",
                "value": f"{attr_rate:.1f}%",
                "raw_value": attr_rate,
                "delta": None,
                "help": f"Percentage of employees who left ({attr_count}/{len(self.df)})"
            })

        if salary_col:
            avg_sal = float(self.df[salary_col].mean())
            kpis.append({
                "label": "Average Salary",
                "value": self._format_number(avg_sal, is_currency=True),
                "raw_value": avg_sal,
                "delta": None,
                "help": f"Mean compensation across workforce ({salary_col})"
            })

        if overtime_col:
            ot_series = self.df[overtime_col].astype(str).str.lower().str.strip()
            ot_count = (ot_series.isin(["yes", "true", "1"])).sum()
            ot_pct = (ot_count / max(len(self.df), 1)) * 100.0
            kpis.append({
                "label": "Overtime Rate",
                "value": f"{ot_pct:.1f}%",
                "raw_value": ot_pct,
                "delta": None,
                "help": "Percentage of employees working overtime"
            })

        if perf_col:
            avg_perf = float(self.df[perf_col].mean())
            kpis.append({
                "label": "Avg Performance",
                "value": f"{avg_perf:.2f}",
                "raw_value": avg_perf,
                "delta": None,
                "help": f"Mean employee performance score ({perf_col})"
            })

        if satisfaction_col:
            avg_sat = float(self.df[satisfaction_col].mean())
            kpis.append({
                "label": "Avg Satisfaction",
                "value": f"{avg_sat:.2f}",
                "raw_value": avg_sat,
                "delta": None,
                "help": f"Mean job satisfaction score ({satisfaction_col})"
            })

        return kpis

    def _finance_kpis(self) -> List[Dict[str, Any]]:
        kpis = []
        rev_col = self._find_column_by_keywords(["revenue", "gross_revenue", "income"])
        exp_col = self._find_column_by_keywords(["expense", "expenses", "cost", "operating_expense"])
        ebitda_col = self._find_column_by_keywords(["ebitda", "operating_income"])

        if rev_col:
            rev_val = float(self.df[rev_col].sum())
            kpis.append({
                "label": "Total Revenue",
                "value": self._format_number(rev_val, is_currency=True),
                "raw_value": rev_val,
                "delta": None,
                "help": f"Sum of {rev_col}"
            })
        if exp_col:
            exp_val = float(self.df[exp_col].sum())
            kpis.append({
                "label": "Total Expenses",
                "value": self._format_number(exp_val, is_currency=True),
                "raw_value": exp_val,
                "delta": None,
                "help": f"Sum of {exp_col}"
            })
        if rev_col and exp_col:
            net_income = float(self.df[rev_col].sum() - self.df[exp_col].sum())
            kpis.append({
                "label": "Net Income",
                "value": self._format_number(net_income, is_currency=True),
                "raw_value": net_income,
                "delta": None,
                "help": "Revenue minus Total Expenses"
            })
        if ebitda_col:
            ebitda_val = float(self.df[ebitda_col].sum())
            kpis.append({
                "label": "Total EBITDA",
                "value": self._format_number(ebitda_val, is_currency=True),
                "raw_value": ebitda_val,
                "delta": None,
                "help": f"Sum of {ebitda_col}"
            })
        return kpis

    def _marketing_kpis(self) -> List[Dict[str, Any]]:
        kpis = []
        spend_col = self._find_column_by_keywords(["spend", "ad_spend", "cost"])
        conv_col = self._find_column_by_keywords(["conversion", "conversions", "leads"])
        imp_col = self._find_column_by_keywords(["impressions", "views"])
        clicks_col = self._find_column_by_keywords(["clicks"])

        if spend_col:
            spend_val = float(self.df[spend_col].sum())
            kpis.append({
                "label": "Total Ad Spend",
                "value": self._format_number(spend_val, is_currency=True),
                "raw_value": spend_val,
                "delta": None,
                "help": f"Sum of {spend_col}"
            })
        if conv_col:
            conv_val = float(self.df[conv_col].sum())
            kpis.append({
                "label": "Total Conversions",
                "value": self._format_number(conv_val),
                "raw_value": conv_val,
                "delta": None,
                "help": f"Sum of {conv_col}"
            })
        if imp_col and clicks_col:
            tot_imp = self.df[imp_col].sum()
            tot_clicks = self.df[clicks_col].sum()
            ctr = (tot_clicks / max(tot_imp, 1)) * 100.0
            kpis.append({
                "label": "Average CTR",
                "value": f"{ctr:.2f}%",
                "raw_value": ctr,
                "delta": None,
                "help": "Total Clicks / Total Impressions"
            })
        return kpis

    def _general_kpis(self) -> List[Dict[str, Any]]:
        kpis = []
        kpis.append({
            "label": "Total Records",
            "value": f"{len(self.df):,}",
            "raw_value": len(self.df),
            "delta": None,
            "help": "Number of rows in the dataset"
        })

        # Top 3 numeric columns by variance or mean
        num_cols = [c for c, t in self.column_types.items() if t == "numeric"]
        for col in num_cols[:3]:
            series = self.df[col].dropna()
            if len(series) > 0:
                kpis.append({
                    "label": f"Total {col}",
                    "value": self._format_number(float(series.sum())),
                    "raw_value": float(series.sum()),
                    "delta": None,
                    "help": f"Sum of {col}"
                })
        return kpis
