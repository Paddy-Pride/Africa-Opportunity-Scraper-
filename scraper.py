import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json
from datetime import datetime
import os

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

def extract_date(text):
    """Extract deadline from text using regex patterns"""
    if not text:
        return 'N/A'
    
    # Common date patterns
    patterns = [
        r'(?:deadline|closing date|application deadline|apply by)[:\s]*([^\.]+)',
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'(?:ends|closes)[:\s]*([^\.]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return clean_text(match.group(1))
    
    return 'N/A'

# ============ SOURCE 1: One Young World Scholarships ============
def scrape_oneyoungworld():
    """Scrapes scholarships from One Young World"""
    opportunities = []
    url = "https://www.oneyoungworld.com/scholarships"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find scholarship cards
            cards = soup.find_all('div', class_=re.compile(r'scholarship|card|item', re.I))
            
            for card in cards[:10]:
                # Title
                title_tag = card.find(['h2', 'h3', 'h4'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                # Link
                link_tag = card.find('a', href=True)
                if link_tag:
                    href = link_tag.get('href', '')
                    if href.startswith('/'):
                        link = 'https://www.oneyoungworld.com' + href
                    else:
                        link = href
                else:
                    link = 'N/A'
                
                # Description
                desc_tag = card.find(['p', 'div'], class_=re.compile(r'desc|body|excerpt', re.I))
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                # Extract deadline from description
                deadline = extract_date(description)
                
                if title != 'N/A' and link != 'N/A':
                    opportunities.append({
                        'title': f"One Young World: {title}",
                        'company': 'One Young World',
                        'description': description,
                        'posted_date': f"Deadline: {deadline}" if deadline != 'N/A' else 'Ongoing',
                        'job_page_url': link,
                        'original_apply_link': link,
                        'source': 'One Young World',
                        'type': 'Scholarship'
                    })
    except Exception as e:
        print(f"Error scraping One Young World: {e}")
    
    return opportunities

# ============ SOURCE 2: DAAD Scholarships ============
def scrape_daad():
    """Scrapes DAAD scholarships for Africa"""
    opportunities = []
    url = "https://www.daad.de/en/study-and-research-in-germany/scholarships/"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find scholarship entries
            entries = soup.find_all('li', class_=re.compile(r'scholarship|item|entry', re.I))
            
            for entry in entries[:10]:
                # Title
                title_tag = entry.find('a')
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                # Link
                if title_tag and title_tag.has_attr('href'):
                    href = title_tag.get('href', '')
                    if href.startswith('/'):
                        link = 'https://www.daad.de' + href
                    else:
                        link = href
                else:
                    link = 'N/A'
                
                # Description
                desc_tag = entry.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                # Extract deadline
                deadline = extract_date(description)
                
                if title != 'N/A' and link != 'N/A':
                    opportunities.append({
                        'title': f"DAAD: {title}",
                        'company': 'DAAD',
                        'description': description,
                        'posted_date': f"Deadline: {deadline}" if deadline != 'N/A' else 'Varies',
                        'job_page_url': link,
                        'original_apply_link': link,
                        'source': 'DAAD',
                        'type': 'Scholarship'
                    })
    except Exception as e:
        print(f"Error scraping DAAD: {e}")
    
    return opportunities

# ============ SOURCE 3: Mastercard Foundation ============
def scrape_mastercard():
    """Scrapes Mastercard Foundation opportunities"""
    opportunities = []
    url = "https://mastercardfdn.org/opportunities/"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find opportunity listings
            items = soup.find_all('article', class_=re.compile(r'post|item|opportunity', re.I))
            
            for item in items[:10]:
                # Title
                title_tag = item.find(['h2', 'h3'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                # Link
                link_tag = item.find('a', href=True)
                if link_tag:
                    href = link_tag.get('href', '')
                    if href.startswith('/'):
                        link = 'https://mastercardfdn.org' + href
                    else:
                        link = href
                else:
                    link = 'N/A'
                
                # Description
                desc_tag = item.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                # Extract deadline
                deadline = extract_date(description)
                
                if title != 'N/A' and link != 'N/A':
                    opportunities.append({
                        'title': f"Mastercard: {title}",
                        'company': 'Mastercard Foundation',
                        'description': description,
                        'posted_date': f"Deadline: {deadline}" if deadline != 'N/A' else 'Varies',
                        'job_page_url': link,
                        'original_apply_link': link,
                        'source': 'Mastercard Foundation',
                        'type': 'Scholarship'
                    })
    except Exception as e:
        print(f"Error scraping Mastercard Foundation: {e}")
    
    return opportunities

# ============ SOURCE 4: African Union Opportunities ============
def scrape_african_union():
    """Scrapes African Union opportunities"""
    opportunities = []
    url = "https://au.int/en/opportunities"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find opportunity listings
            items = soup.find_all('div', class_=re.compile(r'views-row|item|opportunity', re.I))
            
            for item in items[:10]:
                # Title
                title_tag = item.find('a')
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                # Link
                if title_tag and title_tag.has_attr('href'):
                    href = title_tag.get('href', '')
                    if href.startswith('/'):
                        link = 'https://au.int' + href
                    else:
                        link = href
                else:
                    link = 'N/A'
                
                # Description
                desc_tag = item.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                # Extract deadline
                deadline = extract_date(description)
                
                if title != 'N/A' and link != 'N/A':
                    opportunities.append({
                        'title': f"AU: {title}",
                        'company': 'African Union',
                        'description': description,
                        'posted_date': f"Deadline: {deadline}" if deadline != 'N/A' else 'Ongoing',
                        'job_page_url': link,
                        'original_apply_link': link,
                        'source': 'African Union',
                        'type': 'Fellowship'
                    })
    except Exception as e:
        print(f"Error scraping African Union: {e}")
    
    return opportunities

# ============ SOURCE 5: UNDP Opportunities ============
def scrape_undp():
    """Scrapes UNDP opportunities"""
    opportunities = []
    url = "https://www.undp.org/opportunities"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find opportunity listings
            items = soup.find_all('div', class_=re.compile(r'card|item|opportunity', re.I))
            
            for item in items[:10]:
                # Title
                title_tag = item.find(['h2', 'h3'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                # Link
                link_tag = item.find('a', href=True)
                if link_tag:
                    href = link_tag.get('href', '')
                    if href.startswith('/'):
                        link = 'https://www.undp.org' + href
                    else:
                        link = href
                else:
                    link = 'N/A'
                
                # Description
                desc_tag = item.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                # Extract deadline
                deadline = extract_date(description)
                
                # Determine type
                if 'grant' in (title + description).lower():
                    opp_type = 'Grant'
                elif 'fellowship' in (title + description).lower():
                    opp_type = 'Fellowship'
                elif 'internship' in (title + description).lower():
                    opp_type = 'Internship'
                else:
                    opp_type = 'Opportunity'
                
                if title != 'N/A' and link != 'N/A':
                    opportunities.append({
                        'title': f"UNDP: {title}",
                        'company': 'UNDP',
                        'description': description,
                        'posted_date': f"Deadline: {deadline}" if deadline != 'N/A' else 'Ongoing',
                        'job_page_url': link,
                        'original_apply_link': link,
                        'source': 'UNDP',
                        'type': opp_type
                    })
    except Exception as e:
        print(f"Error scraping UNDP: {e}")
    
    return opportunities

# ============ SOURCE 6: MyJobMag Internships ============
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
                    date_text = clean_text(date_tag.get_text()) if date_tag else 'N/A'
                    
                    company_tag = listing.find('h3')
                    company = clean_text(company_tag.get_text()) if company_tag else 'N/A'
                    
                    if title != 'N/A' and job_page_url != 'N/A':
                        internships.append({
                            'title': title,
                            'company': company,
                            'description': description,
                            'posted_date': date_text,
                            'job_page_url': job_page_url,
                            'original_apply_link': job_page_url,
                            'source': 'MyJobMag',
                            'type': 'Internship'
                        })
                time.sleep(2)
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            pass
    return internships

# ============ SOURCE 7: Remotive Remote Jobs ============
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

# ============ FILTER & DEDUPLICATE ============
def filter_africa_opportunities(jobs):
    keywords = ['africa', 'remote', 'worldwide', 'kenya', 'nigeria', 'ghana', 
                'uganda', 'tanzania', 'south africa', 'rwanda', 'ethiopia', 
                'zambia', 'zimbabwe', 'cameroon', 'senegal', 'botswana',
                'sub-saharan', 'west africa', 'east africa']
    filtered = []
    for job in jobs:
        text = str(job).lower()
        if any(kw in text for kw in keywords):
            filtered.append(job)
    return filtered

def deduplicate_opportunities(jobs):
    """Remove duplicates based on title and company"""
    seen = set()
    unique = []
    for job in jobs:
        key = f"{job['title']}|{job['company']}"
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique

# ============ MAIN SCRAPER ============
def run_scraper():
    all_opportunities = []
    
    print("Starting comprehensive opportunity scraper...")
    
    # Scrape all sources
    print("Scraping One Young World...")
    all_opportunities.extend(scrape_oneyoungworld())
    
    print("Scraping DAAD...")
    all_opportunities.extend(scrape_daad())
    
    print("Scraping Mastercard Foundation...")
    all_opportunities.extend(scrape_mastercard())
    
    print("Scraping African Union...")
    all_opportunities.extend(scrape_african_union())
    
    print("Scraping UNDP...")
    all_opportunities.extend(scrape_undp())
    
    print("Scraping MyJobMag...")
    all_opportunities.extend(scrape_myjobmag())
    
    print("Scraping Remotive...")
    all_opportunities.extend(scrape_remotive())
    
    print(f"Total found: {len(all_opportunities)}")
    
    # Filter for Africa
    africa_ops = filter_africa_opportunities(all_opportunities)
    print(f"After Africa filter: {len(africa_ops)}")
    
    # Deduplicate
    unique_ops = deduplicate_opportunities(africa_ops)
    print(f"After deduplication: {len(unique_ops)}")
    
    return unique_ops

if __name__ == '__main__':
    data = run_scraper()
    df = pd.DataFrame(data)
    df.to_csv('opportunities.csv', index=False)
    print(f"Saved {len(data)} opportunities to CSV")
