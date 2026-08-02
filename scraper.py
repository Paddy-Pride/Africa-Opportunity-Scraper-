import requests
import feedparser
import pandas as pd
import concurrent.futures
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser
from fake_useragent import UserAgent

HEADERS = {
    "User-Agent": UserAgent().random
}

RSS_FEEDS = [

    # Scholarships
    "https://www.opportunitiesforafricans.com/feed/",
    "https://youthopportunitieshub.com/feed/",
    "https://opportunitydesk.org/feed/",

    # UN
    "https://jobs.undp.org/rss",
    "https://careers.un.org/lbw/home.aspx?viewtype=SJOBS&Lang=en-US/rss",

]

KEYWORDS = [

    "africa",
    "african",
    "uganda",
    "kenya",
    "rwanda",
    "tanzania",
    "ghana",
    "nigeria",
    "zambia",
    "cameroon",
    "student",
    "youth",
    "scholarship",
    "grant",
    "internship",
    "fellowship",
    "competition",
    "leadership"

]


def clean(text):

    if text is None:
        return ""

    return " ".join(text.split())


def parse_date(text):

    if text is None:
        return None

    text = text.strip()

    try:
        return parser.parse(text,fuzzy=True)

    except:

        return None


def is_active(deadline):

    if deadline is None:

        return True

    return deadline >= datetime.now()


def score(item):

    s = 0

    txt = (
        item["title"]+" "+
        item["description"]
    ).lower()

    for k in KEYWORDS:

        if k in txt:
            s += 2

    if "fully funded" in txt:
        s += 10

    if "uganda" in txt:
        s += 5

    if item["deadline"] != "Rolling":
        s += 3

    return s


def verify(url):

    try:

        r = requests.head(
            url,
            timeout=8,
            allow_redirects=True,
            headers=HEADERS
        )

        return r.status_code == 200

    except:

        return False


def scrape_feed(feed):

    data=[]

    rss=feedparser.parse(feed)

    for e in rss.entries:

        title=clean(e.get("title",""))

        link=e.get("link","")

        desc=BeautifulSoup(
            e.get("summary",""),
            "html.parser"
        ).text

        deadline="Rolling"

        date=parse_date(desc)

        if date:

            deadline=date.strftime("%d %b %Y")

        item={

            "title":title,
            "organization":feed.split("/")[2],
            "description":clean(desc)[:600],
            "deadline":deadline,
            "link":link,
            "source":feed,
            "type":"Opportunity"

        }

        data.append(item)

    return data


def scrape_page(url):

    out=[]

    try:

        r=requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        soup=BeautifulSoup(
            r.text,
            "lxml"
        )

        links=soup.find_all("a",href=True)

        for a in links:

            href=a["href"]

            title=clean(a.get_text())

            if len(title)<8:

                continue

            if "http" not in href:

                continue

            text=(title+" "+href).lower()

            if not any(k in text for k in KEYWORDS):

                continue

            out.append({

                "title":title,
                "organization":url.split("/")[2],
                "description":"",
                "deadline":"Rolling",
                "link":href,
                "source":url,
                "type":"Opportunity"

            })

    except:

        pass

    return out
def remove_duplicates(data):

    seen = set()
    clean_data = []

    for item in data:

        key = (
            item["title"].strip().lower(),
            item["link"].strip().lower()
        )

        if key not in seen:

            seen.add(key)
            clean_data.append(item)

    return clean_data


def filter_relevant(data):

    filtered = []

    for item in data:

        text = (
            item["title"] + " " +
            item["description"]
        ).lower()

        if any(k in text for k in KEYWORDS):

            filtered.append(item)

    return filtered


def filter_active(data):

    active = []

    for item in data:

        if item["deadline"] == "Rolling":

            active.append(item)

        else:

            d = parse_date(item["deadline"])

            if is_active(d):

                active.append(item)

    return active


def verify_links(data):

    verified = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:

        future_map = {
            executor.submit(
                verify,
                item["link"]
            ): item for item in data
        }

        for future in concurrent.futures.as_completed(future_map):

            item = future_map[future]

            try:

                if future.result():

                    verified.append(item)

            except:

                pass

    return verified


def rank(data):

    for item in data:

        item["score"] = score(item)

    data = sorted(
        data,
        key=lambda x: x["score"],
        reverse=True
    )

    return data


def scrape_all():

    opportunities = []

    print("Loading RSS feeds...")

    for feed in RSS_FEEDS:

        try:

            opportunities.extend(
                scrape_feed(feed)
            )

        except Exception as e:

            print(e)

    print("Scanning websites...")

    sites = [

        "https://www.mastercardfdn.org/",
        "https://www.oneyoungworld.com/",
        "https://au.int/",
        "https://www.undp.org/",
        "https://www.afdb.org/",
        "https://codeforafrica.org/",
        "https://yali.state.gov/",
        "https://opportunitydesk.org/",
        "https://opportunitiesforafricans.com/"
    ]

    for site in sites:

        try:

            opportunities.extend(
                scrape_page(site)
            )

        except Exception as e:

            print(e)

    print("Removing duplicates...")

    opportunities = remove_duplicates(opportunities)

    print("Filtering relevance...")

    opportunities = filter_relevant(opportunities)

    print("Filtering expired opportunities...")

    opportunities = filter_active(opportunities)

    print("Checking links...")

    opportunities = verify_links(opportunities)

    print("Ranking...")

    opportunities = rank(opportunities)

    return opportunities


def run_scraper():

    data = scrape_all()

    df = pd.DataFrame(data)

    if len(df):

        df["scraped_at"] = datetime.now().strftime(
            "%d %b %Y %H:%M"
        )

        df.to_csv(
            "opportunities.csv",
            index=False
        )

    print(f"{len(df)} opportunities saved.")

    return df


if __name__ == "__main__":

    run_scraper()def remove_duplicates(data):

    seen = set()
    clean_data = []

    for item in data:

        key = (
            item["title"].strip().lower(),
            item["link"].strip().lower()
        )

        if key not in seen:

            seen.add(key)
            clean_data.append(item)

    return clean_data


def filter_relevant(data):

    filtered = []

    for item in data:

        text = (
            item["title"] + " " +
            item["description"]
        ).lower()

        if any(k in text for k in KEYWORDS):

            filtered.append(item)

    return filtered


def filter_active(data):

    active = []

    for item in data:

        if item["deadline"] == "Rolling":

            active.append(item)

        else:

            d = parse_date(item["deadline"])

            if is_active(d):

                active.append(item)

    return active


def verify_links(data):

    verified = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:

        future_map = {
            executor.submit(
                verify,
                item["link"]
            ): item for item in data
        }

        for future in concurrent.futures.as_completed(future_map):

            item = future_map[future]

            try:

                if future.result():

                    verified.append(item)

            except:

                pass

    return verified


def rank(data):

    for item in data:

        item["score"] = score(item)

    data = sorted(
        data,
        key=lambda x: x["score"],
        reverse=True
    )

    return data


def scrape_all():

    opportunities = []

    print("Loading RSS feeds...")

    for feed in RSS_FEEDS:

        try:

            opportunities.extend(
                scrape_feed(feed)
            )

        except Exception as e:

            print(e)

    print("Scanning websites...")

    sites = [

        "https://www.mastercardfdn.org/",
        "https://www.oneyoungworld.com/",
        "https://au.int/",
        "https://www.undp.org/",
        "https://www.afdb.org/",
        "https://codeforafrica.org/",
        "https://yali.state.gov/",
        "https://opportunitydesk.org/",
        "https://opportunitiesforafricans.com/"
    ]

    for site in sites:

        try:

            opportunities.extend(
                scrape_page(site)
            )

        except Exception as e:

            print(e)

    print("Removing duplicates...")

    opportunities = remove_duplicates(opportunities)

    print("Filtering relevance...")

    opportunities = filter_relevant(opportunities)

    print("Filtering expired opportunities...")

    opportunities = filter_active(opportunities)

    print("Checking links...")

    opportunities = verify_links(opportunities)

    print("Ranking...")

    opportunities = rank(opportunities)

    return opportunities


def run_scraper():

    data = scrape_all()

    df = pd.DataFrame(data)

    if len(df):

        df["scraped_at"] = datetime.now().strftime(
            "%d %b %Y %H:%M"
        )

        df.to_csv(
            "opportunities.csv",
            index=False
        )

    print(f"{len(df)} opportunities saved.")

    return df


if __name__ == "__main__":

    run_scraper()
