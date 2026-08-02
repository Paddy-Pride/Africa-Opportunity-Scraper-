import streamlit as st
import pandas as pd
from io import BytesIO

from scraper import scrape_sources
from verifier import verify_link
from nlp_matcher import match_opportunities

from reportlab.pdfgen import canvas



# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(

    page_title="Official Opportunity Finder",

    page_icon="🌍",

    layout="wide"

)



# -----------------------------------
# TITLE
# -----------------------------------

st.title(
    "🌍 Official Opportunity Finder"
)


st.write(

"""
Find scholarships, internships, fellowships,
jobs and grants with verified official
application portals.
"""

)



# -----------------------------------
# SIDEBAR
# -----------------------------------

st.sidebar.header(
    "Search Settings"
)



websites = st.sidebar.text_area(

    "Opportunity websites",

"""
https://careers.microsoft.com
https://www.un.org
""",

)



profile = st.sidebar.text_area(

    "Describe yourself",

"""
Computer Science student interested in
AI, software development and internships
in Africa.
"""

)



start = st.sidebar.button(

    "🔎 Find Opportunities"

)



# -----------------------------------
# SESSION STORAGE
# -----------------------------------

if "results" not in st.session_state:

    st.session_state.results = pd.DataFrame()



# -----------------------------------
# MAIN PROCESS
# -----------------------------------

if start:


    sources = [

        x.strip()

        for x in websites.split("\n")

        if x.strip()

    ]



    with st.spinner(
        "Searching official portals..."
    ):


        # 1. SCRAPE

        data = scrape_sources(

            sources

        )



        if data.empty:


            st.warning(

                "No opportunities found"

            )

            st.stop()



        # 2. VERIFY LINKS


        verification = []


        for link in data[

            "Official Application Link"

        ]:


            verification.append(

                verify_link(

                    link

                )

            )



        verification_df = pd.DataFrame(

            verification

        )



        data = pd.concat(

            [

                data.reset_index(drop=True),

                verification_df

            ],

            axis=1

        )



        # Keep only verified portals

        data = data[

            data["Status"]

            ==

            "Verified Official Portal"

        ]



        if data.empty:


            st.warning(

                "No verified official portals found"

            )

            st.stop()



        # 3. NLP MATCHING


        data = match_opportunities(

            data,

            profile

        )



        st.session_state.results = data




# -----------------------------------
# DISPLAY RESULTS
# -----------------------------------

df = st.session_state.results



if not df.empty:


    st.success(

        f"{len(df)} verified opportunities found"

    )



    st.subheader(

        "Recommended Opportunities"

    )



    st.dataframe(

        df,

        use_container_width=True

    )



    # --------------------------------
    # CSV DOWNLOAD
    # --------------------------------


    csv = df.to_csv(

        index=False

    )



    st.download_button(

        "⬇ Download CSV",

        csv,

        "verified_opportunities.csv",

        "text/csv"

    )



    # --------------------------------
    # PDF REPORT
    # --------------------------------


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

            "Official Opportunity Finder Report"

        )


        y -= 40



        for _,row in data.iterrows():


            text = (

                f"{row['Opportunity']} | "

                f"{row['Category']} | "

                f"{row['Official Application Link']}"

            )


            pdf.drawString(

                50,

                y,

                text[:120]

            )


            y -= 30



            if y < 50:

                pdf.showPage()

                y = 800



        pdf.save()


        buffer.seek(0)


        return buffer




    pdf = create_pdf(

        df

    )



    st.download_button(

        "📄 Download PDF Report",

        pdf,

        "opportunity_report.pdf",

        "application/pdf"

    )



else:


    st.info(

        "Enter your profile and click Find Opportunities"

    )
