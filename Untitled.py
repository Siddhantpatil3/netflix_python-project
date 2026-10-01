from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


st.set_page_config(
	page_title="Netflix Insights",
	page_icon="N",
	layout="wide",
	initial_sidebar_state="expanded",
)

st.markdown(
	"""
	<style>
	@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
	:root { --ink: #20201f; --muted: #74736f; --paper: #f6f5f1; --red: #e50914; --line: #e5e2dc; }
	.stApp { background: var(--paper); color: var(--ink); font-family: 'DM Sans', sans-serif; }
	[data-testid="stSidebar"] { background: #eeece6; border-right: 1px solid var(--line); }
	[data-testid="stSidebar"] * { font-family: 'DM Sans', sans-serif; }
	.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1440px; }
	h1, h2, h3 { font-family: 'Manrope', sans-serif; color: var(--ink); letter-spacing: 0; }
	.eyebrow { color: var(--red); text-transform: uppercase; font-size: .72rem; font-weight: 700; letter-spacing: .12em; }
	.page-title { font-family: 'Manrope', sans-serif; font-size: 2.25rem; font-weight: 800; line-height: 1.15; margin: .3rem 0 .55rem; }
	.page-subtitle { color: var(--muted); margin-bottom: 1.7rem; }
	.metric-card { background: #fff; border: 1px solid var(--line); border-top: 3px solid var(--red); padding: 1rem 1.1rem; min-height: 112px; }
	.metric-label { color: var(--muted); font-size: .78rem; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }
	.metric-value { font-family: 'Manrope', sans-serif; font-size: 1.8rem; font-weight: 800; line-height: 1.35; }
	.section-heading { font-family: 'Manrope', sans-serif; font-size: 1.08rem; font-weight: 700; padding-bottom: .65rem; border-bottom: 1px solid var(--line); margin: 1.1rem 0 .9rem; }
	.empty-state { border: 1px dashed #c9c5bc; background: rgba(255,255,255,.55); padding: 2rem; color: var(--muted); }
	div[data-testid="stDataFrame"] { border: 1px solid var(--line); }
	</style>
	""",
	unsafe_allow_html=True,
)


def load_data(uploaded_file):
	if uploaded_file is not None:
		return pd.read_csv(uploaded_file)
	default_path = Path(__file__).with_name("netflix.csv")
	if default_path.exists():
		return pd.read_csv(default_path)
	return None


def money(value):
	return f"${value:,.0f}"


st.sidebar.markdown("<div class='eyebrow'>Data source</div>", unsafe_allow_html=True)
st.sidebar.header("Netflix Insights")
uploaded_file = st.sidebar.file_uploader("Upload a Netflix CSV", type=["csv"])
st.sidebar.caption("Uses `netflix.csv` beside this app when no file is uploaded.")

st.markdown("<div class='eyebrow'>Audience & revenue overview</div>", unsafe_allow_html=True)
st.markdown("<div class='page-title'>Netflix Insights</div>", unsafe_allow_html=True)
st.markdown(
	"<div class='page-subtitle'>Explore viewing activity, ratings, and revenue across your dataset.</div>",
	unsafe_allow_html=True,
)

try:
	netflix = load_data(uploaded_file)
except Exception as error:
	st.error(f"The CSV could not be read: {error}")
	st.stop()

if netflix is None:
	st.markdown(
		"<div class='empty-state'><strong>Your dashboard is ready for data.</strong><br>Upload a CSV to begin, or add <code>netflix.csv</code> beside this Python file.</div>",
		unsafe_allow_html=True,
	)
	st.stop()

if netflix.empty:
	st.warning("This CSV has headers but no rows to analyze.")
	st.stop()

required_columns = {"Watch_Date", "Region", "Monthly_Revenue", "Subscription_Plan", "Rating", "Category"}
missing_columns = sorted(required_columns.difference(netflix.columns))
if missing_columns:
	st.error(f"Missing required columns: {', '.join(missing_columns)}")
	st.caption(f"Available columns: {', '.join(map(str, netflix.columns))}")
	st.stop()

netflix["Watch_Date"] = pd.to_datetime(netflix["Watch_Date"], errors="coerce")
netflix["Monthly_Revenue"] = pd.to_numeric(netflix["Monthly_Revenue"], errors="coerce")
netflix["Rating"] = pd.to_numeric(netflix["Rating"], errors="coerce")

st.sidebar.markdown("<div class='eyebrow'>Refine view</div>", unsafe_allow_html=True)
filter_columns = ["Region", "Subscription_Plan", "Category"]
filters = {}
for column in filter_columns:
	options = sorted(netflix[column].dropna().astype(str).unique().tolist())
	selected = st.sidebar.multiselect(column.replace("_", " "), options, default=options)
	filters[column] = selected

filtered = netflix.copy()
for column, selected in filters.items():
	filtered = filtered[filtered[column].astype(str).isin(selected)]

valid_dates = filtered["Watch_Date"].dropna()
if not valid_dates.empty:
	date_range = st.sidebar.date_input(
		"Watch date range",
		value=(valid_dates.min().date(), valid_dates.max().date()),
		min_value=valid_dates.min().date(),
		max_value=valid_dates.max().date(),
	)
	if isinstance(date_range, tuple) and len(date_range) == 2:
		start_date, end_date = date_range
		filtered = filtered[
			filtered["Watch_Date"].dt.date.between(start_date, end_date)
		]

if filtered.empty:
	st.info("No records match these filters. Adjust the selections in the sidebar.")
	st.stop()

total_revenue = filtered["Monthly_Revenue"].sum()
average_rating = filtered["Rating"].mean()
region_count = filtered["Region"].nunique()
watch_period = filtered["Watch_Date"].nunique()

metric_columns = st.columns(4, gap="small")
metrics = [
	("Monthly revenue", money(total_revenue)),
	("Watch records", f"{len(filtered):,}"),
	("Average rating", f"{average_rating:.1f}" if pd.notna(average_rating) else "—"),
	("Regions covered", f"{region_count:,}"),
]
for column, (label, value) in zip(metric_columns, metrics):
	column.markdown(
		f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>",
		unsafe_allow_html=True,
	)

st.markdown("<div class='section-heading'>Performance breakdown</div>", unsafe_allow_html=True)
chart_columns = st.columns(2, gap="large")

with chart_columns[0]:
	st.subheader("Revenue by region")
	revenue_by_region = filtered.groupby("Region")["Monthly_Revenue"].sum().sort_values(ascending=False)
	figure, axis = plt.subplots(figsize=(7, 4))
	revenue_by_region.plot(kind="bar", ax=axis, color="#e50914", edgecolor="white")
	axis.set_ylabel("Monthly revenue")
	axis.set_xlabel("")
	axis.tick_params(axis="x", rotation=30)
	axis.spines[["top", "right"]].set_visible(False)
	figure.tight_layout()
	st.pyplot(figure, width="stretch")
	plt.close(figure)

with chart_columns[1]:
	st.subheader("Rating sum by subscription plan")
	ratings_by_plan = filtered.groupby("Subscription_Plan")["Rating"].sum()
	if ratings_by_plan.empty or ratings_by_plan.sum() == 0:
		st.caption("No ratings are available for this selection.")
	else:
		figure, axis = plt.subplots(figsize=(7, 4))
		ratings_by_plan.plot(
			kind="pie",
			ax=axis,
			startangle=90,
			counterclock=False,
			colors=["#e50914", "#282826", "#d5a021", "#4c8c6b", "#b9b5ab"],
			wedgeprops={"linewidth": 2, "edgecolor": "white"},
			autopct="%1.1f%%",
		)
		axis.set_ylabel("")
		axis.set_aspect("equal")
		figure.tight_layout()
		st.pyplot(figure, width="stretch")
		plt.close(figure)

chart_columns = st.columns(2, gap="large")
with chart_columns[0]:
	st.subheader("Rating distribution")
	rating_counts = filtered["Rating"].dropna().value_counts().sort_index()
	if rating_counts.empty:
		st.caption("No numeric ratings are available for this selection.")
	else:
		figure, axis = plt.subplots(figsize=(7, 3.5))
		rating_counts.plot(kind="bar", ax=axis, color="#282826", edgecolor="white")
		axis.set_xlabel("Rating")
		axis.set_ylabel("Number of records")
		axis.tick_params(axis="x", rotation=0)
		axis.spines[["top", "right"]].set_visible(False)
		figure.tight_layout()
		st.pyplot(figure, width="stretch")
		plt.close(figure)

with chart_columns[1]:
	st.subheader("Revenue by category")
	revenue_by_category = filtered.groupby("Category")["Monthly_Revenue"].sum()
	if revenue_by_category.empty or revenue_by_category.sum() == 0:
		st.caption("No revenue is available for this selection.")
	else:
		figure, axis = plt.subplots(figsize=(7, 3.5))
		revenue_by_category.plot(
			kind="pie",
			ax=axis,
			startangle=90,
			counterclock=False,
			colors=["#e50914", "#282826", "#d5a021", "#4c8c6b", "#b9b5ab"],
			wedgeprops={"linewidth": 2, "edgecolor": "white"},
			autopct="%1.1f%%",
		)
		axis.set_ylabel("")
		axis.set_aspect("equal")
		figure.tight_layout()
		st.pyplot(figure, width="stretch")
		plt.close(figure)

st.markdown("<div class='section-heading'>Dataset</div>", unsafe_allow_html=True)
data_tab, quality_tab = st.tabs(["Filtered records", "Data quality"])
with data_tab:
	st.dataframe(filtered, width="stretch", hide_index=True)
with quality_tab:
	quality_columns = st.columns(3)
	quality_columns[0].metric("Rows", f"{len(netflix):,}")
	quality_columns[1].metric("Columns", f"{len(netflix.columns):,}")
	quality_columns[2].metric("Duplicate rows", f"{int(netflix.duplicated().sum()):,}")
	missing_values = netflix.isna().sum().rename("Missing values").to_frame()
	st.dataframe(missing_values, width="stretch")
	st.caption(f"Distinct watch dates in current view: {watch_period:,}")





# In[ ]:





# In[ ]:




