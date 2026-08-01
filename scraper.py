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

def extract_deadline(text):
    if not text:
        return 'N/A'
    patterns = [
        r'(?:deadline|closing date|application deadline|apply by)[:\s]*([^\.]+)',
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return clean_text(match.group(1))
    return 'N/A'

def extract_eligibility(text):
    if not text:
        return 'N/A'
    patterns = [
        r'(?:eligibility|qualifications|requirements|criteria)[:\s]*([^.]+[.])',
        r'(?:you are eligible|you qualify|must be|should have)[:\s]*([^.]+[.])',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return clean_text(match.group(1))
    return 'N/A'

def extract_benefits(text):
    if not text:
        return 'N/A'
    patterns = [
        r'(?:benefits|includes|what you get|funding|coverage)[:\s]*([^.]+[.])',
        r'(?:tuition|stipend|travel|allowance|salary)[:\s]*([^.]+[.])',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return clean_text(match.group(1))
    return 'N/A'

# ============ SOURCE 1: One Young World Scholarships ============
def scrape_oneyoungworld():
    opportunities = []
    url = "https://www.oneyoungworld.com/scholarships"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            cards = soup.find_all('div', class_=re.compile(r'scholarship|card|item', re.I))
            
            for card in cards[:15]:
                # Get link FIRST
                link_tag = card.find('a', href=True)
                link = 'N/A'
                if link_tag:
                    href = link_tag.get('href', '')
                    if href:
                        if href.startswith('/'):
                            link = 'https://www.oneyoungworld.com' + href
                        elif href.startswith('http'):
                            link = href
                        else:
                            link = 'https://www.oneyoungworld.com/' + href
                
                # Get title
                title_tag = card.find(['h2', 'h3', 'h4'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                # Get description
                desc_tag = card.find(['p', 'div'], class_=re.compile(r'desc|body|excerpt', re.I))
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                # Extract details
                deadline = extract_deadline(description + title)
                eligibility = extract_eligibility(description)
                benefits = extract_benefits(description)
                
                opp_type = 'Scholarship'
                if 'fellowship' in (title + description).lower():
                    opp_type = 'Fellowship'
                elif 'grant' in (title + description).lower():
                    opp_type = 'Grant'
                
                if title != 'N/A' and link != 'N/A' and link != '#':
                    opportunities.append({
                        'title': title,
                        'organization': 'One Young World',
                        'description': description[:500],
                        'deadline': deadline,
                        'eligibility': eligibility[:300],
                        'benefits': benefits[:300],
                        'link': link,
                        'source': 'One Young World',
                        'type': opp_type,
                        'target_audience': 'African youth',
                        'funding_level': 'Fully Funded' if 'fully' in (benefits + description).lower() else 'Varies'
                    })
    except Exception as e:
        print(f"Error scraping One Young World: {e}")
    
    return opportunities

# ============ SOURCE 2: DAAD Scholarships ============
def scrape_daad():
    opportunities = []
    url = "https://www.daad.de/en/study-and-research-in-germany/scholarships/"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            entries = soup.find_all('li', class_=re.compile(r'scholarship|item|entry', re.I))
            
            for entry in entries[:15]:
                # Get link FIRST
                link_tag = entry.find('a', href=True)
                link = 'N/A'
                if link_tag:
                    href = link_tag.get('href', '')
                    if href:
                        if href.startswith('/'):
                            link = 'https://www.daad.de' + href
                        elif href.startswith('http'):
                            link = href
                        else:
                            link = 'https://www.daad.de/' + href
                
                # Get title
                title = clean_text(link_tag.get_text()) if link_tag else 'N/A'
                
                # Get description
                desc_tag = entry.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                deadline = extract_deadline(description + title)
                eligibility = extract_eligibility(description)
                benefits = extract_benefits(description)
                
                if title != 'N/A' and link != 'N/A' and link != '#':
                    opportunities.append({
                        'title': title,
                        'organization': 'DAAD',
                        'description': description[:500],
                        'deadline': deadline,
                        'eligibility': eligibility[:300],
                        'benefits': benefits[:300],
                        'link': link,
                        'source': 'DAAD',
                        'type': 'Scholarship',
                        'target_audience': 'African students',
                        'funding_level': 'Fully Funded' if 'fully' in (benefits + description).lower() else 'Partial'
                    })
    except Exception as e:
        print(f"Error scraping DAAD: {e}")
    
    return opportunities

# ============ SOURCE 3: Mastercard Foundation ============
def scrape_mastercard():
    opportunities = []
    url = "https://mastercardfdn.org/opportunities/"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('article', class_=re.compile(r'post|item|opportunity', re.I))
            
            for item in items[:10]:
                # Get link FIRST
                link_tag = item.find('a', href=True)
                link = 'N/A'
                if link_tag:
                    href = link_tag.get('href', '')
                    if href:
                        if href.startswith('/'):
                            link = 'https://mastercardfdn.org' + href
                        elif href.startswith('http'):
                            link = href
                        else:
                            link = 'https://mastercardfdn.org/' + href
                
                # Get title
                title_tag = item.find(['h2', 'h3'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                # Get description
                desc_tag = item.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                deadline = extract_deadline(description + title)
                eligibility = extract_eligibility(description)
                benefits = extract_benefits(description)
                
                if title != 'N/A' and link != 'N/A' and link != '#':
                    opportunities.append({
                        'title': title,
                        'organization': 'Mastercard Foundation',
                        'description': description[:500],
                        'deadline': deadline,
                        'eligibility': eligibility[:300],
                        'benefits': benefits[:300],
                        'link': link,
                        'source': 'Mastercard Foundation',
                        'type': 'Scholarship',
                        'target_audience': 'African youth',
                        'funding_level': 'Fully Funded' if 'fully' in (benefits + description).lower() else 'Varies'
                    })
    except Exception as e:
        print(f"Error scraping Mastercard Foundation: {e}")
    
    return opportunities

# ============ SOURCE 4: African Union ============
def scrape_african_union():
    opportunities = []
    url = "https://au.int/en/opportunities"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('div', class_=re.compile(r'views-row|item|opportunity', re.I))
            
            for item in items[:10]:
                # Get link FIRST
                link_tag = item.find('a', href=True)
                link = 'N/A'
                if link_tag:
                    href = link_tag.get('href', '')
                    if href:
                        if href.startswith('/'):
                            link = 'https://au.int' + href
                        elif href.startswith('http'):
                            link = href
                        else:
                            link = 'https://au.int/' + href
                
                # Get title
                title = clean_text(link_tag.get_text()) if link_tag else 'N/A'
                
                # Get description
                desc_tag = item.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                deadline = extract_deadline(description + title)
                eligibility = extract_eligibility(description)
                benefits = extract_benefits(description)
                
                if title != 'N/A' and link != 'N/A' and link != '#':
                    opportunities.append({
                        'title': title,
                        'organization': 'African Union',
                        'description': description[:500],
                        'deadline': deadline,
                        'eligibility': eligibility[:300],
                        'benefits': benefits[:300],
                        'link': link,
                        'source': 'African Union',
                        'type': 'Fellowship',
                        'target_audience': 'African youth',
                        'funding_level': 'Fully Funded' if 'fully' in (benefits + description).lower() else 'Varies'
                    })
    except Exception as e:
        print(f"Error scraping African Union: {e}")
    
    return opportunities

# ============ SOURCE 5: UNDP ============
def scrape_undp():
    opportunities = []
    url = "https://www.undp.org/opportunities"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('div', class_=re.compile(r'card|item|opportunity', re.I))
            
            for item in items[:10]:
                # Get link FIRST
                link_tag = item.find('a', href=True)
                link = 'N/A'
                if link_tag:
                    href = link_tag.get('href', '')
                    if href:
                        if href.startswith('/'):
                            link = 'https://www.undp.org' + href
                        elif href.startswith('http'):
                            link = href
                        else:
                            link = 'https://www.undp.org/' + href
                
                # Get title
                title_tag = item.find(['h2', 'h3'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                # Get description
                desc_tag = item.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                deadline = extract_deadline(description + title)
                eligibility = extract_eligibility(description)
                benefits = extract_benefits(description)
                
                opp_type = 'Opportunity'
                if 'grant' in (title + description).lower():
                    opp_type = 'Grant'
                elif 'fellowship' in (title + description).lower():
                    opp_type = 'Fellowship'
                elif 'internship' in (title + description).lower():
                    opp_type = 'Internship'
                
                if title != 'N/A' and link != 'N/A' and link != '#':
                    opportunities.append({
                        'title': title,
                        'organization': 'UNDP',
                        'description': description[:500],
                        'deadline': deadline,
                        'eligibility': eligibility[:300],
                        'benefits': benefits[:300],
                        'link': link,
                        'source': 'UNDP',
                        'type': opp_type,
                        'target_audience': 'African youth',
                        'funding_level': 'Fully Funded' if 'fully' in (benefits + description).lower() else 'Varies'
                    })
    except Exception as e:
        print(f"Error scraping UNDP: {e}")
    
    return opportunities

# ============ FILTERS ============
def filter_africa_opportunities(opportunities):
    keywords = ['africa', 'african', 'kenya', 'nigeria', 'ghana', 'uganda', 
                'tanzania', 'south africa', 'rwanda', 'ethiopia', 'zambia',
                'zimbabwe', 'cameroon', 'senegal', 'botswana', 'sub-saharan',
                'west africa', 'east africa', 'southern africa']
    filtered = []
    for opp in opportunities:
        text = str(opp).lower()
        if any(kw in text for kw in keywords):
            filtered.append(opp)
    return filtered

def filter_active_opportunities(opportunities):
    active = []
    for opp in opportunities:
        deadline = opp.get('deadline', '')
        if deadline:
            deadline_lower = deadline.lower()
            if 'ongoing' in deadline_lower:
                active.append(opp)
            elif 'vari' in deadline_lower:
                active.append(opp)
            elif 'rolling' in deadline_lower:
                active.append(opp)
            elif deadline != 'N/A':
                active.append(opp)
        else:
            active.append(opp)
    return active

# ============ MAIN ============
def run_scraper():
    all_opportunities = []
    
    print("Starting comprehensive opportunity scraper...")
    
    # Existing sources
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
    
    # NEW SOURCES
    print("Scraping UNDP Youth Co-Creators Council...")
    all_opportunities.extend(scrape_undp_youth_council())
    
    print("Scraping AU Digital & Innovation Fellowship...")
    all_opportunities.extend(scrape_au_digital_fellowship())
    
    print("Scraping EAC Student Mobility Scholarship...")
    all_opportunities.extend(scrape_eac_scholarship())
    
    print("Scraping UNDP timbuktoo EdTech...")
    all_opportunities.extend(scrape_timbuktoo_edtech())
    
    print("Scraping New Leaders Lab...")
    all_opportunities.extend(scrape_new_leaders_lab())
    
    print("Scraping Africa CDC Fellowship...")
    all_opportunities.extend(scrape_africa_cdc_fellowship())
    
    print("Scraping World Bank Fellowship...")
    all_opportunities.extend(scrape_world_bank_fellowship())
    
    print("Scraping Africa Fundraising Incubator...")
    all_opportunities.extend(scrape_fundraising_incubator())
    
    print("Scraping Mastercard Scholars...")
    all_opportunities.extend(scrape_mastercard_scholars())
    
    print("Scraping Code for Africa...")
    all_opportunities.extend(scrape_code_for_africa())
    
    print(f"Total found: {len(all_opportunities)}")
    
    # Filter for Africa
    africa_ops = filter_africa_opportunities(all_opportunities)
    print(f"After Africa filter: {len(africa_ops)}")
    
    # Filter for active opportunities
    active_ops = filter_active_opportunities(africa_ops)
    print(f"After active filter: {len(active_ops)}")
    
    return active_ops
