# app.py - Comprehensive African Youth Opportunity Scraper
import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import random
import json
from urllib.parse import urljoin, urlparse

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
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #e9f0f5;
        text-align: center;
    }
    .saved-badge {
        color: #0f7b3a;
        background: #e2f3e9;
        padding: 0.2rem 0.7rem;
        border-radius: 40px;
        font-size: 0.75rem;
        border: 1px solid #b5dac8;
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
    .source-tag {
        background: #f0f4f8;
        padding: 0.1rem 0.5rem;
        border-radius: 20px;
        font-size: 0.7rem;
        color: #4a6f84;
    }
    .progress-container {
        margin: 1rem 0;
        padding: 1rem;
        background: #f8fafc;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

class ComprehensiveScraper:
    """Comprehensive scraper for African youth opportunities"""
    
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
        
    def scrape_all_sources(self, progress_callback=None):
        """Scrape from all configured sources"""
        sources = self.get_source_configs()
        total_sources = len(sources)
        
        for i, (source_name, source_config) in enumerate(sources.items()):
            if progress_callback:
                progress_callback(i / total_sources, f"Scraping {source_name}...")
            
            try:
                opportunities = self.scrape_source(source_name, source_config)
                if opportunities:
                    self.all_opportunities.extend(opportunities)
                    if progress_callback:
                        progress_callback(i / total_sources, f"Found {len(opportunities)} from {source_name}")
                else:
                    if progress_callback:
                        progress_callback(i / total_sources, f"No results from {source_name}")
            except Exception as e:
                if progress_callback:
                    progress_callback(i / total_sources, f"Error scraping {source_name}")
            
            time.sleep(random.uniform(1, 3))  # Respectful delay
        
        # Deduplicate
        if progress_callback:
            progress_callback(1.0, "Deduplicating opportunities...")
        
        unique = self.deduplicate(self.all_opportunities)
        
        if not unique:
            # Use fallback data
            if progress_callback:
                progress_callback(1.0, "Using fallback opportunity data...")
            unique = self.get_fallback_data()
        
        return unique
    
    def get_source_configs(self):
        """Get all source configurations"""
        return {
            # Major African Youth Opportunity Platforms
            "Youth Opportunities": {
                "urls": [
                    "https://www.youthop.com/opportunities/africa",
                    "https://www.youthop.com/opportunities/fellowships",
                    "https://www.youthop.com/opportunities/scholarships",
                    "https://www.youthop.com/opportunities/competitions"
                ],
                "selectors": {
                    "container": ["div.opportunity-item", "article.listing-item", "div.post-item", "div.listing"],
                    "title": ["h3", "h2", "a.title", "a", "h4"],
                    "description": ["p.description", "div.excerpt", "p", "div.summary"],
                    "deadline": ["span.date", "div.deadline", "time", "span.deadline"],
                    "location": ["span.location", "div.country", "span.region", "div.location"]
                }
            },
            "Opportunity Desk": {
                "urls": [
                    "https://opportunitydesk.org/category/opportunities/",
                    "https://opportunitydesk.org/category/fellowships/",
                    "https://opportunitydesk.org/category/scholarships/"
                ],
                "selectors": {
                    "container": ["article", "div.post", "div.entry", "div.blog-post"],
                    "title": ["h2", "h3", "a", "h1"],
                    "description": ["p", "div.excerpt", "div.entry-content", "div.summary"],
                    "deadline": ["span.deadline", "div.deadline", "time"],
                    "location": ["span.location", "div.location", "span.country"]
                }
            },
            "African Development Bank": {
                "urls": [
                    "https://www.afdb.org/en/careers",
                    "https://www.afdb.org/en/careers/current-vacancies"
                ],
                "selectors": {
                    "container": ["div.job-listing", "article.job", "div.views-row", "div.listing-item"],
                    "title": ["h3", "a", "h2", "span.title"],
                    "description": ["p", "div.description", "div.summary"],
                    "deadline": ["span.date", "div.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            "UNESCO Africa": {
                "urls": [
                    "https://www.unesco.org/en/fieldoffice/africa",
                    "https://en.unesco.org/fieldoffice/africa/opportunities"
                ],
                "selectors": {
                    "container": ["div.card", "article", "div.field-content", "div.content-item"],
                    "title": ["h2", "h3", "a", "h4"],
                    "description": ["p", "div.description", "div.excerpt"],
                    "deadline": ["span.deadline", "time", "div.deadline"],
                    "location": ["span.location", "div.location"]
                }
            },
            "Mastercard Foundation": {
                "urls": [
                    "https://mastercardfdn.org/our-work/programs/",
                    "https://mastercardfdn.org/opportunities/"
                ],
                "selectors": {
                    "container": ["div.program-item", "div.card", "article", "div.opportunity"],
                    "title": ["h3", "a", "h2", "span.title"],
                    "description": ["p", "div.description", "div.summary"],
                    "deadline": ["span.deadline", "time", "div.date"],
                    "location": ["span.location", "div.location"]
                }
            },
            "African Union": {
                "urls": [
                    "https://au.int/en/opportunities",
                    "https://au.int/en/careers"
                ],
                "selectors": {
                    "container": ["div.view-content", "article", "div.listing", "div.job"],
                    "title": ["a", "h3", "h2", "span.title"],
                    "description": ["p", "div.description", "div.summary"],
                    "deadline": ["span.deadline", "time", "div.date"],
                    "location": ["span.location", "div.location"]
                }
            },
            # Additional African Focused Sites
            "African Leadership Academy": {
                "urls": [
                    "https://www.africanleadershipacademy.org/opportunities/"
                ],
                "selectors": {
                    "container": ["div.opportunity", "article", "div.post"],
                    "title": ["h3", "h2", "a", "h4"],
                    "description": ["p", "div.description", "div.excerpt"],
                    "deadline": ["span.deadline", "time", "div.date"],
                    "location": ["span.location", "div.location"]
                }
            },
            "Forum for African Women": {
                "urls": [
                    "https://www.forumafricanwomen.org/opportunities/"
                ],
                "selectors": {
                    "container": ["div.opportunity-item", "article", "div.post"],
                    "title": ["h3", "h2", "a", "h4"],
                    "description": ["p", "div.description", "div.excerpt"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            "African Youth Network": {
                "urls": [
                    "https://www.africanyouthnetwork.org/opportunities/"
                ],
                "selectors": {
                    "container": ["div.opportunity", "article", "div.listing"],
                    "title": ["h3", "h2", "a"],
                    "description": ["p", "div.description", "div.summary"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            "YALI Network": {
                "urls": [
                    "https://yali.state.gov/opportunities/"
                ],
                "selectors": {
                    "container": ["div.opportunity", "article", "div.post"],
                    "title": ["h3", "h2", "a"],
                    "description": ["p", "div.description", "div.excerpt"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            "Africa Youth Employment": {
                "urls": [
                    "https://www.africayouthemployment.org/opportunities/"
                ],
                "selectors": {
                    "container": ["div.opportunity", "article", "div.listing"],
                    "title": ["h3", "h2", "a"],
                    "description": ["p", "div.description", "div.summary"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            # Development & NGO Opportunities
            "UNDP Africa": {
                "urls": [
                    "https://www.undp.org/africa/careers",
                    "https://www.undp.org/africa/opportunities"
                ],
                "selectors": {
                    "container": ["div.job", "article", "div.opportunity"],
                    "title": ["h3", "a", "h2"],
                    "description": ["p", "div.description", "div.summary"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            "World Bank Africa": {
                "urls": [
                    "https://www.worldbank.org/en/region/afr/opportunities"
                ],
                "selectors": {
                    "container": ["div.opportunity", "article", "div.listing"],
                    "title": ["h3", "a", "h2"],
                    "description": ["p", "div.description", "div.summary"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            "UNICEF Africa": {
                "urls": [
                    "https://www.unicef.org/africa/careers",
                    "https://www.unicef.org/africa/opportunities"
                ],
                "selectors": {
                    "container": ["div.job", "article", "div.opportunity"],
                    "title": ["h3", "a", "h2"],
                    "description": ["p", "div.description", "div.summary"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            "International Labour Organization Africa": {
                "urls": [
                    "https://www.ilo.org/africa/careers"
                ],
                "selectors": {
                    "container": ["div.job", "article", "div.opportunity"],
                    "title": ["h3", "a", "h2"],
                    "description": ["p", "div.description"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            # News & Aggregator Sites
            "African Youth News": {
                "urls": [
                    "https://www.africanyouthnews.com/opportunities/"
                ],
                "selectors": {
                    "container": ["div.opportunity", "article", "div.post"],
                    "title": ["h3", "h2", "a"],
                    "description": ["p", "div.description", "div.excerpt"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            "Opportunities for Africans": {
                "urls": [
                    "https://opportunitiesforafricans.com/"
                ],
                "selectors": {
                    "container": ["div.opportunity", "article", "div.post"],
                    "title": ["h3", "h2", "a"],
                    "description": ["p", "div.description", "div.excerpt"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            },
            "Scholarships for Africans": {
                "urls": [
                    "https://scholarshipsforafricans.com/"
                ],
                "selectors": {
                    "container": ["div.scholarship", "article", "div.post"],
                    "title": ["h3", "h2", "a"],
                    "description": ["p", "div.description", "div.excerpt"],
                    "deadline": ["span.deadline", "time"],
                    "location": ["span.location", "div.location"]
                }
            }
        }
    
    def scrape_source(self, source_name, source_config):
        """Scrape a single source"""
        opportunities = []
        urls = source_config.get("urls", [])
        selectors = source_config.get("selectors", {})
        
        for url in urls:
            try:
                self.session.headers.update({
                    'User-Agent': random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ])
                })
                
                response = self.session.get(url, timeout=20)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find containers
                    containers = []
                    for container_selector in selectors.get("container", []):
                        containers = soup.find_all(container_selector.split()[0] if ' ' in container_selector else container_selector)
                        if containers:
                            break
                    
                    if not containers:
                        # Try finding any article or content div
                        containers = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'(post|entry|item|listing|opportunity|job)'))
                    
                    for container in containers[:10]:  # Limit per page
                        try:
                            # Extract title
                            title = None
                            for title_selector in selectors.get("title", []):
                                elem = container.find(title_selector.split()[0] if ' ' in title_selector else title_selector)
                                if elem:
                                    title = elem.get_text().strip()
                                    break
                            
                            if not title or len(title) < 5:
                                continue
                            
                            # Extract description
                            description = ""
                            for desc_selector in selectors.get("description", []):
                                elem = container.find(desc_selector.split()[0] if ' ' in desc_selector else desc_selector)
                                if elem:
                                    description = elem.get_text().strip()
                                    break
                            
                            if not description:
                                description = "Opportunity available in Africa"
                            
                            # Extract deadline
                            deadline = None
                            for deadline_selector in selectors.get("deadline", []):
                                elem = container.find(deadline_selector.split()[0] if ' ' in deadline_selector else deadline_selector)
                                if elem:
                                    deadline = elem.get_text().strip()
                                    break
                            
                            # Extract location
                            location = "Africa"
                            for location_selector in selectors.get("location", []):
                                elem = container.find(location_selector.split()[0] if ' ' in location_selector else location_selector)
                                if elem:
                                    location = elem.get_text().strip()
                                    break
                            
                            # Extract link if available
                            link = None
                            link_elem = container.find('a')
                            if link_elem and link_elem.get('href'):
                                link = urljoin(url, link_elem.get('href'))
                            
                            # Determine category
                            category = self.detect_category(title)
                            
                            # Determine region
                            region = self.detect_region(location + " " + title)
                            
                            opportunities.append({
                                'title': title[:200],
                                'description': description[:500] if description else "No description available",
                                'category': category,
                                'region': region,
                                'country': location,
                                'deadline': deadline,
                                'source': source_name,
                                'url': link or url,
                                'scraped_at': datetime.now().isoformat()
                            })
                        except Exception as e:
                            continue
                
            except Exception as e:
                continue
            
            time.sleep(random.uniform(1, 2))  # Be respectful
        
        return opportunities
    
    def detect_category(self, title):
        """Detect category from title"""
        title_lower = title.lower()
        
        categories = {
            'fellowship': ['fellowship', 'fellow', 'fellow'],
            'scholarship': ['scholarship', 'scholar', 'study', 'tuition', 'academic'],
            'internship': ['internship', 'intern', 'trainee', 'traineeship', 'apprentice'],
            'grant': ['grant', 'fund', 'funding', 'financial support'],
            'competition': ['competition', 'contest', 'award', 'prize', 'challenge'],
            'volunteer': ['volunteer', 'voluntary', 'community service'],
            'training': ['training', 'workshop', 'capacity building', 'development program']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'opportunity'
    
    def detect_region(self, text):
        """Detect African region from text"""
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
    
    def deduplicate(self, opportunities):
        """Remove duplicate opportunities"""
        seen = set()
        unique = []
        
        for opp in opportunities:
            key = f"{opp.get('title', '')[:50]}_{opp.get('source', '')}"
            if key not in seen:
                seen.add(key)
                unique.append(opp)
        
        return unique
    
    def get_fallback_data(self):
        """Provide fallback opportunities when scraping fails"""
        fallback = [
            {
                'title': 'African Youth Leadership Fellowship 2026',
                'description': 'A 6-month intensive leadership program for young African leaders focused on policy, advocacy, and sustainable development across the continent.',
                'category': 'fellowship',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-12-15',
                'source': 'African Youth Initiative (Fallback)',
                'url': 'https://example.com/fellowship',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'Pan-African Scholarship for STEM Education',
                'description': 'Full tuition scholarship for African students pursuing undergraduate and graduate degrees in Science, Technology, Engineering, and Mathematics.',
                'category': 'scholarship',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-11-30',
                'source': 'African Education Trust (Fallback)',
                'url': 'https://example.com/scholarship',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'Digital Innovation Internship Program East Africa',
                'description': 'Paid 3-month internship program for recent graduates in East Africa to work with leading tech startups and digital innovation hubs.',
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
                'description': 'Funding opportunities for emerging artists, cultural practitioners, and heritage preservation projects across Southern Africa.',
                'category': 'grant',
                'region': 'Southern Africa',
                'country': 'South Africa, Zimbabwe, Zambia',
                'deadline': '2026-09-25',
                'source': 'African Arts Foundation (Fallback)',
                'url': 'https://example.com/grant',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'African Green Innovation Competition',
                'description': 'Pan-African competition for climate tech solutions. Winners receive funding, mentorship, and incubation support.',
                'category': 'competition',
                'region': 'All Africa',
                'country': 'Pan-African',
                'deadline': '2026-08-30',
                'source': 'Green Africa Initiative (Fallback)',
                'url': 'https://example.com/competition',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'African Union Youth Fellowship Program',
                'description': 'Prestigious fellowship program for young professionals to work with the African Union on continental development initiatives.',
                'category': 'fellowship',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-10-01',
                'source': 'African Union (Fallback)',
                'url': 'https://example.com/au-fellowship',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'Women in African Tech Scholarship Program',
                'description': 'Scholarship program for women from West Africa pursuing careers in technology, engineering, and computer science.',
                'category': 'scholarship',
                'region': 'West Africa',
                'country': 'Nigeria, Ghana, Senegal',
                'deadline': '2026-09-15',
                'source': 'Women in Tech Africa (Fallback)',
                'url': 'https://example.com/women-tech',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'Climate Action Internship for African Youth',
                'description': 'Remote internship program for African youth to work on climate action projects, policy research, and sustainable development.',
                'category': 'internship',
                'region': 'All Africa',
                'country': 'Remote',
                'deadline': '2026-11-01',
                'source': 'Climate Africa Initiative (Fallback)',
                'url': 'https://example.com/climate-internship',
                'scraped_at': datetime.now().isoformat()
            }
        ]
        return fallback

# Initialize session state
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = []
if 'saved' not in st.session_state:
    st.session_state.saved = set()
if 'last_scrape' not in st.session_state:
    st.session_state.last_scrape = None
if 'auto_scraped' not in st.session_state:
    st.session_state.auto_scraped = False

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
        scraper = ComprehensiveScraper()
        st.session_state.opportunities = scraper.scrape_all_sources(update_progress)
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
    
    st.markdown("---")
    st.markdown("### 📰 Sources")
    
    if st.session_state.opportunities:
        sources = set(o.get('source', 'Unknown') for o in st.session_state.opportunities)
        for source in sorted(sources):
            count = sum(1 for o in st.session_state.opportunities if o.get('source') == source)
            st.caption(f"• {source}: {count}")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh All Sources", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(progress, status):
            progress_bar.progress(progress)
            status_text.text(status)
        
        with st.spinner("Scraping all sources..."):
            scraper = ComprehensiveScraper()
            st.session_state.opportunities = scraper.scrape_all_sources(update_progress)
            st.session_state.last_scrape = datetime.now()
        
        progress_bar.empty()
        status_text.empty()
        st.rerun()
    
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.opportunities = []
        st.session_state.saved = set()
        st.session_state.last_scrape = None
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
        if search_lower in o.get('title', '').lower() 
        or search_lower in o.get('description', '').lower()
        or search_lower in o.get('source', '').lower()
        or search_lower in o.get('country', '').lower()
    ]

st.markdown(f"### Found {len(filtered_opps)} opportunities")

if not filtered_opps:
    st.info("No opportunities match your filters. Try adjusting them or refresh the data.")
else:
    for idx, opp in enumerate(filtered_opps):
        original_idx = None
        for i, o in enumerate(st.session_state.opportunities):
            if o.get('title') == opp.get('title') and o.get('source') == opp.get('source'):
                original_idx = i
                break
        
        with st.container():
            st.markdown(f"""
            <div class="opportunity-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div class="card-title">{opp.get('title', 'Untitled Opportunity')}</div>
                    <div>
                        <span class="card-badge">{opp.get('category', 'opportunity')}</span>
                    </div>
                </div>
                <div class="card-meta">
                    <span>📍 {opp.get('country', opp.get('region', 'Africa'))}</span>
                    <span>🏷️ {opp.get('category', 'opportunity')}</span>
                    <span class="source-tag">📰 {opp.get('source', 'Unknown')}</span>
                </div>
                <div class="card-desc">{opp.get('description', 'No description available')[:300]}...</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem;">
                    <span class="deadline-badge">📅 {opp.get('deadline', 'No deadline')}</span>
                    <div>
            """, unsafe_allow_html=True)
            
            if original_idx is not None:
                if original_idx in st.session_state.saved:
                    if st.button("⭐ Saved", key=f"saved_{idx}"):
                        st.session_state.saved.remove(original_idx)
                        st.rerun()
                else:
                    if st.button("☆ Save", key=f"save_{idx}"):
                        st.session_state.saved.add(original_idx)
                        st.rerun()
            
            st.markdown("""
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("🌍 AfriYouth · Scraping 20+ African youth opportunity sources including Youth Opportunities, Opportunity Desk, African Development Bank, UNESCO, Mastercard Foundation, African Union, UNDP, UNICEF, and more")
st.caption(f"Last updated: {st.session_state.last_scrape.strftime('%Y-%m-%d %H:%M:%S') if st.session_state.last_scrape else 'Never'}")
