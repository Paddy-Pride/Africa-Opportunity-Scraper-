import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

def clean_text(text):
    if not text:
        return 'N/A'
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'style="[^"]*"', ' ', text)
    text = re.sub(r'class="[^"]*"', ' ', text)
    text = re.sub(r'id="[^"]*"', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\r', '').replace('\n', ' ').replace('\t', ' ')
    text = text.strip()
    return text if text else 'N/A'

def get_original_company_link(job_page_url):
    """
    Visit the job board's job page and extract the original company application link
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(job_page_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Look for "Apply" or "Apply on company website" button
            apply_links = soup.find_all('a', href=True)
            for link in apply_links:
                text = link.get_text().lower()
                href = link.get('href', '')
                
                if ('apply' in text or 'apply' in href.lower() or 'external' in href.lower()):
                    if href.startswith('http'):
                        return href
                    elif href.startswith('/'):
                        return 'https://www.myjobmag.co.ke' + href
            
            # Method 2: Look for the "Apply" button with specific classes
            apply_buttons = soup.find_all('a', class_=re.compile(r'apply|btn-apply|job-apply|apply-now', re.I))
            for btn in apply_buttons:
                href = btn.get('href', '')
                if href and href.startswith('http'):
                    return href
                elif href and href.startswith('/'):
                    return 'https://www.myjobmag.co.ke' + href
            
            # Method 3: Look for iframe or external link in onclick
            apply_elements = soup.find_all(['a', 'button'], onclick=True)
            for elem in apply_elements:
                onclick = elem.get('onclick', '')
                match = re.search(r"window\.location=['\"]([^'\"]+)['\"]", onclick)
                if match:
                    return match.group(1)
                
                match = re.search(r"['\"]https?://[^'\"]+['\"]", onclick)
                if match:
                    return match.group(1).strip("'\"")
            
            # Method 4: Look for direct external links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith('http'):
                    if 'myjobmag' not in href.lower() and 'remotive' not in href.lower():
                        if any(domain in href.lower() for domain in ['.com', '.org', '.io', '.co', '.uk', '.de', '.fr']):
                            if any(keyword in href.lower() for keyword in ['apply', 'job', 'career', 'position', 'opportunity']):
                                return href
            
            return 'N/A'
        else:
            return 'N/A'
    except Exception as e:
        print(f"Error getting original link from {job_page_url}: {e}")
        return 'N/A'

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
                    a_tag = listing.find('a')
                    if not a_tag:
                        continue
                    
                    href = a_tag.get('href', '')
                    if href:
                        if href.startswith('/'):
                            job_page_url = base_url + href
                        else:
                            job_page_url = href
                    else:
                        job_page_url = 'N/A'
                    
                    title = clean_text(a_tag.get_text())
                    
                    desc_tag = listing.find('li', class_='job-desc')
                    description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                    
                    date_tag = listing.find('li', id='job-date')
                    posted_date = clean_text(date_tag.get_text()) if date_tag else 'N/A'
                    
                    company_tag = listing.find('h3')
                    company = clean_text(company_tag.get_text()) if company_tag else 'N/A'
                    
                    if title != 'N/A' and job_page_url != 'N/A':
                        original_link = get_original_company_link(job_page_url)
                        final_link = original_link if original_link != 'N/A' else job_page_url
                        
                        internships.append({
                            'title': title,
                            'company': company,
                            'description': description,
                            'posted_date': posted_date,
                            'job_page_url': job_page_url,
                            'original_apply_link': final_link,
                            'source': 'MyJobMag',
                            'type': 'Internship'
                        })
                        
                        time.sleep(1)
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
                desc = job.get('description', 'N/A')
                if desc != 'N/A':
                    desc = re.sub(r'<[^>]+>', ' ', desc)
                    desc = re.sub(r'\s+', ' ', desc).strip()
                else:
                    desc = 'N/A'
                
                original_link = job.get('url', '#')
                
                jobs.append({
                    'title': job.get('title', 'N/A'),
                    'company': job.get('company_name', 'N/A'),
                    'description': desc[:500] if desc != 'N/A' else 'N/A',
                    'posted_date': job.get('publication_date', 'N/A'),
                    'job_page_url': original_link,
                    'original_apply_link': original_link,
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
            'posted_date': 'Open: Ongoing | Deadline: 1 March 2026',
            'job_page_url': 'https://au.int/en',
            'original_apply_link': 'https://au.int/en',
            'source': 'Curated',
            'type': 'Fellowship'
        },
        {
            'title': 'Mastercard Foundation Scholars Program',
            'company': 'Mastercard Foundation',
            'description': 'Full scholarship for African students to study at partner universities across Africa and globally.',
            'posted_date': 'Open: Varies by institution | Deadline: Varies by institution',
            'job_page_url': 'https://mastercardfdn.org',
            'original_apply_link': 'https://mastercardfdn.org',
            'source': 'Curated',
            'type': 'Scholarship'
        },
        {
            'title': 'DAAD Scholarships for Africa',
            'company': 'DAAD',
            'description': 'Study funding for African students pursuing Masters and PhD programs in Germany.',
            'posted_date': 'Open: Varies by program | Deadline: Varies by program',
            'job_page_url': 'https://www.daad.de',
            'original_apply_link': 'https://www.daad.de',
            'source': 'Curated',
            'type': 'Scholarship'
        },
        {
            'title': 'Yoma Youth Opportunities Platform',
            'company': 'UNICEF and Generation Unlimited',
            'description': 'Free platform providing access to skilling, earning, and impact opportunities for young Africans.',
            'posted_date': 'Open: Ongoing | Deadline: Ongoing',
            'job_page_url': 'https://yoma.world',
            'original_apply_link': 'https://yoma.world',
            'source': 'Curated',
            'type': 'Various'
        },
        {
            'title': 'Africa Green Growth Fellowship',
            'company': 'AGGF',
            'description': 'Fellowship program with stipend for African youth working on environmental and sustainability initiatives.',
            'posted_date': 'Open: Varies | Deadline: Varies',
            'job_page_url': 'https://www.aggf.org',
            'original_apply_link': 'https://www.aggf.org',
            'source': 'Curated',
            'type': 'Fellowship'
        },
        {
            'title': 'Commonwealth Scholarships',
            'company': 'UK Government',
            'description': 'Full funding for Masters and PhD students from Commonwealth countries including many African nations.',
            'posted_date': 'Open: Varies | Deadline: Varies',
            'job_page_url': 'https://cscuk.fcdo.gov.uk',
            'original_apply_link': 'https://cscuk.fcdo.gov.uk',
            'source': 'Curated',
            'type': 'Scholarship'
        },
        {
            'title': 'New Leaders Lab - AEYA',
            'company': 'AEYA',
            'description': 'Free 3-4 month leadership program focused on entrepreneurship, civic engagement, and community development.',
            'posted_date': 'Open: Ongoing | Deadline: 19 July 2026',
            'job_page_url': 'https://aeya.org',
            'original_apply_link': 'https://aeya.org',
            'source': 'Curated',
            'type': 'Program'
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
    print("Scraping MyJobMag and extracting original company links...")
    internships = scrape_myjobmag()
    print(f"Found {len(internships)} internships with original links")
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
