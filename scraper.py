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
    """Extract deadline from text"""
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
    """Extract eligibility criteria from text"""
    if not text:
        return 'N/A'
    
    # Look for eligibility sections
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
    """Extract benefits/funding from text"""
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
            
            for card in cards[:15]:
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
                
                # Extract details
                deadline = extract_deadline(description + title)
                eligibility = extract_eligibility(description)
                benefits = extract_benefits(description)
                
                # Determine type
                opp_type = 'Scholarship'
                if 'fellowship' in (title + description).lower():
                    opp_type = 'Fellowship'
                elif 'grant' in (title + description).lower():
                    opp_type = 'Grant'
                
                if title != 'N/A' and link != 'N/A':
                    opportunities.append({
                        'title': f"One Young World: {title}",
                        'organization': 'One Young World',
                        'description': description[:500],
                        'deadline': deadline,
                        'eligibility': eligibility[:200],
                        'benefits': benefits[:200],
                        'link': link,
                        'source': 'One Young World',
                        'type': opp_type,
                        'eligibility_criteria': eligibility,
                        'funding_level': benefits
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
            
            entries = soup.find_all('li', class_=re.compile(r'scholarship|item|entry', re.I))
            
            for entry in entries[:15]:
                title_tag = entry.find('a')
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                if title_tag and title_tag.has_attr('href'):
                    href = title_tag.get('href', '')
                    if href.startswith('/'):
                        link = 'https://www.daad.de' + href
                    else:
                        link = href
                else:
                    link = 'N/A'
                
                desc_tag = entry.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                deadline = extract_deadline(description + title)
                eligibility = extract_eligibility(description)
                benefits = extract_benefits(description)
                
                if title != 'N/A' and link != 'N/A':
                    opportunities.append({
                        'title': f"DAAD: {title}",
                        'organization': 'DAAD',
                        'description': description[:500],
                        'deadline': deadline,
                        'eligibility': eligibility[:200],
                        'benefits': benefits[:200],
                        'link': link,
                        'source': 'DAAD',
                        'type': 'Scholarship',
                        'eligibility_criteria': eligibility,
                        'funding_level': benefits
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
            
            items = soup.find_all('article', class_=re.compile(r'post|item|opportunity', re.I))
            
            for item in items[:10]:
                title_tag = item.find(['h2', 'h3'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                link_tag = item.find('a', href=True)
                if link_tag:
                    href = link_tag.get('href', '')
                    if href.startswith('/'):
                        link = 'https://mastercardfdn.org' + href
                    else:
                        link = href
                else:
                    link = 'N/A'
                
                desc_tag = item.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                deadline = extract_deadline(description + title)
                eligibility = extract_eligibility(description)
                benefits = extract_benefits(description)
                
                if title != 'N/A' and link != 'N/A':
                    opportunities.append({
                        'title': f"Mastercard: {title}",
                        'organization': 'Mastercard Foundation',
                        'description': description[:500],
                        'deadline': deadline,
                        'eligibility': eligibility[:200],
                        'benefits': benefits[:200],
                        'link': link,
                        'source': 'Mastercard Foundation',
                        'type': 'Scholarship',
                        'eligibility_criteria': eligibility,
                        'funding_level': benefits
                    })
    except Exception as e:
        print(f"Error scraping Mastercard Foundation: {e}")
    
    return opportunities

# ============ SOURCE 4: UNDP Opportunities ============
def scrape_undp():
    """Scrapes UNDP opportunities"""
    opportunities = []
    url = "https://www.undp.org/opportunities"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            items = soup.find_all('div', class_=re.compile(r'card|item|opportunity', re.I))
            
            for item in items[:10]:
                title_tag = item.find(['h2', 'h3'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                link_tag = item.find('a', href=True)
                if link_tag:
                    href = link_tag.get('href', '')
                    if href.startswith('/'):
                        link = 'https://www.undp.org' + href
                    else:
                        link = href
                else:
                    link = 'N/A'
                
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
                
                if title != 'N/A' and link != 'N/A':
                    opportunities.append({
                        'title': f"UNDP: {title}",
                        'organization': 'UNDP',
                        'description': description[:500],
                        'deadline': deadline,
                        'eligibility': eligibility[:200],
                        'benefits': benefits[:200],
                        'link': link,
                        'source': 'UNDP',
                        'type': opp_type,
                        'eligibility_criteria': eligibility,
                        'funding_level': benefits
                    })
    except Exception as e:
        print(f"Error scraping UNDP: {e}")
    
    return opportunities

# ============ SOURCE 5: African Union ============
def scrape_african_union():
    """Scrapes African Union opportunities"""
    opportunities = []
    url = "https://au.int/en/opportunities"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            items = soup.find_all('div', class_=re.compile(r'views-row|item|opportunity', re.I))
            
            for item in items[:10]:
                title_tag = item.find('a')
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                if title_tag and title_tag.has_attr('href'):
                    href = title_tag.get('href', '')
                    if href.startswith('/'):
                        link = 'https://au.int' + href
                    else:
                        link = href
                else:
                    link = 'N/A'
                
                desc_tag = item.find('p')
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
                deadline = extract_deadline(description + title)
                eligibility = extract_eligibility(description)
                benefits = extract_benefits(description)
                
                if title != 'N/A' and link != 'N/A':
                    opportunities.append({
                        'title': f"AU: {title}",
                        'organization': 'African Union',
                        'description': description[:500],
                        'deadline': deadline,
                        'eligibility': eligibility[:200],
                        'benefits': benefits[:200],
                        'link': link,
                        'source': 'African Union',
                        'type': 'Fellowship',
                        'eligibility_criteria': eligibility,
                        'funding_level': benefits
                    })
    except Exception as e:
        print(f"Error scraping African Union: {e}")
    
    return opportunities

# ============ FILTER FUNCTIONS ============
def filter_africa_opportunities(opportunities):
    """Filter for Africa-relevant opportunities"""
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
    """Filter for opportunities with deadlines in the future"""
    # Simple filter - keep opportunities that have a deadline or are ongoing
    active = []
    for opp in opportunities:
        deadline = opp.get('deadline', '')
        if deadline and 'ongoing' in deadline.lower():
            active.append(opp)
        elif deadline and 'vari' in deadline.lower():
            active.append(opp)
        elif deadline and deadline != 'N/A':
            active.append(opp)
        elif not deadline or deadline == 'N/A':
            # Keep if no deadline specified (likely ongoing)
            active.append(opp)
    return active

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
    
    print("Scraping UNDP...")
    all_opportunities.extend(scrape_undp())
    
    print("Scraping African Union...")
    all_opportunities.extend(scrape_african_union())
    
    print(f"Total found: {len(all_opportunities)}")
    
    # Filter for Africa
    africa_ops = filter_africa_opportunities(all_opportunities)
    print(f"After Africa filter: {len(africa_ops)}")
    
    # Filter for active opportunities
    active_ops = filter_active_opportunities(africa_ops)
    print(f"After active filter: {len(active_ops)}")
    
    return active_ops

if __name__ == '__main__':
    data = run_scraper()
    df = pd.DataFrame(data)
    df.to_csv('opportunities.csv', index=False)
    print(f"Saved {len(data)} opportunities to CSV")
