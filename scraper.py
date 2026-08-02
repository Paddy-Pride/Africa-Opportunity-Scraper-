import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin, urlparse


# ---------------------------------------
# REQUEST SETTINGS
# ---------------------------------------

HEADERS = {
    "User-Agent": 
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}



# ---------------------------------------
# BLOCKED WEBSITES
# ---------------------------------------

BLOCKED_DOMAINS = [

    "medium.com",
    "linkedin.com",
    "facebook.com",
    "reddit.com",
    "opportunitiesforafricans.com",
    "scholarshiproar.com",
    "scholarshipportal.com",
    "weforum.org/blog",
    "wordpress.com"

]



# ---------------------------------------
# CLEAN TEXT
# ---------------------------------------

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()



# ---------------------------------------
# CHECK OFFICIAL DOMAIN
# ---------------------------------------

def is_official_link(url):

    if not url:
        return False


    domain = urlparse(url).netloc.lower()


    for blocked in BLOCKED_DOMAINS:

        if blocked in domain:

            return False


    return True



# ---------------------------------------
# CHECK APPLICATION URL
# ---------------------------------------

def is_application_link(url):

    if not url:

        return False


    keywords = [

        "apply",
        "application",
        "register",
        "registration",
        "career",
        "jobs",
        "internship",
        "scholarship",
        "admission",
        "portal"

    ]


    url = url.lower()


    return any(
        word in url
        for word in keywords
    )



# ---------------------------------------
# CATEGORY IDENTIFIER
# ---------------------------------------

def identify_category(text):

    text = text.lower()


    if "intern" in text:

        return "Internship"


    if "scholar" in text:

        return "Scholarship"


    if "fellow" in text:

        return "Fellowship"


    if "grant" in text:

        return "Grant"


    if "job" in text or "career" in text:

        return "Job"


    return "Opportunity"



# ---------------------------------------
# DEADLINE EXTRACTION
# ---------------------------------------

def find_deadline(text):

    pattern = (

        r"\b\d{1,2}"
        r"[-/]"
        r"\d{1,2}"
        r"[-/]"
        r"\d{2,4}\b"

    )


    result = re.search(
        pattern,
        text
    )


    if result:

        return result.group()


    months = (

        "January|February|March|April|May|June|"
        "July|August|September|October|November|December"

    )


    result = re.search(

        rf"\d{{1,2}}\s({months})\s\d{{4}}",

        text,

        re.IGNORECASE

    )


    if result:

        return result.group()


    return "Not specified"



# ---------------------------------------
# EXTRACT OPPORTUNITIES
# ---------------------------------------

def scrape_website(url):

    opportunities = []


    try:

        response = requests.get(

            url,

            headers=HEADERS,

            timeout=15

        )


        soup = BeautifulSoup(

            response.text,

            "html.parser"

        )


        page_text = clean_text(
            soup.get_text()
        )


        links = soup.find_all(
            "a"
        )


        for link in links:


            title = clean_text(
                link.text
            )


            href = link.get(
                "href"
            )


            if not href:

                continue


            href = urljoin(
                url,
                href
            )


            if not is_application_link(
                href
            ):

                continue


            if not is_official_link(
                href
            ):

                continue



            opportunity = {


                "Opportunity":

                title,


                "Organization":

                urlparse(url).netloc,


                "Category":

                identify_category(
                    page_text
                ),


                "Deadline":

                find_deadline(
                    page_text
                ),


                "Official Application Link":

                href,


                "Verification":

                "Verified"


            }


            opportunities.append(
                opportunity
            )


    except Exception as error:


        print(
            error
        )



    return opportunities



# ---------------------------------------
# MULTI SOURCE SCRAPER
# ---------------------------------------

def scrape_sources(urls):

    results = []


    for url in urls:


        print(
            "Checking:",
            url
        )


        results.extend(

            scrape_website(
                url
            )

        )


    return clean_results(
        results
    )



# ---------------------------------------
# CLEAN RESULTS
# ---------------------------------------

def clean_results(data):

    df = pd.DataFrame(
        data
    )


    if df.empty:

        return df



    df.drop_duplicates(

        subset=[
            "Official Application Link"
        ],

        inplace=True

    )


    return df.reset_index(
        drop=True
    )



# ---------------------------------------
# EXPORT CSV
# ---------------------------------------

def export_csv(df):

    return df.to_csv(
        index=False
    )



# ---------------------------------------
# TEST
# ---------------------------------------

if __name__ == "__main__":


    sources = [

        "https://careers.microsoft.com/",

        "https://www.un.org/development/desa/youth/"

    ]


    data = scrape_sources(
        sources
    )


    print(data)
