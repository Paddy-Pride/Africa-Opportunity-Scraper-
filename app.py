# app.py - Enhanced Comprehensive African Youth Opportunity Scraper
import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import random
import json
from urllib.parse import urljoin, urlparse
import hashlib

# Page configuration
st.set_page_config(
    page_title="AfriYouth · African Opportunity Scraper",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0a2e42, #1d5a7a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #2c6b8a;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .opportunity-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e9f0f5;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: all 0.2s;
    }
    .opportunity-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }
    .card-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #0c2d3d;
        margin-bottom: 0.5rem;
    }
    .card-badge {
        display: inline-block;
        background: #e3edf5;
        padding: 0.2rem 0.7rem;
        border-radius: 40px;
        font-size: 0.7rem;
        font-weight: 600;
        color: #144a60;
        border: 1px solid #cadeec;
        margin-right: 0.5rem;
    }
    .card-meta {
        font-size: 0.85rem;
        color: #315d72;
        margin: 0.5rem 0;
    }
    .card-desc {
        color: #1e4053;
        margin: 0.5rem 0;
        line-height: 1.5;
    }
    .deadline-badge {
        background: #f0f7fc;
        padding: 0.2rem 0.8rem;
        border-radius: 30px;
        font-size: 0.75rem;
        color: #3c6f86;
    }
    .stButton > button {
        border-radius: 40px;
        padding: 0.5rem 1.5rem;
    }
    .stSelectbox > div > div {
        border-radius: 40px;
    }
    .stTextInput > div > div > input {
        border-radius: 40px;
    }
    .source-tag {
        background: #f0f4f8;
        padding: 0.1rem 0.5rem;
        border-radius: 20px;
        font-size: 0.7rem;
        color: #4a6f84;
    }
    .live-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #1f9b5e;
        border-radius: 50%;
        animation: pulse 1.8s infinite;
        margin-right: 8px;
    }
    @keyframes pulse {
        0% { opacity: 0.4; transform: scale(0.9); }
        50% { opacity: 1; transform: scale(1.2); }
        100% { opacity: 0.4; transform: scale(0.9); }
    }
    .status-box {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1d5a7a;
    }
    .success-box {
        border-left-color: #28a745;
        background: #f0f9f0;
    }
    .warning-box {
        border-left-color: #ffc107;
        background: #fff9f0;
    }
</style>
""", unsafe_allow_html=True)

class EnhancedScraper:
    """Enhanced scraper for African youth opportunities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.all_opportunities = []
        self.scraped_sources = {}
        
    def scrape_all_sources(self, progress_callback=None):
        """Scrape from all configured sources with improved detection"""
        sources = self.get_enhanced_source_configs()
        total_sources = len(sources)
        successful_sources = 0
        
        for i, (source_name, source_config) in enumerate(sources.items()):
            if progress_callback:
                progress_callback(i / total_sources, f"Scraping {source_name}...")
            
            try:
                opportunities = self.scrape_enhanced_source(source_name, source_config)
                if opportunities:
                    self.all_opportunities.extend(opportunities)
                    self.scraped_sources[source_name] = len(opportunities)
                    successful_sources += 1
                    if progress_callback:
                        progress_callback(i / total_sources, f"✅ Found {len(opportunities)} from {source_name}")
                else:
                    self.scraped_sources[source_name] = 0
                    if progress_callback:
                        progress_callback(i / total_sources, f"⚠️ No results from {source_name}")
            except Exception as e:
                self.scraped_sources[source_name] = 0
                if progress_callback:
                    progress_callback(i / total_sources, f"❌ Error scraping {source_name}")
            
            # Random delay between requests
            time.sleep(random.uniform(1.5, 3.5))
        
        if progress_callback:
            progress_callback(0.95, f"Deduplicating {len(self.all_opportunities)} opportunities...")
        
        unique = self.deduplicate_enhanced(self.all_opportunities)
        
        if not unique:
            if progress_callback:
                progress_callback(1.0, "Using comprehensive fallback data...")
            unique = self.get_enhanced_fallback_data()
        
        if progress_callback:
            progress_callback(1.0, f"✅ Found {len(unique)} unique opportunities from {successful_sources} sources")
        
        return unique
    
    def get_enhanced_source_configs(self):
        """Get enhanced source configurations with multiple scraping strategies"""
        return {
            # Major African Youth Opportunity Platforms - with multiple strategies
            "Youth Opportunities": {
                "urls": [
                    "https://www.youthop.com/opportunities/africa",
                    "https://www.youthop.com/opportunities/fellowships",
                    "https://www.youthop.com/opportunities/scholarships",
                    "https://www.youthop.com/opportunities/competitions"
                ],
                "strategies": [
                    {"container": "div.opportunity-item", "title": "h3", "desc": "p.description", "date": "span.date", "location": "span.location"},
                    {"container": "article.listing-item", "title": "h2", "desc": "div.excerpt", "date": "span.deadline", "location": "span.country"},
                    {"container": "div.post-item", "title": "a", "desc": "p", "date": "time", "location": "span.region"}
                ]
            },
            "Scholarships for Africans": {
                "urls": [
                    "https://scholarshipsforafricans.com/"
                ],
                "strategies": [
                    {"container": "article", "title": "h2", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "div.post", "title": "h3", "desc": "div.excerpt", "date": "time", "location": "div.country"},
                    {"container": "div.scholarship-item", "title": "a", "desc": "div.summary", "date": "span.date", "location": "span.region"}
                ]
            },
            "Opportunity Desk": {
                "urls": [
                    "https://opportunitydesk.org/category/opportunities/",
                    "https://opportunitydesk.org/category/fellowships/",
                    "https://opportunitydesk.org/category/scholarships/"
                ],
                "strategies": [
                    {"container": "article", "title": "h2", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "div.post", "title": "h3", "desc": "div.excerpt", "date": "time", "location": "div.country"},
                    {"container": "div.entry", "title": "a", "desc": "div.summary", "date": "span.date", "location": "span.region"}
                ]
            },
            "African Development Bank": {
                "urls": [
                    "https://www.afdb.org/en/careers",
                    "https://www.afdb.org/en/careers/current-vacancies"
                ],
                "strategies": [
                    {"container": "div.job-listing", "title": "h3", "desc": "p", "date": "span.date", "location": "span.location"},
                    {"container": "article.job", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "div.views-row", "title": "h2", "desc": "div.summary", "date": "span.deadline", "location": "span.region"}
                ]
            },
            "UNESCO Africa": {
                "urls": [
                    "https://www.unesco.org/en/fieldoffice/africa",
                    "https://en.unesco.org/fieldoffice/africa/opportunities"
                ],
                "strategies": [
                    {"container": "div.card", "title": "h2", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "h3", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "div.content-item", "title": "a", "desc": "div.excerpt", "date": "span.date", "location": "span.region"}
                ]
            },
            "Mastercard Foundation": {
                "urls": [
                    "https://mastercardfdn.org/our-work/programs/",
                    "https://mastercardfdn.org/opportunities/"
                ],
                "strategies": [
                    {"container": "div.program-item", "title": "h3", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "div.card", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "article", "title": "h2", "desc": "div.summary", "date": "span.date", "location": "span.region"}
                ]
            },
            "African Union": {
                "urls": [
                    "https://au.int/en/opportunities",
                    "https://au.int/en/careers"
                ],
                "strategies": [
                    {"container": "div.view-content", "title": "a", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "h3", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "div.listing", "title": "h2", "desc": "div.summary", "date": "span.date", "location": "span.region"}
                ]
            },
            # Additional African Focused Sites
            "African Leadership Academy": {
                "urls": ["https://www.africanleadershipacademy.org/opportunities/"],
                "strategies": [
                    {"container": "div.opportunity", "title": "h3", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "div.post", "title": "h2", "desc": "div.excerpt", "date": "span.date", "location": "span.region"}
                ]
            },
            "YALI Network": {
                "urls": ["https://yali.state.gov/opportunities/"],
                "strategies": [
                    {"container": "div.opportunity", "title": "h3", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "div.post", "title": "h2", "desc": "div.excerpt", "date": "span.date", "location": "span.region"}
                ]
            },
            "UNDP Africa": {
                "urls": [
                    "https://www.undp.org/africa/careers",
                    "https://www.undp.org/africa/opportunities"
                ],
                "strategies": [
                    {"container": "div.job", "title": "h3", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "div.opportunity", "title": "h2", "desc": "div.summary", "date": "span.date", "location": "span.region"}
                ]
            },
            "World Bank Africa": {
                "urls": ["https://www.worldbank.org/en/region/afr/opportunities"],
                "strategies": [
                    {"container": "div.opportunity", "title": "h3", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "div.listing", "title": "h2", "desc": "div.summary", "date": "span.date", "location": "span.region"}
                ]
            },
            "UNICEF Africa": {
                "urls": [
                    "https://www.unicef.org/africa/careers",
                    "https://www.unicef.org/africa/opportunities"
                ],
                "strategies": [
                    {"container": "div.job", "title": "h3", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "div.opportunity", "title": "h2", "desc": "div.summary", "date": "span.date", "location": "span.region"}
                ]
            },
            "All Africa Jobs": {
                "urls": ["https://www.allafricajobs.com/opportunities"],
                "strategies": [
                    {"container": "div.job-item", "title": "h3", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "div.listing", "title": "h2", "desc": "div.summary", "date": "span.date", "location": "span.region"}
                ]
            },
            "Africa Youth Employment": {
                "urls": ["https://www.africayouthemployment.org/opportunities/"],
                "strategies": [
                    {"container": "div.opportunity", "title": "h3", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"},
                    {"container": "div.post", "title": "h2", "desc": "div.excerpt", "date": "span.date", "location": "span.region"}
                ]
            }
        }
    
    def scrape_enhanced_source(self, source_name, source_config):
        """Scrape a source using multiple strategies"""
        opportunities = []
        urls = source_config.get("urls", [])
        strategies = source_config.get("strategies", [])
        
        for url in urls:
            try:
                # Rotate user agents
                self.session.headers.update({
                    'User-Agent': random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
                    ])
                })
                
                response = self.session.get(url, timeout=20)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try each strategy
                    for strategy in strategies:
                        container_selector = strategy.get("container", "")
                        title_selector = strategy.get("title", "")
                        desc_selector = strategy.get("desc", "")
                        date_selector = strategy.get("date", "")
                        location_selector = strategy.get("location", "")
                        
                        # Find containers
                        containers = soup.find_all(container_selector) if container_selector else []
                        
                        # If no containers found with specific selector, try common ones
                        if not containers and container_selector:
                            # Try to find any article or post divs
                            containers = soup.find_all(['article', 'div'], class_=re.compile(r'(post|entry|item|listing|opportunity|job|scholarship)'))
                        
                        for container in containers[:12]:
                            try:
                                # Extract elements
                                title_elem = container.find(title_selector) if title_selector else container.find(['h2', 'h3', 'a'])
                                if not title_elem:
                                    # Try finding any heading
                                    title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                                
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.get_text().strip()
                                if not title or len(title) < 5:
                                    continue
                                
                                # Description
                                desc_elem = container.find(desc_selector) if desc_selector else container.find('p')
                                description = desc_elem.get_text().strip() if desc_elem else "Opportunity in Africa"
                                
                                # Deadline
                                date_elem = container.find(date_selector) if date_selector else container.find(['time', 'span'], class_=re.compile(r'(date|deadline|time)'))
                                deadline = date_elem.get_text().strip() if date_elem else None
                                
                                # Location
                                loc_elem = container.find(location_selector) if location_selector else container.find(['span', 'div'], class_=re.compile(r'(location|country|region)'))
                                location = loc_elem.get_text().strip() if loc_elem else "Africa"
                                
                                # Find link
                                link = None
                                link_elem = container.find('a')
                                if link_elem and link_elem.get('href'):
                                    link = urljoin(url, link_elem.get('href'))
                                
                                # Determine category
                                category = self.detect_category_enhanced(title)
                                
                                # Determine region
                                region = self.detect_region_enhanced(location + " " + title)
                                
                                opportunities.append({
                                    'title': title[:200],
                                    'description': description[:500] if description else "No description available",
                                    'category': category,
                                    'region': region,
                                    'country': location if location != "Africa" else "Various",
                                    'deadline': deadline,
                                    'source': source_name,
                                    'url': link or url,
                                    'scraped_at': datetime.now().isoformat(),
                                    'id': hashlib.md5(f"{title}_{source_name}".encode()).hexdigest()[:8]
                                })
                            except Exception as e:
                                continue
                    
            except Exception as e:
                continue
            
            time.sleep(random.uniform(1, 2))
        
        return opportunities
    
    def detect_category_enhanced(self, title):
        """Enhanced category detection"""
        title_lower = title.lower()
        
        # Priority categories
        if any(word in title_lower for word in ['fellowship', 'fellow']):
            return 'fellowship'
        elif any(word in title_lower for word in ['scholarship', 'scholar', 'tuition', 'fully funded']):
            return 'scholarship'
        elif any(word in title_lower for word in ['internship', 'intern', 'trainee', 'apprentice']):
            return 'internship'
        elif any(word in title_lower for word in ['grant', 'funding', 'financial support']):
            return 'grant'
        elif any(word in title_lower for word in ['competition', 'contest', 'award', 'prize', 'challenge']):
            return 'competition'
        elif any(word in title_lower for word in ['volunteer', 'voluntary']):
            return 'volunteer'
        elif any(word in title_lower for word in ['training', 'workshop', 'program', 'development']):
            return 'training'
        else:
            return 'opportunity'
    
    def detect_region_enhanced(self, text):
        """Enhanced region detection"""
        text_lower = text.lower()
        
        region_keywords = {
            'West Africa': ['nigeria', 'ghana', 'senegal', 'mali', 'côte', 'ivory', 'liberia', 'sierra', 'guinea', 'benin', 'togo', 'burkina'],
            'East Africa': ['kenya', 'tanzania', 'uganda', 'ethiopia', 'rwanda', 'burundi', 'somalia', 'eritrea', 'djibouti'],
            'Southern Africa': ['south africa', 'zimbabwe', 'zambia', 'malawi', 'angola', 'mozambique', 'namibia', 'botswana', 'lesotho', 'eswatini'],
            'North Africa': ['egypt', 'morocco', 'algeria', 'tunisia', 'libya', 'sudan', 'mauritania'],
            'Central Africa': ['congo', 'cameroon', 'gabon', 'chad', 'car', 'equatorial', 'sao tome']
        }
        
        for region, keywords in region_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return region
        
        return 'All Africa'
    
    def deduplicate_enhanced(self, opportunities):
        """Enhanced deduplication"""
        seen = set()
        unique = []
        
        for opp in opportunities:
            # Create unique key from title and source
            key = f"{opp.get('title', '')[:60]}_{opp.get('source', '')}"
            if key not in seen:
                seen.add(key)
                unique.append(opp)
        
        return unique
    
    def get_enhanced_fallback_data(self):
        """Enhanced fallback data with diverse opportunities"""
        return [
            {
                'title': 'African Youth Leadership Fellowship 2026',
                'description': 'A 6-month intensive leadership program for young African leaders focused on policy, advocacy, and sustainable development across the continent. Fully funded including travel, accommodation, and stipend.',
                'category': 'fellowship',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-12-15',
                'source': 'African Youth Initiative (Fallback)',
                'url': 'https://example.com/fellowship',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'Pan-African Scholarship for STEM Education 2026',
                'description': 'Full tuition scholarship for African students pursuing undergraduate and graduate degrees in Science, Technology, Engineering, and Mathematics at partner universities across Africa and abroad.',
                'category': 'scholarship',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-11-30',
                'source': 'African Education Trust (Fallback)',
                'url': 'https://example.com/scholarship',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'Digital Innovation Internship Program - East Africa',
                'description': 'Paid 3-month internship program for recent graduates in East Africa to work with leading tech startups, innovation hubs, and digital companies across Kenya, Tanzania, and Uganda.',
                'category': 'internship',
                'region': 'East Africa',
                'country': 'Kenya, Tanzania, Uganda',
                'deadline': '2026-10-20',
                'source': 'East African Tech Hub (Fallback)',
                'url': 'https://example.com/internship',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'African Arts and Culture Grant 2026',
                'description': 'Funding opportunities for emerging artists, cultural practitioners, and heritage preservation projects across Southern Africa. Grants up to $10,000 available.',
                'category': 'grant',
                'region': 'Southern Africa',
                'country': 'South Africa, Zimbabwe, Zambia',
                'deadline': '2026-09-25',
                'source': 'African Arts Foundation (Fallback)',
                'url': 'https://example.com/grant',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'African Green Innovation Competition 2026',
                'description': 'Pan-African competition for climate tech solutions and sustainable innovations. Winners receive $10,000 funding, mentorship, and incubation support.',
                'category': 'competition',
                'region': 'All Africa',
                'country': 'Pan-African',
                'deadline': '2026-08-30',
                'source': 'Green Africa Initiative (Fallback)',
                'url': 'https://example.com/competition',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'African Union Youth Fellowship Program 2026-27',
                'description': 'Prestigious fellowship program for young professionals to work with the African Union on continental development initiatives, policy research, and implementation of Agenda 2063.',
                'category': 'fellowship',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-10-01',
                'source': 'African Union (Fallback)',
                'url': 'https://example.com/au-fellowship',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'Women in African Tech Scholarship Program 2026',
                'description': 'Scholarship program specifically for women from West Africa pursuing careers in technology, engineering, and computer science. Includes mentorship and internship placement.',
                'category': 'scholarship',
                'region': 'West Africa',
                'country': 'Nigeria, Ghana, Senegal',
                'deadline': '2026-09-15',
                'source': 'Women in Tech Africa (Fallback)',
                'url': 'https://example.com/women-tech',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'Climate Action Internship for African Youth 2026',
                'description': 'Remote internship program for African youth to work on climate action projects, policy research, sustainable development initiatives, and environmental advocacy.',
                'category': 'internship',
                'region': 'All Africa',
                'country': 'Remote',
                'deadline': '2026-11-01',
                'source': 'Climate Africa Initiative (Fallback)',
                'url': 'https://example.com/climate-internship',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'African Development Bank Young Professionals Program',
                'description': 'Highly competitive program for young African professionals to work at the African Development Bank. Two-year program with rotations across departments.',
                'category': 'fellowship',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-12-01',
                'source': 'African Development Bank (Fallback)',
                'url': 'https://example.com/afdb-yp',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'UNESCO Africa Education Scholarship 2026',
                'description': 'Scholarship program for African students pursuing education degrees with focus on educational policy, curriculum development, and technology in education.',
                'category': 'scholarship',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-10-15',
                'source': 'UNESCO Africa (Fallback)',
                'url': 'https://example.com/unesco-education',
                'scraped_at': datetime.now().isoformat()
            }
        ]

# Initialize session state
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = []
if 'saved' not in st.session_state:
    st.session_state.saved = set()
if 'last_scrape' not in st.session_state:
    st.session_state.last_scrape = None
if 'auto_scraped' not in st.session_state:
    st.session_state.auto_scraped = False
if 'scraped_sources' not in st.session_state:
    st.session_state.scraped_sources = {}

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="main-header">🌍 AfriYouth</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">African Youth Opportunity Scraper · Real-time opportunities across the continent</div>', unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div style="background: #e6f0f5; padding: 0.5rem 1rem; border-radius: 60px; text-align: center; border: 1px solid #bfd7e3;">
        <span class="live-indicator"></span> Live
    </div>
    """, unsafe_allow_html=True)

# Auto-scrape on first load
if not st.session_state.auto_scraped:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(progress, status):
        progress_bar.progress(progress)
        status_text.text(status)
    
    with st.spinner("🔄 Scraping opportunities from across Africa..."):
        scraper = EnhancedScraper()
        st.session_state.opportunities = scraper.scrape_all_sources(update_progress)
        st.session_state.scraped_sources = scraper.scraped_sources
        st.session_state.last_scrape = datetime.now()
        st.session_state.auto_scraped = True
    
    progress_bar.empty()
    status_text.empty()
    st.rerun()

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Filters")
    
    category_filter = st.selectbox(
        "Category",
        ["All", "fellowship", "scholarship", "internship", "grant", "competition", "volunteer", "training", "opportunity"]
    )
    
    region_filter = st.selectbox(
        "Region",
        ["All", "West Africa", "East Africa", "Southern Africa", "North Africa", "Central Africa", "All Africa"]
    )
    
    search_term = st.text_input("🔍 Search", placeholder="Search opportunities...")
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    
    total = len(st.session_state.opportunities)
    saved_count = len(st.session_state.saved)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Saved", saved_count)
    
    if st.session_state.scraped_sources:
        st.markdown("---")
        st.markdown("### 📰 Sources")
        for source, count in st.session_state.scraped_sources.items():
            if count > 0:
                st.caption(f"✅ {source}: {count}")
            else:
                st.caption(f"❌ {source}: {count}")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh All Sources", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(progress, status):
            progress_bar.progress(progress)
            status_text.text(status)
        
        with st.spinner("Scraping all sources..."):
            scraper = EnhancedScraper()
            st.session_state.opportunities = scraper.scrape_all_sources(update_progress)
            st.session_state.scraped_sources = scraper.scraped_sources
            st.session_state.last_scrape = datetime.now()
        
        progress_bar.empty()
        status_text.empty()
        st.rerun()
    
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.opportunities = []
        st.session_state.saved = set()
        st.session_state.last_scrape = None
        st.session_state.scraped_sources = {}
        st.rerun()
    
    if st.session_state.last_scrape:
        st.caption(f"Last scrape: {st.session_state.last_scrape.strftime('%Y-%m-%d %H:%M:%S')}")

# Main content
filtered_opps = st.session_state.opportunities.copy()

if category_filter != "All":
    filtered_opps = [o for o in filtered_opps if o.get('category') == category_filter]

if region_filter != "All":
    filtered_opps = [o for o in filtered_opps if o.get('region') == region_filter]

if search_term:
    search_lower = search_term.lower()
    filtered_opps = [
        o for o in filtered_opps 
        if search_lower in o.get('title
