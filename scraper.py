import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin, urlparse


# =====================================
# AFRICAN OPPORTUNITY SOURCES
# =====================================

OPPORTUNITY_SOURCES = [

    {
        "name": "African Union",
        "url": "https://au.int/en/jobs"
    },

    {
        "name": "United Nations Careers",
        "url": "https://careers.un.org/"
    },

    {
        "name": "World Bank Careers",
        "url": "https://www.worldbank.org/en/about/careers"
    },

    {
        "name": "African Development Bank",
        "url": "https://www.afdb.org/en/about-us/careers"
    },

    {
        "name": "Mastercard Foundation",
        "url": "https://mastercardfdn.org/all/scholarships/"
    },

    {
        "name": "Google Careers",
        "url": "https://careers.google.com/"
    },

    {
        "name": "Microsoft Careers",
        "url": "https://careers.microsoft.com/"
    },

    {
        "name": "Youth Hub Africa",
        "url": "https://opportunities.youthhubafrica.org/"
    }

]



# =====================================
# HEADERS
# =====================================

HEADERS = {

    "User-Agent":

    "Mozilla/5.0"

}



# =====================================
# BLOCKED SOURCES
# =====================================

BLOCKED_DOMAINS = [

    "medium.com",
    "linkedin.com",
    "facebook.com",
    "reddit.com",
    "wordpress.com",
    "blogspot.com"

]



# =====================================
# CLEAN TEXT
# =====================================

def clean_text(text):

    if not text:

        return ""

    text = re.sub(

        r"\s+",

        " ",

        text

    )

    return text.strip()



# =====================================
# DOMAIN CHECK
# =====================================

def valid_domain(url):

    domain = urlparse(

        url

    ).netloc.lower()



    for blocked in BLOCKED_DOMAINS:

        if blocked in domain:

            return False


    return True



# =====================================
# FIND APPLICATION LINK
# =====================================

def is_application_link(url):

    keywords = [

        "apply",

        "application",

        "register",

        "career",

        "jobs",

        "internship",

        "program",

        "scholarship"

    ]


    url = url.lower()


    return any(

        word in url

        for word in keywords

    )



# =====================================
# CATEGORY
# =====================================

def detect_category(text):

    text = text.lower()


    if "internship" in text:

        return "Internship"


    if "scholarship" in text:

        return "Scholarship"


    if "fellowship" in text:

        return "Fellowship"


    if "grant" in text:

        return "Grant"


    if "job" in text:

        return "Job"


    return "Youth Opportunity"




# =====================================
# SCRAPE SINGLE SOURCE
# =====================================

def scrape_source(source):

    results = []


    try:

        response = requests.get(

            source["url"],

            headers=HEADERS,

            timeout=20

        )


        soup = BeautifulSoup(

            response.text,

            "html.parser"

        )


        links = soup.find_all(

            "a"

        )


        for link in links:


            title = clean_text(

                link.get_text()

            )


            href = link.get(

                "href"

            )


            if not href:

                continue



            href = urljoin(

                source["url"],

                href

            )



            if len(title) < 5:

                continue



            if not valid_domain(

                href

            ):

                continue



            if not is_application_link(

                href

            ):

                continue



            results.append(

                {

                    "Opportunity":

                    title,


                    "Organization":

                    source["name"],


                    "Category":

                    detect_category(

                        title

                    ),


                    "Official Application Link":

                    href,


                    "Source":

                    source["url"]

                }

            )


    except Exception as e:

        print(

            source["name"],

            e

        )


    return results




# =====================================
# SCRAPE ALL SOURCES
# =====================================

def scrape_sources():

    all_results = []


    for source in OPPORTUNITY_SOURCES:


        print(

            "Scanning:",

            source["name"]

        )


        results = scrape_source(

            source

        )


        all_results.extend(

            results

        )



    return clean_results(

        all_results

    )



# =====================================
# CLEAN DATA
# =====================================

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



# =====================================
# TEST
# =====================================

if __name__ == "__main__":


    opportunities = scrape_sources()


    print(

        opportunities.head()

    )
