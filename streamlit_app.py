import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional

st.set_page_config(layout="wide")
st.title("CORD-19 Metadata Explorer (robust loader)")

# ----- load data (optionally limit rows to avoid huge downloads) -----
@st.cache_data
def load_data(url: str, nrows: Optional[int] = 50000):
    try:
        if nrows:
            return pd.read_csv(url, nrows=nrows, low_memory=False)
        else:
            return pd.read_csv(url, low_memory=False)
    except Exception as e:
        # re-raise so caller can display error
        raise

# replace with your Drive id/url
DATA_URL = "https://drive.google.com/uc?export=download&id=1xNK8OfdT33pR-hQKB2wlKemQDSGBBWd9"

# load (use nrows during development; remove or set to None later)
with st.spinner("Loading data — this may take a while..."):
    try:
        df = load_data(DATA_URL, nrows=50000)
    except Exception as e:
        st.error("Failed to load CSV from the URL. Check sharing permissions and link.")
        st.exception(e)
        st.stop()

st.write("### Available columns (first 100 shown):")
st.write(list(df.columns[:100]))  # show columns, helps debugging

# ----- find a date column (robust) -----
def find_date_column(df: pd.DataFrame) -> Optional[str]:
    cols = list(df.columns)
    low = [c.lower() for c in cols]
    # 1) exact common names
    candidates = ['publish_time','publish_date','pub_date','date','publication_date','pub_date']
    for cand in candidates:
        if cand in low:
            return cols[low.index(cand)]
    # 2) keywords match ('publish' or 'date' or 'time' or 'pub')
    for i, c in enumerate(low):
        if any(k in c for k in ('publish','publication','pub','date','time')):
            return cols[i]
    return None

date_col = find_date_column(df)
if date_col is None:
    st.warning("No obvious date column found. The app cannot compute 'papers per year' without a date column.")
    st.info("Column names shown above — if a date-like column exists, rename it to 'publish_time' or 'publish_date' in your CSV, or update the code.")
    # Still show a preview of data so you can inspect
    st.subheader("Dataset preview")
    st.dataframe(df.head())
    st.stop()

st.success(f"Detected date column: **{date_col}** — attempting to parse it now.")
# parse the detected column
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# if parsing produced no usable dates, let user know
if df[date_col].notna().sum() == 0:
    st.error(f"The column `{date_col}` was found but could not be parsed to datetime (all values NaT).")
    st.info("Try a different sample or check the CSV formatting.")
    st.dataframe(df[[date_col]].head(20))
    st.stop()

# create year column
df['year'] = df[date_col].dt.year

# show basic preview + counts
st.subheader("Dataset Preview (first 5 rows)")
st.dataframe(df.head())

# --- Papers per Year (only if years exist) ---
st.subheader("Number of Papers per Year")
year_counts = df['year'].value_counts().dropna().sort_index()
if len(year_counts) == 0:
    st.warning("No year values found after parsing dates — cannot plot yearly trend.")
else:
    fig, ax = plt.subplots(figsize=(10,4))
    sns.barplot(x=year_counts.index.astype(str), y=year_counts.values, ax=ax)
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Papers")
    ax.set_title("Papers Published per Year")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# --- Top Journals ---
st.subheader("Top 10 Journals")
if 'journal' in df.columns:
    top_journals = df['journal'].value_counts().head(10)
    fig2, ax2 = plt.subplots(figsize=(8,5))
    sns.barplot(y=top_journals.index, x=top_journals.values, ax=ax2)
    ax2.set_xlabel("Number of Papers")
    ax2.set_ylabel("Journal")
    st.pyplot(fig2)
else:
    st.info("No 'journal' column found in the CSV.")

# --- Filter by Year ---
st.subheader("Filter Papers by Year")
years_available = sorted(df['year'].dropna().unique())
if len(years_available) == 0:
    st.info("No available years to filter.")
else:
    selected_year = st.selectbox("Select Year:", years_available)
    filtered = df[df['year'] == selected_year]
    st.write(f"Showing {len(filtered)} papers published in {selected_year}")
    cols_to_show = [c for c in ['title','journal', date_col] if c in df.columns]
    st.dataframe(filtered[cols_to_show].head(50))

