# Netflix Insights

A Streamlit dashboard for exploring Netflix viewing records, monthly revenue, ratings, regions, subscription plans, and content categories.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run Untitled.py
```

Upload a CSV in the sidebar, or place a file named `netflix.csv` beside `Untitled.py`. The CSV must include these columns:

- `Watch_Date`
- `Region`
- `Monthly_Revenue`
- `Subscription_Plan`
- `Rating`
- `Category`