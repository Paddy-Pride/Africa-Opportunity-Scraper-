import requests
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse
import concurrent.futures

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

RSS_FEEDS = [
    "https://opportunitydesk.org/feed/",
    "https://www.opportunitiesforafricans.com/feed/",
    "https://youthopportunitieshub.com/feed/"
]

KEYWORDS = [
    "africa","african","uganda","kenya","rwanda","tanzania",
    "student","youth","scholarship","internship","grant",
    "fellowship","competition","leadership"
]

def clean(text):
    if not text:
        return ""
    return " ".join(str(text).split())

def parse_deadline(text):
    try:
        return parse(text, fuzzy=True)
    except:
        return None

def is_active(deadline):
    if deadline is None:
        return True
    return deadline >= datetime.now()

def verify_link(url):
    try:
        r = requests.head(url, timeout=8, allow_redirects=True, headers=HEADERS)
        return r.status_code == 200
    except:
        return False

def scrape_feed(feed_url):
    opportunities = []

    try:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:

            title = clean(entry.get("title", ""))
            description = BeautifulSoup(
                entry.get("summary", ""),
                "html.parser"
            ).get_text(" ")

            link = entry.get("link", "")

            deadline = "Rolling"

            if hasattr(entry, "published"):
                d = parse_deadline(entry.published)
                if d:
                    deadline = d.strftime("%d %b %Y")

            opportunities.append({
                "title": title,
                "organization": feed.feed.get("title", "Unknown"),
                "description": description[:600],
                "deadline": deadline,
                "link": link,
                "source": feed_url,
                "type": "Opportunity"
            })

    except Exception as e:
        print(f"RSS Error: {feed_url} -> {e}")

    return opportunities


def scrape_page(url):

    results = []

    try:

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        soup = BeautifulSoup(r.text, "lxml")

        for a in soup.find_all("a", href=True):

            href = a["href"]

            if not href.startswith("http"):
                continue

            title = clean(a.get_text())

            if len(title) < 8:
                continue

            text = (title + " " + href).lower()

            if not any(k in text for k in KEYWORDS):
                continue

            results.append({

                "title": title,
                "organization": url.split("/")[2],
                "description": "",
                "deadline": "Rolling",
                "link": href,
                "source": url,
                "type": "Opportunity"

            })

    except Exception as e:

        print(f"Website Error: {url} -> {e}")

    return results

def remove_duplicates(data):

    seen = set()
    cleaned = []

    for item in data:

        key = (
            item["title"].strip().lower(),
            item["link"].strip().lower()
        )

        if key not in seen:
            seen.add(key)
            cleaned.append(item)

    return cleaned


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
            continue

        d = parse_deadline(item["deadline"])

        if is_active(d):
            active.append(item)

    return active


def verify_all_links(data):

    verified = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:

        futures = {
            executor.submit(
                verify_link,
                item["link"]
            ): item for item in data
        }

        for future in concurrent.futures.as_completed(futures):

            item = futures[future]

            try:
                if future.result():
                    verified.append(item)
            except:
                pass

    return verified


def run_scraper():

    opportunities = []

    print("Reading RSS feeds...")

    for feed in RSS_FEEDS:
        opportunities.extend(scrape_feed(feed))

    print("Scanning websites...")

    websites = [

        "https://www.mastercardfdn.org/",
        "https://www.oneyoungworld.com/",
        "https://au.int/",
        "https://www.undp.org/",
        "https://opportunitydesk.org/",
        "https://www.opportunitiesforafricans.com/",
        "https://youthopportunitieshub.com/"

    ]

    for site in websites:
        opportunities.extend(scrape_page(site))

    opportunities = remove_duplicates(opportunities)

    opportunities = filter_relevant(opportunities)

    opportunities = filter_active(opportunities)

    opportunities = verify_all_links(opportunities)

    for item in opportunities:

        score = 0

        text = (
            item["title"] + " " +
            item["description"]
        ).lower()

        if "fully funded" in text:
            score += 10

        if "uganda" in text:
            score += 5

        if "africa" in text:
            score += 3

        score += sum(
            1 for k in KEYWORDS if k in text
        )

        item["score"] = score

    opportunities.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    df = pd.DataFrame(opportunities)

    if not df.empty:

        df["scraped_at"] = datetime.now().strftime(
            "%d %b %Y %H:%M"
        )

        df.to_csv(
            "opportunities.csv",
            index=False
        )

    print(f"Saved {len(df)} opportunities.")

    return df


if __name__ == "__main__":
    run_scraper()
