import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional
import gdown

st.set_page_config(layout="wide")
st.title("COVID-19 Metadata Explorer")

# -------------------------------------------------------------------
# Download & Load Data
# -------------------------------------------------------------------
@st.cache_data
def load_data(file_id: str, nrows: Optional[int] = 50000) -> pd.DataFrame:
    """
    Download a large CSV from Google Drive and load a pandas DataFrame.
    nrows limits rows for faster dev/testing; set to None for full file.
    """
    url = f"https://drive.google.com/uc?id={file_id}"
    output = "metadata.csv"
    gdown.download(url, output, quiet=False)  # handles confirm token for big files
    return pd.read_csv(output, nrows=nrows, low_memory=False)

FILE_ID = "1xNK8OfdT33pR-hQKB2wlKemQDSGBBWd9"   # <-- your file ID
with st.spinner("Downloading & loading data... this may take a while"):
    df = load_data(FILE_ID, nrows=50000)      # set nrows=None for full dataset

st.success(f"Loaded {len(df):,} rows.")
st.write("### Available columns (first 100 shown):")
st.write(list(df.columns[:100]))

# -------------------------------------------------------------------
# Detect a date column automatically
# -------------------------------------------------------------------
def find_date_column(data: pd.DataFrame) -> Optional[str]:
    cols = list(data.columns)
    low  = [c.lower() for c in cols]
    candidates = [
        "publish_time", "publish_date", "pub_date",
        "date", "publication_date", "time"
    ]
    for cand in candidates:
        if cand in low:
            return cols[low.index(cand)]
    for i, c in enumerate(low):
        if any(k in c for k in ("publish","publication","pub","date","time")):
            return cols[i]
    return None

date_col = find_date_column(df)
if date_col is None:
    st.warning("No obvious date column found. Cannot compute papers per year.")
    st.dataframe(df.head())
    st.stop()

st.success(f"Detected date column: **{date_col}**")
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
if df[date_col].notna().sum() == 0:
    st.error(f"Column `{date_col}` exists but no valid dates were parsed.")
    st.dataframe(df[[date_col]].head(20))
    st.stop()

df["year"] = df[date_col].dt.year

# -------------------------------------------------------------------
# Data Preview
# -------------------------------------------------------------------
st.subheader("Dataset Preview (first 5 rows)")
st.dataframe(df.head())

# -------------------------------------------------------------------
# Papers per Year
# -------------------------------------------------------------------
st.subheader("Number of Papers per Year")
year_counts = df["year"].value_counts().dropna().sort_index()
if len(year_counts) > 0:
    fig, ax = plt.subplots(figsize=(10,4))
    sns.barplot(x=year_counts.index.astype(str), y=year_counts.values, ax=ax)
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Papers")
    ax.set_title("Papers Published per Year")
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("No valid year values found.")

# -------------------------------------------------------------------
# Top Journals
# -------------------------------------------------------------------
st.subheader("Top 10 Journals")
if "journal" in df.columns:
    top_journals = df["journal"].value_counts().head(10)
    fig2, ax2 = plt.subplots(figsize=(8,5))
    sns.barplot(y=top_journals.index, x=top_journals.values, ax=ax2, color="coral")
    ax2.set_xlabel("Number of Papers")
    ax2.set_ylabel("Journal")
    ax2.set_title("Top 10 Journals")
    st.pyplot(fig2)
else:
    st.info("No 'journal' column found in the CSV.")

# -------------------------------------------------------------------
# Filter by Year
# -------------------------------------------------------------------
st.subheader("Filter Papers by Year")
years_available = sorted(df["year"].dropna().unique())
if years_available:
    selected_year = st.selectbox("Select Year:", years_available)
    filtered = df[df["year"] == selected_year]
    st.write(f"Showing {len(filtered):,} papers published in {selected_year}")
    cols_to_show = [c for c in ["title","journal",date_col] if c in df.columns]
    st.dataframe(filtered[cols_to_show].head(50))
else:
    st.info("No available years to filter.")
