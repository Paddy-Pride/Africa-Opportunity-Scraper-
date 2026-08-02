import streamlit as st
import pandas as pd
from scraper import scrape_sources, generate_report_text
from io import BytesIO
from reportlab.pdfgen import canvas


# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="Opportunity Scraper AI",
    page_icon="🔎",
    layout="wide"
)


# -----------------------------------
# TITLE
# -----------------------------------

st.title("🔎 Opportunity Scraper AI")

st.write(
    """
Find scholarships, internships, jobs, fellowships and grants 
from different sources using AI-powered matching.
"""
)



# -----------------------------------
# SIDEBAR
# -----------------------------------

st.sidebar.header(
    "Scraper Settings"
)


urls_input = st.sidebar.text_area(
    "Enter websites (one per line)",
    """
https://www.opportunitiesforafricans.com/
"""
)


keywords_input = st.sidebar.text_input(
    "Your interests",
    "computer science, AI, data science, internship"
)



run = st.sidebar.button(
    "🚀 Start Scraping"
)



# -----------------------------------
# SESSION STORAGE
# -----------------------------------

if "data" not in st.session_state:

    st.session_state.data = pd.DataFrame()



# -----------------------------------
# SCRAPE
# -----------------------------------

if run:


    websites = [

        url.strip()

        for url in urls_input.split("\n")

        if url.strip()

    ]


    keywords = [

        x.strip()

        for x in keywords_input.split(",")

    ]


    with st.spinner(
        "Searching opportunities..."
    ):


        data = scrape_sources(
            websites
        )


        if not data.empty:

            # Recalculate score based on user interests

            from scraper import calculate_score


            data["Score"] = data[
                "Description"
            ].apply(
                lambda x:
                calculate_score(
                    x,
                    keywords
                )
            )


            data.sort_values(
                "Score",
                ascending=False,
                inplace=True
            )


        st.session_state.data = data



# -----------------------------------
# DISPLAY RESULTS
# -----------------------------------

df = st.session_state.data



if not df.empty:


    st.success(
        f"{len(df)} opportunities found"
    )


    # Filters

    col1,col2 = st.columns(2)


    with col1:

        category = st.selectbox(
            "Filter category",
            [
                "All"
            ]
            +
            sorted(
                df["Category"]
                .unique()
                .tolist()
            )
        )


    with col2:

        search = st.text_input(
            "Search opportunity"
        )



    filtered = df.copy()



    if category != "All":

        filtered = filtered[
            filtered["Category"]
            ==
            category
        ]



    if search:

        filtered = filtered[
            filtered.apply(
                lambda row:
                search.lower()
                in
                row.astype(str)
                .str.lower()
                .to_string(),

                axis=1
            )
        ]



    st.dataframe(
        filtered,
        use_container_width=True
    )



    # -----------------------------------
    # CSV DOWNLOAD
    # -----------------------------------

    csv = filtered.to_csv(
        index=False
    )


    st.download_button(

        label="⬇ Download CSV",

        data=csv,

        file_name=
        "opportunities.csv",

        mime=
        "text/csv"

    )



    # -----------------------------------
    # PDF GENERATION
    # -----------------------------------

    def create_pdf(data):

        buffer = BytesIO()


        pdf = canvas.Canvas(
            buffer
        )


        y = 800


        pdf.setFont(
            "Helvetica",
            12
        )


        pdf.drawString(
            50,
            y,
            "Opportunity Scraper Report"
        )


        y -= 40



        for _,row in data.iterrows():

            text = (
                f"{row['Title']} | "
                f"{row['Category']} | "
                f"{row['Deadline']}"
            )


            pdf.drawString(
                50,
                y,
                text[:100]
            )


            y -= 20


            if y < 50:

                pdf.showPage()

                y = 800



        pdf.save()


        buffer.seek(0)


        return buffer



    pdf_file = create_pdf(
        filtered
    )



    st.download_button(

        label="📄 Download PDF Report",

        data=pdf_file,

        file_name=
        "opportunity_report.pdf",

        mime=
        "application/pdf"

    )



else:

    st.info(
        "Enter websites and click Start Scraping"
    )
