import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.title("CORD-19 Metadata Explorer")

import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    url = 'https://drive.google.com/uc?export=download&id=1xNK8OfdT33pR-hQKB2wlKemQDSGBBWd9'
    return pd.read_csv(url)

df = load_data()
st.dataframe(df.head())


st.subheader("Dataset Preview")
st.dataframe(df.head())

# --- Papers per Year ---
st.subheader("Number of Papers per Year")
df['publish_time'] = pd.to_datetime(df['publish_time'], errors='coerce')
df['year'] = df['publish_time'].dt.year
year_counts = df['year'].value_counts().sort_index()

fig, ax = plt.subplots(figsize=(10,5))
sns.barplot(x=year_counts.index, y=year_counts.values, color='skyblue', ax=ax)
ax.set_xlabel("Year")
ax.set_ylabel("Number of Papers")
ax.set_title("Papers Published per Year")
st.pyplot(fig)

# --- Top Journals ---
st.subheader("Top 10 Journals")
top_journals = df['journal'].value_counts().head(10)

fig2, ax2 = plt.subplots(figsize=(8,6))
sns.barplot(y=top_journals.index, x=top_journals.values, color='coral', ax=ax2)
ax2.set_xlabel("Number of Papers")
ax2.set_ylabel("Journal")
ax2.set_title("Top 10 Journals")
st.pyplot(fig2)

# --- Filter by Year ---
st.subheader("Filter Papers by Year")
selected_year = st.selectbox("Select Year:", sorted(df['year'].dropna().unique()))
filtered = df[df['year'] == selected_year]
st.write(f"Showing {len(filtered)} papers published in {selected_year}")
st.dataframe(filtered[['title','journal','publish_time']].head(20))
