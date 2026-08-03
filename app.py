# app.py - Streamlit version of African Youth Opportunity Scraper
import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import pandas as pd
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
</style>
""", unsafe_allow_html=True)

class OpportunityScraper:
    """Real web scraper for African youth opportunities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
    def scrape_all_sources(self):
        """Scrape all opportunity sources"""
        all_opportunities = []
        
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        sources = [
            ('Youth Opportunities', self.scrape_youth_opportunities),
            ('African Development Bank', self.scrape_afdb_opportunities),
            ('UNESCO Africa', self.scrape_unesco_africa),
            ('Mastercard Foundation', self.scrape_mastercard_foundation),
            ('African Union', self.scrape_african_union)
        ]
        
        for i, (source_name, scrape_func) in enumerate(sources):
            status_text.text(f"Scraping {source_name}...")
            try:
                opps = scrape_func()
                all_opportunities.extend(opps)
                logger.info(f"Scraped {len(opps)} from {source_name}")
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {str(e)}")
            
            progress_bar.progress((i + 1) / len(sources))
        
        status_text.text("Deduplicating opportunities...")
        unique_opps = self.deduplicate_opportunities(all_opportunities)
        
        status_text.text(f"Found {len(unique_opps)} unique opportunities")
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()
        
        return unique_opps
    
    def scrape_youth_opportunities(self):
        """Scrape from Youth Opportunities platform"""
        opportunities = []
        urls = [
            'https://www.youthop.com/opportunities/africa',
            'https://www.youthop.com/opportunities/fellowships',
            'https://www.youthop.com/opportunities/scholarships'
        ]
        
        for url in urls:
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    listings = soup.find_all('div', class_='opportunity-item') or soup.find_all('article', class_='listing-item')
                    
                    for listing in listings[:8]:
                        try:
                            title_elem = listing.find('h3') or listing.find('h2') or listing.find('a')
                            title = title_elem.get_text().strip() if title_elem else "Youth Opportunity"
                            
                            desc_elem = listing.find('p', class_='description') or listing.find('div', class_='excerpt')
                            description = desc_elem.get_text().strip() if desc_elem else "Youth opportunity in Africa"
                            
                            date_elem = listing.find('span', class_='date') or listing.find('div', class_='deadline')
                            deadline = date_elem.get_text().strip() if date_elem else None
                            
                            location_elem = listing.find('span', class_='location') or listing.find('div', class_='country')
                            location = location_elem.get_text().strip() if location_elem else "Africa"
                            
                            category = self.detect_category(title)
                            
                            opportunities.append({
                                'title': title[:200],
                                'description': description[:500],
                                'category': category,
                                'region': self.detect_region(location),
                                'country': location,
                                'deadline': deadline,
                                'source': 'Youth Opportunities',
                                'url': url,
                                'scraped_at': datetime.now().isoformat()
                            })
                        except Exception as e:
                            continue
            except Exception as e:
                logger.warning(f"Error scraping {url}: {str(e)}")
                continue
        
        return opportunities
    
    def scrape_afdb_opportunities(self):
        """Scrape from African Development Bank"""
        opportunities = []
        try:
            url = 'https://www.afdb.org/en/careers'
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                job_listings = soup.find_all('div', class_='job-listing') or soup.find_all('article', class_='job')
                
                for job in job_listings[:8]:
                    try:
                        title_elem = job.find('h3') or job.find('a')
                        title = title_elem.get_text().strip() if title_elem else "AfDB Opportunity"
                        
                        desc_elem = job.find('p') or job.find('div', class_='description')
                        description = desc_elem.get_text().strip() if desc_elem else "African Development Bank career opportunity"
                        
                        opportunities.append({
                            'title': title[:200],
                            'description': description[:500],
                            'category': 'internship',
                            'region': 'all',
                            'country': 'Various (Africa)',
                            'deadline': None,
                            'source': 'African Development Bank',
                            'url': url,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Error scraping AfDB: {str(e)}")
        
        return opportunities
    
    def scrape_unesco_africa(self):
        """Scrape from UNESCO Africa"""
        opportunities = []
        try:
            url = 'https://www.unesco.org/en/fieldoffice/africa'
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                items = soup.find_all('div', class_='card') or soup.find_all('article')
                
                for item in items[:8]:
                    try:
                        title_elem = item.find('h2') or item.find('h3')
                        title = title_elem.get_text().strip() if title_elem else "UNESCO Africa Opportunity"
                        
                        desc_elem = item.find('p') or item.find('div', class_='excerpt')
                        description = desc_elem.get_text().strip() if desc_elem else "UNESCO opportunity in Africa"
                        
                        opportunities.append({
                            'title': title[:200],
                            'description': description[:500],
                            'category': 'scholarship',
                            'region': 'all',
                            'country': 'Various (Africa)',
                            'deadline': None,
                            'source': 'UNESCO Africa',
                            'url': url,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Error scraping UNESCO: {str(e)}")
        
        return opportunities
    
    def scrape_mastercard_foundation(self):
        """Scrape from Mastercard Foundation"""
        opportunities = []
        try:
            url = 'https://mastercardfdn.org/our-work/programs/'
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                programs = soup.find_all('div', class_='program-item') or soup.find_all('div', class_='card')
                
                for program in programs[:8]:
                    try:
                        title_elem = program.find('h3') or program.find('a')
                        title = title_elem.get_text().strip() if title_elem else "Mastercard Foundation Opportunity"
                        
                        desc_elem = program.find('p') or program.find('div', class_='description')
                        description = desc_elem.get_text().strip() if desc_elem else "Mastercard Foundation opportunity in Africa"
                        
                        opportunities.append({
                            'title': title[:200],
                            'description': description[:500],
                            'category': 'scholarship',
                            'region': 'all',
                            'country': 'Various (Africa)',
                            'deadline': None,
                            'source': 'Mastercard Foundation',
                            'url': url,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Error scraping Mastercard Foundation: {str(e)}")
        
        return opportunities
    
    def scrape_african_union(self):
        """Scrape from African Union"""
        opportunities = []
        try:
            url = 'https://au.int/en/opportunities'
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                listings = soup.find_all('div', class_='view-content') or soup.find_all('article')
                
                for listing in listings[:8]:
                    try:
                        title_elem = listing.find('a') or listing.find('h3')
                        title = title_elem.get_text().strip() if title_elem else "African Union Opportunity"
                        
                        desc_elem = listing.find('p') or listing.find('div', class_='description')
                        description = desc_elem.get_text().strip() if desc_elem else "African Union opportunity"
                        
                        opportunities.append({
                            'title': title[:200],
                            'description': description[:500],
                            'category': 'fellowship',
                            'region': 'all',
                            'country': 'Various (Africa)',
                            'deadline': None,
                            'source': 'African Union',
                            'url': url,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Error scraping African Union: {str(e)}")
        
        return opportunities
    
    def detect_category(self, title):
        """Detect category from title"""
        title_lower = title.lower()
        if 'fellowship' in title_lower or 'fellow' in title_lower:
            return 'fellowship'
        elif 'scholarship' in title_lower or 'scholar' in title_lower:
            return 'scholarship'
        elif 'intern' in title_lower or 'trainee' in title_lower:
            return 'internship'
        elif 'grant' in title_lower or 'fund' in title_lower:
            return 'grant'
        elif 'competition' in title_lower or 'award' in title_lower:
            return 'competition'
        else:
            return 'opportunity'
    
    def detect_region(self, location):
        """Detect African region from location string"""
        location_lower = location.lower()
        west_africa = ['nigeria', 'ghana', 'senegal', 'mali', 'côte', 'ivory', 'liberia', 'sierra', 'guinea']
        east_africa = ['kenya', 'tanzania', 'uganda', 'ethiopia', 'rwanda', 'burundi', 'somalia']
        south_africa = ['south africa', 'zimbabwe', 'zambia', 'malawi', 'angola', 'mozambique']
        north_africa = ['egypt', 'morocco', 'algeria', 'tunisia', 'libya', 'sudan']
        central_africa = ['congo', 'cameroon', 'gabon', 'chad', 'car', 'equatorial']
        
        if any(country in location_lower for country in west_africa):
            return 'West Africa'
        elif any(country in location_lower for country in east_africa):
            return 'East Africa'
        elif any(country in location_lower for country in south_africa):
            return 'Southern Africa'
        elif any(country in location_lower for country in north_africa):
            return 'North Africa'
        elif any(country in location_lower for country in central_africa):
            return 'Central Africa'
        else:
            return 'All Africa'
    
    def deduplicate_opportunities(self, opportunities):
        """Remove duplicate opportunities based on title similarity"""
        unique = []
        seen_titles = set()
        
        for opp in opportunities:
            title_key = opp['title'].lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique.append(opp)
        
        return unique

# Initialize session state
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = []
if 'saved' not in st.session_state:
    st.session_state.saved = set()
if 'last_scrape' not in st.session_state:
    st.session_state.last_scrape = None

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

# Sidebar - Filters and Controls
with st.sidebar:
    st.markdown("### 🎯 Filters")
    
    category_filter = st.selectbox(
        "Category",
        ["All", "fellowship", "scholarship", "internship", "grant", "competition", "opportunity"]
    )
    
    region_filter = st.selectbox(
        "Region",
        ["All", "West Africa", "East Africa", "Southern Africa", "North Africa", "Central Africa", "All Africa"]
    )
    
    search_term = st.text_input("🔍 Search", placeholder="Search opportunities...")
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    
    # Stats
    total = len(st.session_state.opportunities)
    saved_count = len(st.session_state.saved)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Saved", saved_count)
    
    st.markdown("---")
    
    # Action buttons
    if st.button("🔄 Refresh Opportunities", use_container_width=True):
        with st.spinner("Scraping opportunities..."):
            scraper = OpportunityScraper()
            st.session_state.opportunities = scraper.scrape_all_sources()
            st.session_state.last_scrape = datetime.now()
            st.rerun()
    
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.opportunities = []
        st.session_state.saved = set()
        st.session_state.last_scrape = None
        st.rerun()
    
    if st.session_state.last_scrape:
        st.caption(f"Last scrape: {st.session_state.last_scrape.strftime('%H:%M:%S')}")

# Main content - Filter and display opportunities
# Filter opportunities
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
    ]

# Display count
st.markdown(f"### Found {len(filtered_opps)} opportunities")

# Display opportunities
if not filtered_opps:
    st.info("No opportunities found. Try adjusting your filters or click 'Refresh Opportunities' to scrape new data.")
else:
    for idx, opp in enumerate(filtered_opps):
        # Get the original index for save functionality
        original_idx = st.session_state.opportunities.index(opp) if opp in st.session_state.opportunities else None
        
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
            
            # Save button
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
st.caption("🌍 AfriYouth · Automatically scraped from Youth Opportunities, African Development Bank, UNESCO Africa, Mastercard Foundation, and African Union")
st.caption(f"Last updated: {st.session_state.last_scrape.strftime('%Y-%m-%d %H:%M:%S') if st.session_state.last_scrape else 'Never'}")
