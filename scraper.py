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
                
                title_tag = card.find(['h2', 'h3', 'h4'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
                desc_tag = card.find(['p', 'div'], class_=re.compile(r'desc|body|excerpt', re.I))
                description = clean_text(desc_tag.get_text()) if desc_tag else 'N/A'
                
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
                
                title = clean_text(link_tag.get_text()) if link_tag else 'N/A'
                
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
                
                title_tag = item.find(['h2', 'h3'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
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
                
                title = clean_text(link_tag.get_text()) if link_tag else 'N/A'
                
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
                
                title_tag = item.find(['h2', 'h3'])
                title = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                
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

# ============ SOURCE 6: UNDP Youth Co-Creators Council ============
def scrape_undp_youth_council():
    opportunities = []
    
    try:
        opportunities.append({
            'title': 'UNDP African Youth Co-Creators Council',
            'organization': 'UNDP',
            'description': 'Call for applications for young African leaders to join the African Youth Co-Creators Council. Shape UNDP\'s work on youth engagement and provide strategic guidance on youth programming across the continent.',
            'deadline': '31 July 2026',
            'eligibility': 'African nationals aged 18-34 with demonstrated leadership experience',
            'benefits': 'Leadership development, policy influence, networking, mentorship',
            'link': 'https://www.undp.org/africa/call-applications-african-youth-co-creators-council',
            'source': 'UNDP',
            'type': 'Leadership Program',
            'target_audience': 'African youth',
            'funding_level': 'Fully Funded (travel costs covered)'
        })
    except Exception as e:
        print(f"Error scraping UNDP Youth Council: {e}")
    
    return opportunities

# ============ SOURCE 7: AU Digital & Innovation Fellowship ============
def scrape_au_digital_fellowship():
    opportunities = []
    
    try:
        opportunities.append({
            'title': 'AU Digital & Innovation Fellowship - Cohort 3',
            'organization': 'African Union Commission',
            'description': '12-month immersive programme selecting Africa\'s brightest technical minds to co-develop data-driven solutions within AU institutions. Fellows work across specialized technical tracks including Data Analytics, Digital Communications, Full-Stack Development, and ERP SAP.',
            'deadline': '1 March 2026',
            'eligibility': 'AU Member State citizens under 35 with degree in relevant technical field',
            'benefits': 'Monthly stipend (2500 Euros), equipment budget, learning budget, international exposure, bootcamps',
            'link': 'https://au.int/en/digital-and-innovation-fellowship',
            'source': 'African Union',
            'type': 'Fellowship',
            'target_audience': 'African youth in tech',
            'funding_level': 'Fully Funded'
        })
    except Exception as e:
        print(f"Error scraping AU Digital Fellowship: {e}")
    
    return opportunities

# ============ SOURCE 8: EAC Student Mobility Scholarship ============
def scrape_eac_scholarship():
    opportunities = []
    
    try:
        opportunities.append({
            'title': 'EAC Student Mobility Scholarship Scheme',
            'organization': 'East African Community',
            'description': 'Scholarships for diploma, undergraduate, master\'s and PhD study at 28 universities across Burundi, Kenya, Rwanda, South Sudan, Tanzania and Uganda. Covers tuition, exam fees, travel, health insurance and research support.',
            'deadline': '20 August 2026',
            'eligibility': 'Nationals and residents of EAC partner states; Master\'s applicants under 35, PhD applicants under 45',
            'benefits': 'Tuition, exam fees, travel, health insurance, research support (students cover housing and living costs)',
            'link': 'https://www.eac.int/',
            'source': 'EAC',
            'type': 'Scholarship',
            'target_audience': 'EAC nationals',
            'funding_level': 'Partial (tuition + fees)'
        })
    except Exception as e:
        print(f"Error scraping EAC scholarship: {e}")
    
    return opportunities

# ============ SOURCE 9: UNDP timbuktoo EdTech ============
def scrape_timbuktoo_edtech():
    opportunities = []
    
    try:
        opportunities.append({
            'title': 'UNDP timbuktoo EdTech Hub Pan-African Incubation Programme',
            'organization': 'UNDP',
            'description': 'Supports African EdTech startups with mentorship, incubation services, investment-readiness help and access to investors. Based in Dakar, Senegal. Connects startups with governments, universities, investors and incubators.',
            'deadline': 'Rolling (applications reviewed continuously)',
            'eligibility': 'African-based startups working on education/skills development with prototype ready; priority to women-led teams, rural founders, local-language solutions',
            'benefits': 'Mentorship, incubation services, investment-readiness support, investor access',
            'link': 'https://www.undp.org/africa/timbuktoo',
            'source': 'UNDP',
            'type': 'Grant/Incubation',
            'target_audience': 'African EdTech startups',
            'funding_level': 'Fully Funded Incubation'
        })
    except Exception as e:
        print(f"Error scraping timbuktoo: {e}")
    
    return opportunities

# ============ SOURCE 10: New Leaders Lab ============
def scrape_new_leaders_lab():
    opportunities = []
    
    try:
        opportunities.append({
            'title': 'New Leaders Lab - AEYA',
            'organization': 'AEYA (African European Youth Alliance)',
            'description': 'Free 3-4 month leadership program focused on entrepreneurship, civic engagement, and community development. Fully funded by the European Union.',
            'deadline': '19 July 2026',
            'eligibility': 'Aged 18-30 residing in: Benin, Burkina Faso, Cameroon, Congo, Côte d\'Ivoire, Ethiopia, Guinea, Kenya, Malawi, Mauritania, Mozambique, Niger, Uganda, DRC, Rwanda, Senegal, Tanzania, Togo, Zambia',
            'benefits': 'Leadership development, mentorship, networking, project support',
            'link': 'https://aeya.org',
            'source': 'AEYA',
            'type': 'Leadership Program',
            'target_audience': 'Youth in 19 African countries',
            'funding_level': 'Fully Funded'
        })
    except Exception as e:
        print(f"Error scraping New Leaders Lab: {e}")
    
    return opportunities

# ============ SOURCE 11: Africa CDC Fellowship ============
def scrape_africa_cdc_fellowship():
    opportunities = []
    
    try:
        opportunities.append({
            'title': 'Africa CDC African Epidemic Services Fellowship',
            'organization': 'Africa CDC',
            'description': 'Fully funded two-year fellowship for young public health professionals from African Union member states. First three months in Addis Ababa, Ethiopia, followed by 21 months of field-based training in an AU member state.',
            'deadline': '26 August 2026',
            'eligibility': 'Under 35, already employed in Africa, hold relevant health-related qualifications',
            'benefits': 'Fully funded two-year program with training and field experience',
            'link': 'https://africacdc.org/',
            'source': 'Africa CDC',
            'type': 'Fellowship',
            'target_audience': 'African public health professionals',
            'funding_level': 'Fully Funded'
        })
    except Exception as e:
        print(f"Error scraping Africa CDC: {e}")
    
    return opportunities

# ============ SOURCE 12: World Bank Fellowship ============
def scrape_world_bank_fellowship():
    opportunities = []
    
    try:
        opportunities.append({
            'title': 'World Bank Group Africa Fellowship Program 2027',
            'organization': 'World Bank Group',
            'description': 'Six-month fellowship for final-year PhD candidates and recent PhD graduates from Sub-Saharan Africa. Placement runs from January 2027 at World Bank headquarters in Washington, D.C., or at a country office.',
            'deadline': '25 August 2026',
            'eligibility': 'Final-year PhD candidates and recent PhD graduates from Sub-Saharan Africa; 32 or younger as of Jan 1, 2027; strong research and analytical skills',
            'benefits': 'Six-month placement, professional development, networking',
            'link': 'https://www.worldbank.org/',
            'source': 'World Bank',
            'type': 'Fellowship',
            'target_audience': 'Sub-Saharan African PhD candidates',
            'funding_level': 'Fully Funded'
        })
    except Exception as e:
        print(f"Error scraping World Bank: {e}")
    
    return opportunities

# ============ SOURCE 13: Africa Fundraising Incubator ============
def scrape_fundraising_incubator():
    opportunities = []
    
    try:
        opportunities.append({
            'title': 'Africa Fundraising Incubator 2026',
            'organization': 'Various Partners',
            'description': 'Capacity-building programme for nonprofits, social enterprises and community groups focused on fundraising. Hands-on training in fundraising, donor engagement and proposal writing with live fundraising campaign.',
            'deadline': '14 August 2026 (5pm UTC)',
            'eligibility': 'Nonprofits, social enterprises, community groups',
            'benefits': 'Up to $5,000 in matching funds, 12 months fiscal sponsorship, training, in-person bootcamp in Kigali for top performers',
            'link': 'https://africafundraising.org/',
            'source': 'Africa Fundraising Incubator',
            'type': 'Grant/Training',
            'target_audience': 'African nonprofits and social enterprises',
            'funding_level': 'Grant up to $5,000'
        })
    except Exception as e:
        print(f"Error scraping Fundraising Incubator: {e}")
    
    return opportunities

# ============ SOURCE 14: Mastercard Scholars Program ============
def scrape_mastercard_scholars():
    opportunities = []
    
    try:
        opportunities.append({
            'title': 'Mastercard Foundation Scholars Program',
            'organization': 'Mastercard Foundation',
            'description': 'Scholarship program providing financial, social and academic support to talented African students from disadvantaged communities. Available for secondary, undergraduate and Master\'s studies at partner universities globally.',
            'deadline': 'Varies by institution',
            'eligibility': 'African students; under 29 for undergraduate, under 35 for Master\'s; academically talented with leadership potential',
            'benefits': 'Tuition, accommodation, books, research materials, leadership development, mentorship',
            'link': 'https://mastercardfdn.org/',
            'source': 'Mastercard Foundation',
            'type': 'Scholarship',
            'target_audience': 'African students',
            'funding_level': 'Fully Funded'
        })
    except Exception as e:
        print(f"Error scraping Mastercard Scholars: {e}")
    
    return opportunities

# ============ SOURCE 15: Code for Africa ============
def scrape_code_for_africa():
    opportunities = []
    
    try:
        opportunities.append({
            'title': 'Code for Africa Mythbusters Fellowship',
            'organization': 'Code for Africa (CfA)',
            'description': 'Part-time fellowships for community researchers in the SADC region to investigate and counter misinformation, and amplify factual narratives.',
            'deadline': 'Varies',
            'eligibility': 'Community researchers in the SADC region',
            'benefits': 'Monthly stipend',
            'link': 'https://codeforafrica.org/',
            'source': 'Code for Africa',
            'type': 'Fellowship',
            'target_audience': 'SADC region researchers',
            'funding_level': 'Stipend'
        })
    except Exception as e:
        print(f"Error scraping Code for Africa: {e}")
    
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
    
    africa_ops = filter_africa_opportunities(all_opportunities)
    print(f"After Africa filter: {len(africa_ops)}")
    
    active_ops = filter_active_opportunities(africa_ops)
    print(f"After active filter: {len(active_ops)}")
    
    return active_ops

if __name__ == '__main__':
    data = run_scraper()
    df = pd.DataFrame(data)
    df.to_csv('opportunities.csv', index=False)
    print(f"Saved {len(data)} opportunities to CSV")
