import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

def clean_text(text):
    if not text:
        return 'N/A'
    text = text.replace('\r', '').replace('\n', ' ').replace('\t', ' ')
    text = ' '.join(text.split())
    return text.strip()

def scrape_myjobmag():
    internships = []
    base_url = "https://www.myjobmag.co.ke"
    
    for page in range(1, 6):
        url = f"{base_url}/jobs-in-kenya?q=Internship&currentpage={page}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                listings = soup.find_all('li', class_='job-list-li')
                
                for listing in listings:
                    title_tag = listing.find('h2')
                    title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                    
                    a_tag = listing.find('a')
                    if a_tag and a_tag.has_attr('href'):
                        link = base_url + a_tag['href'] if a_tag['href'].startswith('/') else a_tag['href']
                    else:
                        link = 'N/A'
                    
                    desc_tag = listing.find('li', class_='job-desc')
                    description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                    
                    date_tag = listing.find('li', id='job-date')
                    posted_date = clean_text(date_tag.get_text()) if date_tag else 'N/A'
                    
                    if title != 'N/A' and link != 'N/A':
                        internships.append({
                            'title': title,
                            'description': description,
                            'posted_date': posted_date,
                            'link': link,
                            'source': 'MyJobMag',
                            'type': 'Internship'
                        })
                time.sleep(2)
        except:
            pass
    return internships

def scrape_remotive():
    jobs = []
    try:
        url = "https://remotive.com/api/remote-jobs"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            for job in data.get('jobs', [])[:50]:
                jobs.append({
                    'title': job.get('title', 'N/A'),
                    'company': job.get('company_name', 'N/A'),
                    'description': job.get('description', 'N/A')[:500],
                    'posted_date': job.get('publication_date', 'N/A'),
                    'link': job.get('url', '#'),
                    'source': 'Remotive',
                    'type': 'Remote Job'
                })
    except:
        pass
    return jobs

def scrape_scholarships():
    return [
        {'title': 'AU Digital & Innovation Fellowship', 'company': 'African Union', 'description': '12-month immersion program for AU citizens under 35', 'posted_date': 'Deadline: March 2026', 'link': 'https://au.int/en', 'source': 'Curated', 'type': 'Fellowship'},
        {'title': 'Mastercard Foundation Scholars Program', 'company': 'Mastercard Foundation', 'description': 'Full scholarship for African students', 'posted_date': 'Deadline: Varies', 'link': 'https://mastercardfdn.org', 'source': 'Curated', 'type': 'Scholarship'},
        {'title': 'DAAD Scholarships for Africa', 'company': 'DAAD', 'description': 'Study funding for African students in Germany', 'posted_date': 'Deadline: Varies', 'link': 'https://www.daad.de', 'source': 'Curated', 'type': 'Scholarship'},
        {'title': 'Yoma Platform - Youth Opportunities', 'company': 'UNICEF', 'description': 'Free platform for African youth opportunities', 'posted_date': 'Ongoing', 'link': 'https://yoma.world', 'source': 'Curated', 'type': 'Various'},
        {'title': 'Africa Green Growth Fellowship', 'company': 'AGGF', 'description': 'Fellowship with stipend for African youth', 'posted_date': 'Deadline: Varies', 'link': 'https://www.aggf.org', 'source': 'Curated', 'type': 'Fellowship'},
        {'title': 'Commonwealth Scholarships', 'company': 'UK Government', 'description': 'Full funding for Commonwealth country students', 'posted_date': 'Deadline: Varies', 'link': 'https://cscuk.fcdo.gov.uk', 'source': 'Curated', 'type': 'Scholarship'},
        {'title': 'New Leaders Lab - AEYA', 'company': 'AEYA', 'description': 'Free leadership and entrepreneurship program', 'posted_date': 'Deadline: July 2026', 'link': 'https://aeya.org', 'source': 'Curated', 'type': 'Program'}
    ]

def filter_africa_opportunities(jobs):
    keywords = ['africa', 'remote', 'worldwide', 'kenya', 'nigeria', 'ghana', 'uganda', 'tanzania', 'south africa', 'rwanda', 'ethiopia']
    filtered = []
    for job in jobs:
        text = str(job).lower()
        if any(kw in text for kw in keywords):
            filtered.append(job)
    return filtered

def run_scraper():
    internships = scrape_myjobmag()
    remote_jobs = scrape_remotive()
    curated = scrape_scholarships()
    all_ops = internships + remote_jobs + curated
    africa_ops = filter_africa_opportunities(all_ops)
    return africa_ops

if __name__ == '__main__':
    data = run_scraper()
    df = pd.DataFrame(data)
    df.to_csv('opportunities.csv', index=False)
    print(f"Saved {len(data)} opportunities")
