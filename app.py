import os
import time
import streamlit as st
import pandas as pd

from scraper import run_scraper
from pdf_generator import generate_pdf

# ---------------- CONFIG ---------------- #

st.set_page_config(
    page_title="African Youth Opportunities",
    page_icon="🌍",
    layout="wide"
)

CSV_FILE = "opportunities.csv"
PDF_FILE = "opportunities.pdf"

# Auto refresh every 12 hours
REFRESH_HOURS = 12

# ---------------- FUNCTIONS ---------------- #

def needs_refresh():

    if not os.path.exists(CSV_FILE):
        return True

    age = time.time() - os.path.getmtime(CSV_FILE)

    return age > REFRESH_HOURS * 3600


@st.cache_data(show_spinner=False)
def load_data():

    return pd.read_csv(CSV_FILE)


def refresh():

    with st.spinner("Refreshing opportunities..."):

        run_scraper()

        generate_pdf()

# ---------------- SIDEBAR ---------------- #

st.sidebar.title("Opportunity Finder")

if st.sidebar.button("🔄 Refresh Now"):

    refresh()

if needs_refresh():

    refresh()

# ---------------- LOAD ---------------- #

if not os.path.exists(CSV_FILE):

    refresh()

df = load_data()

# ---------------- TITLE ---------------- #

st.title("🌍 African Youth Opportunities")

st.write(f"**{len(df)} Active Opportunities Found**")

# ---------------- SEARCH ---------------- #

search = st.text_input(
    "Search Opportunities"
)

if search:

    mask = (
        df["title"].str.contains(search,case=False,na=False)
        |
        df["organization"].str.contains(search,case=False,na=False)
        |
        df["description"].str.contains(search,case=False,na=False)
    )

    df = df[mask]

# ---------------- FILTERS ---------------- #

col1,col2,col3=st.columns(3)

with col1:

    org=st.selectbox(
        "Organization",
        ["All"]+sorted(df.organization.unique().tolist())
    )

with col2:

    typ=st.selectbox(
        "Type",
        ["All"]+sorted(df.type.unique().tolist())
    )

with col3:

    deadline=st.selectbox(
        "Deadline",
        ["All","Rolling","Closing Soon"]
    )

if org!="All":

    df=df[df.organization==org]

if typ!="All":

    df=df[df.type==typ]

if deadline=="Rolling":

    df=df[df.deadline=="Rolling"]

# ---------------- DISPLAY ---------------- #

for _,row in df.iterrows():

    with st.container():

        st.subheader(row["title"])

        st.write(f"**Organization:** {row['organization']}")

        st.write(f"**Type:** {row['type']}")

        st.write(f"**Deadline:** {row['deadline']}")

        st.write(row["description"])

        st.markdown(
            f"[Apply Here]({row['link']})"
        )

        st.divider()

# ---------------- DOWNLOADS ---------------- #

c1,c2=st.columns(2)

with c1:

    with open(CSV_FILE,"rb") as f:

        st.download_button(

            "⬇ Download CSV",

            f,

            file_name="opportunities.csv",

            mime="text/csv"

        )

with c2:

    with open(PDF_FILE,"rb") as f:

        st.download_button(

            "⬇ Download PDF",

            f,

            file_name="opportunities.pdf",

            mime="application/pdf"

        )

# ---------------- FOOTER ---------------- #

st.markdown("---")

st.caption("Developed by Pride @ Cyber_Ninja")
