import os
import pandas as pd
import numpy as np

np.random.seed(42)

# 1. Retail Sales Dataset
n_retail = 1200
dates = pd.date_range(start="2025-01-01", end="2025-12-31", periods=n_retail)
categories = {
    "Technology": ["Laptops", "Smartphones", "Accessories", "Printers"],
    "Furniture": ["Chairs", "Desks", "Bookcases", "Tables"],
    "Office Supplies": ["Paper", "Binders", "Storage", "Appliances", "Art"]
}
regions = ["North America", "Europe", "Asia-Pacific", "Latin America"]
segments = ["Consumer", "Corporate", "Small Business"]

retail_data = []
for i in range(n_retail):
    order_id = f"ORD-{20250000 + i}"
    cust_id = f"CUST-{np.random.randint(1000, 1300)}"
    date = dates[i].strftime("%Y-%m-%d")
    region = np.random.choice(regions, p=[0.4, 0.3, 0.2, 0.1])
    segment = np.random.choice(segments, p=[0.5, 0.3, 0.2])
    cat = np.random.choice(list(categories.keys()), p=[0.4, 0.35, 0.25])
    sub_cat = np.random.choice(categories[cat])
    
    qty = np.random.randint(1, 9)
    if cat == "Technology":
        base_price = np.random.uniform(150, 1200)
        margin_pct = np.random.uniform(0.15, 0.35)
    elif cat == "Furniture":
        base_price = np.random.uniform(80, 600)
        margin_pct = np.random.uniform(0.05, 0.25)
    else:
        base_price = np.random.uniform(15, 120)
        margin_pct = np.random.uniform(0.20, 0.45)
        
    discount = np.random.choice([0.0, 0.05, 0.1, 0.15, 0.2, 0.3], p=[0.4, 0.2, 0.15, 0.1, 0.1, 0.05])
    sales = round(base_price * qty * (1 - discount), 2)
    # Some items sold at steep discount have negative profit
    cost = round(base_price * qty * (1 - margin_pct), 2)
    profit = round(sales - cost, 2)
    shipping_cost = round(np.random.uniform(5, 45), 2)
    
    retail_data.append({
        "Order_ID": order_id,
        "Order_Date": date,
        "Customer_ID": cust_id,
        "Customer_Segment": segment,
        "Region": region,
        "Category": cat,
        "Sub_Category": sub_cat,
        "Product_Name": f"{sub_cat} Pro #{np.random.randint(10, 99)}",
        "Sales": sales,
        "Quantity": qty,
        "Discount": discount,
        "Profit": profit,
        "Shipping_Cost": shipping_cost
    })

df_retail = pd.DataFrame(retail_data)
# Introduce a few realistic missing values and a couple duplicates to test cleaning
df_retail.loc[10:12, "Customer_Segment"] = np.nan
df_retail.loc[25:26, "Discount"] = np.nan
df_retail.to_csv("sample_data/retail_sales_bi.csv", index=False)
print("Saved sample_data/retail_sales_bi.csv with shape:", df_retail.shape)

# 2. SaaS Churn Dataset
n_saas = 800
saas_dates = pd.date_range(start="2023-01-01", end="2025-10-01", periods=n_saas)
plans = ["Starter", "Professional", "Enterprise"]
contracts = ["Month-to-month", "One year", "Two year"]

saas_data = []
for i in range(n_saas):
    cid = f"USER-{5000 + i}"
    signup = saas_dates[i].strftime("%Y-%m-%d")
    plan = np.random.choice(plans, p=[0.5, 0.35, 0.15])
    contract = np.random.choice(contracts, p=[0.55, 0.30, 0.15])
    
    if plan == "Starter":
        mrr = np.random.uniform(29, 49)
    elif plan == "Professional":
        mrr = np.random.uniform(99, 199)
    else:
        mrr = np.random.uniform(499, 1200)
        
    tenure = np.random.randint(1, 36)
    total_charges = round(mrr * tenure * np.random.uniform(0.95, 1.05), 2)
    mrr = round(mrr, 2)
    tickets = np.random.poisson(lam=2.5)
    active_users = np.random.randint(1, 50 if plan == "Enterprise" else 10)
    nps = np.random.randint(1, 11)
    
    # Churn probability higher with high tickets, low tenure, month-to-month contract
    churn_score = (tickets * 0.15) - (tenure * 0.02) + (0.3 if contract == "Month-to-month" else -0.2) + (0.2 if nps < 6 else -0.3)
    churn = "Yes" if churn_score > 0.2 else "No"
    
    saas_data.append({
        "Customer_ID": cid,
        "Signup_Date": signup,
        "Plan_Tier": plan,
        "Contract_Type": contract,
        "Monthly_Charges": mrr,
        "Total_Charges": total_charges,
        "Tenure_Months": tenure,
        "Support_Tickets": tickets,
        "Active_Users": active_users,
        "NPS_Score": nps,
        "Churn_Status": churn
    })

df_saas = pd.DataFrame(saas_data)
df_saas.to_csv("sample_data/saas_churn_bi.csv", index=False)
print("Saved sample_data/saas_churn_bi.csv with shape:", df_saas.shape)

# 3. HR Workforce Dataset
n_hr = 600
departments = ["Sales", "Engineering", "Marketing", "Human Resources", "Finance"]
roles = {
    "Sales": ["Sales Representative", "Account Executive", "Sales Manager"],
    "Engineering": ["Software Engineer", "DevOps Engineer", "Engineering Lead"],
    "Marketing": ["Content Specialist", "Growth Manager", "Marketing Lead"],
    "Human Resources": ["HR Specialist", "Recruiter", "HR Manager"],
    "Finance": ["Financial Analyst", "Accountant", "Finance Director"]
}

hr_data = []
for i in range(n_hr):
    eid = f"EMP-{3000 + i}"
    dept = np.random.choice(departments, p=[0.3, 0.35, 0.15, 0.1, 0.1])
    role = np.random.choice(roles[dept])
    age = np.random.randint(22, 60)
    years = np.random.randint(1, min(age - 20, 25))
    rating = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.15, 0.5, 0.2, 0.1])
    overtime = np.random.choice(["Yes", "No"], p=[0.28, 0.72])
    satisfaction = np.random.choice([1, 2, 3, 4], p=[0.1, 0.25, 0.45, 0.2])
    base_salary = 40000 + (years * 2500) + (15000 if "Manager" in role or "Lead" in role or "Director" in role else 0)
    salary = round(base_salary * np.random.uniform(0.9, 1.15), -2)
    
    attrition_prob = 0.10 + (0.2 if overtime == "Yes" else 0.0) - (satisfaction * 0.04) + (0.1 if rating == 1 else 0)
    attrition = "Yes" if np.random.rand() < max(0.05, attrition_prob) else "No"
    
    hr_data.append({
        "Employee_ID": eid,
        "Department": dept,
        "Job_Role": role,
        "Age": age,
        "Years_At_Company": years,
        "Annual_Salary": salary,
        "Performance_Rating": rating,
        "Job_Satisfaction": satisfaction,
        "Overtime": overtime,
        "Attrition": attrition,
        "Training_Hours_Last_Year": np.random.randint(10, 60)
    })

df_hr = pd.DataFrame(hr_data)
df_hr.to_csv("sample_data/hr_analytics_bi.csv", index=False)
print("Saved sample_data/hr_analytics_bi.csv with shape:", df_hr.shape)
