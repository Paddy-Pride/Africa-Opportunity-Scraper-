import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

def clean_text(text):
    if not text:
        return 'N/A'
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\r', '').replace('\n', ' ').replace('\t', ' ')
    text = text.strip()
    return text if text else 'N/A'

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
                    # Get title and direct link
                    a_tag = listing.find('a')
                    if not a_tag:
                        continue
                    
                    title = clean_text(a_tag.get_text())
                    if a_tag.has_attr('href'):
                        if a_tag['href'].startswith('/'):
                            link = base_url + a_tag['href']
                        else:
                            link = a_tag['href']
                    else:
                        link = 'N/A'
                    
                    # Get description
                    desc_tag = listing.find('li', class_='job-desc')
                    description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                    
                    # Get date
                    date_tag = listing.find('li', id='job-date')
                    posted_date = clean_text(date_tag.get_text()) if date_tag else 'N/A'
                    
                    # Get company
                    company_tag = listing.find('h3')
                    company = clean_text(company_tag.get_text()) if company_tag else 'N/A'
                    
                    if title != 'N/A' and link != 'N/A':
                        internships.append({
                            'title': title,
                            'company': company,
                            'description': description,
                            'posted_date': posted_date,
                            'link': link,
                            'source': 'MyJobMag',
                            'type': 'Internship'
                        })
                time.sleep(2)
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
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
                # Clean description
                desc = job.get('description', 'N/A')
                desc = re.sub(r'<[^>]+>', '', desc)
                desc = re.sub(r'\s+', ' ', desc).strip()
                
                jobs.append({
                    'title': job.get('title', 'N/A'),
                    'company': job.get('company_name', 'N/A'),
                    'description': desc[:500] if desc != 'N/A' else 'N/A',
                    'posted_date': job.get('publication_date', 'N/A'),
                    'link': job.get('url', '#'),
                    'source': 'Remotive',
                    'type': 'Remote Job'
                })
    except Exception as e:
        print(f"Remotive API error: {e}")
    return jobs

def scrape_scholarships():
    return [
        {
            'title': 'AU Digital and Innovation Fellowship Cohort 3',
            'company': 'African Union',
            'description': '12-month immersive program for Africas top technical minds to co-develop solutions within AU institutions. Financial support and international exposure provided.',
            'posted_date': 'Deadline: 1 March 2026',
            'link': 'https://au.int/en',
            'source': 'Curated',
            'type': 'Fellowship'
        },
        {
            'title': 'Mastercard Foundation Scholars Program',
            'company': 'Mastercard Foundation',
            'description': 'Full scholarship for African students to study at partner universities across Africa and globally.',
            'posted_date': 'Deadline: Varies by institution',
            'link': 'https://mastercardfdn.org',
            'source': 'Curated',
            'type': 'Scholarship'
        },
        {
            'title': 'DAAD Scholarships for Africa',
            'company': 'DAAD',
            'description': 'Study funding for African students pursuing Masters and PhD programs in Germany.',
            'posted_date': 'Deadline: Varies by program',
            'link': 'https://www.daad.de',
            'source': 'Curated',
            'type': 'Scholarship'
        },
        {
            'title': 'Yoma Youth Opportunities Platform',
            'company': 'UNICEF and Generation Unlimited',
            'description': 'Free platform providing access to skilling, earning, and impact opportunities for young Africans.',
            'posted_date': 'Ongoing',
            'link': 'https://yoma.world',
            'source': 'Curated',
            'type': 'Various'
        },
        {
            'title': 'Africa Green Growth Fellowship',
            'company': 'AGGF',
            'description': 'Fellowship program with stipend for African youth working on environmental and sustainability initiatives.',
            'posted_date': 'Deadline: Varies',
            'link': 'https://www.aggf.org',
            'source': 'Curated',
            'type': 'Fellowship'
        },
        {
            'title': 'Commonwealth Scholarships',
            'company': 'UK Government',
            'description': 'Full funding for Masters and PhD students from Commonwealth countries including many African nations.',
            'posted_date': 'Deadline: Varies',
            'link': 'https://cscuk.fcdo.gov.uk',
            'source': 'Curated',
            'type': 'Scholarship'
        },
        {
            'title': 'New Leaders Lab - AEYA',
            'company': 'AEYA',
            'description': 'Free 3-4 month leadership program focused on entrepreneurship, civic engagement, and community development.',
            'posted_date': 'Deadline: 19 July 2026',
            'link': 'https://aeya.org',
            'source': 'Curated',
            'type': 'Program'
        },
        {
            'title': 'NextGen Africa Workforce Fellowship',
            'company': 'NextGen Africa',
            'description': 'Online U.S.-accredited Bachelor of Business Administration with mentorship from African leaders.',
            'posted_date': 'Ongoing',
            'link': 'https://nextgenafrica.org',
            'source': 'Curated',
            'type': 'Fellowship'
        },
        {
            'title': 'Loughborough University Creating Better Futures Scholarship',
            'company': 'Loughborough University',
            'description': 'GBP 6,000 tuition fee discount for African students starting masters program in September 2026.',
            'posted_date': 'Deadline: Automatic with offer',
            'link': 'https://www.lboro.ac.uk',
            'source': 'Curated',
            'type': 'Scholarship'
        },
        {
            'title': 'QUT International Talent Scholarship',
            'company': 'QUT',
            'description': '20 percent tuition fee scholarship for undergraduate and postgraduate students from eligible African countries.',
            'posted_date': 'Ongoing',
            'link': 'https://www.qut.edu.au',
            'source': 'Curated',
            'type': 'Scholarship'
        }
    ]

def filter_africa_opportunities(jobs):
    keywords = ['africa', 'remote', 'worldwide', 'kenya', 'nigeria', 'ghana', 
                'uganda', 'tanzania', 'south africa', 'rwanda', 'ethiopia', 
                'zambia', 'zimbabwe', 'cameroon', 'senegal', 'botswana']
    filtered = []
    for job in jobs:
        text = str(job).lower()
        if any(kw in text for kw in keywords):
            filtered.append(job)
    return filtered

def run_scraper():
    print("Starting scraper...")
    internships = scrape_myjobmag()
    print(f"Found {len(internships)} internships")
    remote_jobs = scrape_remotive()
    print(f"Found {len(remote_jobs)} remote jobs")
    curated = scrape_scholarships()
    print(f"Loaded {len(curated)} curated opportunities")
    all_ops = internships + remote_jobs + curated
    africa_ops = filter_africa_opportunities(all_ops)
    print(f"Total Africa-relevant: {len(africa_ops)}")
    return africa_ops

if __name__ == '__main__':
    data = run_scraper()
    df = pd.DataFrame(data)
    df.to_csv('opportunities.csv', index=False)
    print(f"Saved {len(data)} opportunities to CSV")
