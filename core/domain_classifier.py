"""
Domain Classifier Module
Automatically identifies business domain (Sales, SaaS, HR, Finance, Marketing, Inventory, CRM, General)
from dataset schema and contents.
"""

from typing import Dict, List, Any
import pandas as pd


DOMAIN_DEFINITIONS = {
    "sales": {
        "title": "Sales & Retail Commerce",
        "keywords": [
            "sale", "sales", "revenue", "profit", "margin", "discount", "order", "orders",
            "quantity", "customer", "product", "shipping", "price", "sub_category", "category",
            "store", "transaction", "unit_price", "retail", "merchant", "gross_sales"
        ],
        "default_kpis": ["Total Revenue", "Total Profit", "Profit Margin (%)", "Total Orders", "Average Order Value (AOV)", "Units Sold"]
    },
    "saas": {
        "title": "SaaS & Subscription Analytics",
        "keywords": [
            "mrr", "arr", "churn", "subscription", "tenure", "plan", "tier", "nps", "active_users",
            "contract", "monthly_charges", "total_charges", "seats", "license", "renewal", "arpu"
        ],
        "default_kpis": ["Total MRR", "Churn Rate (%)", "Average Tenure", "Avg NPS Score", "Active Accounts", "Avg Monthly Revenue"]
    },
    "hr": {
        "title": "Human Resources & Workforce",
        "keywords": [
            "employee", "attrition", "salary", "department", "job_role", "performance", "overtime",
            "satisfaction", "years_at_company", "hire_date", "termination", "headcount", "compensation"
        ],
        "default_kpis": ["Total Headcount", "Attrition Rate (%)", "Average Salary", "Overtime Percentage", "Avg Job Satisfaction", "Avg Performance Rating"]
    },
    "marketing": {
        "title": "Marketing & Growth",
        "keywords": [
            "campaign", "impressions", "clicks", "ctr", "cpc", "conversion", "spend", "ad_spend",
            "cpa", "leads", "channel", "traffic", "roas", "bounce_rate", "source"
        ],
        "default_kpis": ["Total Ad Spend", "Total Conversions", "Average CTR (%)", "Cost Per Click (CPC)", "Total Leads", "ROAS"]
    },
    "finance": {
        "title": "Corporate Finance & Accounting",
        "keywords": [
            "revenue", "expense", "expenses", "ebitda", "asset", "liability", "debt", "cash",
            "budget", "equity", "tax", "operating_income", "balance", "cost", "capex", "opex"
        ],
        "default_kpis": ["Gross Revenue", "Total Expenses", "Net Income", "Operating Margin (%)", "EBITDA", "Cash Flow"]
    },
    "inventory": {
        "title": "Inventory & Supply Chain",
        "keywords": [
            "inventory", "stock", "warehouse", "reorder", "supplier", "lead_time", "sku",
            "quantity_on_hand", "restock", "carrying_cost", "safety_stock"
        ],
        "default_kpis": ["Total Inventory Units", "Total Stock Value", "Low Stock Items", "Avg Lead Time", "Reorder Rate", "Active SKUs"]
    }
}


def classify_domain(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Classify the domain of the dataset by inspecting column names and values.
    
    Returns:
        Dict with domain, domain_key, confidence, rationale, and suggested_kpis.
    """
    cols_clean = [col.lower().replace(" ", "_").replace("-", "_") for col in df.columns]
    
    scores: Dict[str, float] = {k: 0.0 for k in DOMAIN_DEFINITIONS}
    matched_keywords: Dict[str, List[str]] = {k: [] for k in DOMAIN_DEFINITIONS}

    for col in cols_clean:
        for domain, defs in DOMAIN_DEFINITIONS.items():
            for kw in defs["keywords"]:
                if kw in col:
                    # Give higher weight to exact or prefix matches
                    weight = 2.0 if (col == kw or col.startswith(kw + "_") or col.endswith("_" + kw)) else 1.0
                    scores[domain] += weight
                    matched_keywords[domain].append(f"column: {col} (matched '{kw}')")

    # Also check string columns for specific keywords (e.g. Churn 'Yes'/'No', Attrition 'Yes'/'No')
    for col in df.select_dtypes(include=["object"]).columns:
        col_lower = col.lower()
        if "churn" in col_lower:
            scores["saas"] += 3.0
        if "attrition" in col_lower:
            scores["hr"] += 3.0

    sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_domain_key, top_score = sorted_domains[0]

    # If the top score is very low, classify as general
    if top_score < 2.0:
        return {
            "domain_key": "general",
            "domain_title": "General Business Analytics",
            "confidence": 0.50,
            "rationale": ["Generic tabular dataset without strong domain-specific column naming signals."],
            "suggested_kpis": ["Total Records", "Numerical Averages", "Unique Categorical Counts", "Aggregated Sums"]
        }

    total_score = sum(scores.values())
    confidence = round(min(0.98, (top_score / max(total_score, 1)) * 1.1), 2)
    
    domain_info = DOMAIN_DEFINITIONS[best_domain_key]
    
    return {
        "domain_key": best_domain_key,
        "domain_title": domain_info["title"],
        "confidence": confidence,
        "rationale": matched_keywords[best_domain_key][:6],
        "suggested_kpis": domain_info["default_kpis"]
    }
