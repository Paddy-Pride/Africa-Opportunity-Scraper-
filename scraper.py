import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime


# ---------------------------------------
# USER AGENT
# ---------------------------------------

HEADERS = {
    "User-Agent": 
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


# ---------------------------------------
# CLEAN TEXT
# ---------------------------------------

def clean_text(text):
    """
    Remove unwanted spaces and characters
    """

    if not text:
        return ""

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()



# ---------------------------------------
# EXTRACT DEADLINE
# ---------------------------------------

def extract_deadline(text):

    if not text:
        return "Not specified"

    patterns = [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        r"\d{1,2}\s(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group()

    return "Not specified"



# ---------------------------------------
# CATEGORY DETECTION
# ---------------------------------------

def detect_category(text):

    text = text.lower()


    if any(word in text for word in [
        "scholarship",
        "funding",
        "financial aid"
    ]):
        return "Scholarship"


    elif any(word in text for word in [
        "internship",
        "attachment",
        "trainee"
    ]):
        return "Internship"


    elif any(word in text for word in [
        "job",
        "career",
        "employment"
    ]):
        return "Job"


    elif any(word in text for word in [
        "fellowship",
        "leadership program"
    ]):
        return "Fellowship"


    elif any(word in text for word in [
        "grant",
        "competition",
        "award"
    ]):
        return "Grant"


    return "Other"



# ---------------------------------------
# RELEVANCE SCORE
# ---------------------------------------

def calculate_score(text, keywords):

    if not text:
        return 0


    text = text.lower()

    score = 0


    for word in keywords:

        if word.lower() in text:
            score += 1


    return score



# ---------------------------------------
# GENERIC WEBSITE SCRAPER
# ---------------------------------------

def scrape_website(url, keywords=None):

    if keywords is None:

        keywords = [
            "technology",
            "computer science",
            "data science",
            "ai",
            "software",
            "student",
            "internship"
        ]


    opportunities = []


    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )


        response.raise_for_status()


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        links = soup.find_all("a")


        for link in links:

            title = clean_text(
                link.get_text()
            )


            href = link.get("href")


            if not title or not href:
                continue



            if href.startswith("/"):

                href = url.rstrip("/") + href



            description = title


            opportunity = {

                "Title": title,

                "Organization": url.split("//")[-1].split("/")[0],

                "Description": description,

                "Deadline": extract_deadline(description),

                "Category": detect_category(description),

                "Location": "Not specified",

                "Link": href,

                "Source": url,

                "Score": calculate_score(
                    description,
                    keywords
                )

            }


            opportunities.append(
                opportunity
            )


    except Exception as e:

        print(
            f"Error scraping {url}: {e}"
        )


    return opportunities




# ---------------------------------------
# MULTIPLE SOURCES SCRAPER
# ---------------------------------------

def scrape_sources(urls):

    all_results = []


    for url in urls:

        print(
            f"Scraping {url}"
        )


        results = scrape_website(
            url
        )


        all_results.extend(
            results
        )


    return clean_dataframe(
        all_results
    )



# ---------------------------------------
# CLEAN DATAFRAME
# ---------------------------------------

def clean_dataframe(data):

    df = pd.DataFrame(data)


    if df.empty:
        return df



    # Remove duplicates

    df.drop_duplicates(
        subset=["Title"],
        inplace=True
    )


    # Remove empty titles

    df = df[
        df["Title"].str.len() > 3
    ]


    # Sort best matches

    df.sort_values(
        by="Score",
        ascending=False,
        inplace=True
    )


    df.reset_index(
        drop=True,
        inplace=True
    )


    return df



# ---------------------------------------
# SAVE CSV
# ---------------------------------------

def save_csv(df, filename):

    df.to_csv(
        filename,
        index=False
    )



# ---------------------------------------
# PDF REPORT DATA
# ---------------------------------------

def generate_report_text(df):

    report = []

    report.append(
        "OPPORTUNITY SCRAPER REPORT"
    )

    report.append(
        str(datetime.now())
    )

    report.append(
        "\n"
    )


    for index,row in df.iterrows():

        report.append(
            f"""
Title:
{row['Title']}

Category:
{row['Category']}

Deadline:
{row['Deadline']}

Link:
{row['Link']}

Score:
{row['Score']}

-----------------------
"""
        )


    return "\n".join(report)



# ---------------------------------------
# TEST RUN
# ---------------------------------------

if __name__ == "__main__":


    websites = [

        "https://www.opportunitiesforafricans.com/",

    ]


    data = scrape_sources(
        websites
    )


    print(data.head())


    save_csv(
        data,
        "opportunities.csv"
    )
