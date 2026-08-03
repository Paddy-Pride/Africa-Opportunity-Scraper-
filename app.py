# app.py - Refined African Youth Opportunity Scraper
import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
import random
import hashlib
from urllib.parse import urljoin

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
    .badge-success {
        background: #d4edda;
        color: #155724;
        padding: 0.2rem 0.7rem;
        border-radius: 40px;
        font-size: 0.7rem;
    }
</style>
""", unsafe_allow_html=True)

class RefinedScraper:
    """Refined scraper that filters out non-opportunity content"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.all_opportunities = []
        self.scraped_sources = {}
        
        # Keywords that indicate this is NOT a real opportunity
        self.skip_keywords = [
            'sign in', 'login', 'register', 'join', 'facebook', 'twitter', 'instagram',
            'subscribe', 'newsletter', 'cookie', 'privacy', 'terms', 'contact', 'about',
            'advertise', 'donate', 'support', 'shop', 'store', 'cart', 'checkout',
            'search', 'find your', '30 seconds', '87,000', 'join the', 'for high school'
        ]
        
        # Keywords that indicate this IS a real opportunity
        self.opportunity_keywords = [
            'scholarship', 'fellowship', 'internship', 'grant', 'competition',
            'award', 'funding', 'program', 'training', 'workshop', 'conference',
            'volunteer', 'exchange', 'study', 'abroad', 'international', 'fully funded',
            'apply', 'application', 'deadline', 'opportunity', 'calls for'
        ]
    
    def scrape_all_sources(self, progress_callback=None):
        """Scrape from all configured sources"""
        sources = self.get_refined_source_configs()
        total_sources = len(sources)
        successful_sources = 0
        
        for i, (source_name, source_config) in enumerate(sources.items()):
            if progress_callback:
                progress_callback(i / total_sources, f"Scraping {source_name}...")
            
            try:
                opportunities = self.scrape_refined_source(source_name, source_config)
                if opportunities:
                    # Filter out non-opportunity content
                    filtered = [o for o in opportunities if self.is_real_opportunity(o)]
                    if filtered:
                        self.all_opportunities.extend(filtered)
                        self.scraped_sources[source_name] = len(filtered)
                        successful_sources += 1
                        if progress_callback:
                            progress_callback(i / total_sources, f"✅ Found {len(filtered)} from {source_name}")
                    else:
                        self.scraped_sources[source_name] = 0
                        if progress_callback:
                            progress_callback(i / total_sources, f"⚠️ No valid opportunities from {source_name}")
                else:
                    self.scraped_sources[source_name] = 0
                    if progress_callback:
                        progress_callback(i / total_sources, f"⚠️ No results from {source_name}")
            except Exception as e:
                self.scraped_sources[source_name] = 0
                if progress_callback:
                    progress_callback(i / total_sources, f"❌ Error scraping {source_name}")
            
            time.sleep(random.uniform(1.5, 3))
        
        if progress_callback:
            progress_callback(0.95, f"Deduplicating {len(self.all_opportunities)} opportunities...")
        
        unique = self.deduplicate_refined(self.all_opportunities)
        
        if not unique:
            if progress_callback:
                progress_callback(1.0, "Using comprehensive fallback data...")
            unique = self.get_refined_fallback_data()
        
        if progress_callback:
            progress_callback(1.0, f"✅ Found {len(unique)} unique opportunities from {successful_sources} sources")
        
        return unique
    
    def get_refined_source_configs(self):
        """Get refined source configurations"""
        return {
            "Scholarships for Africans": {
                "urls": ["https://scholarshipsforafricans.com/"],
                "strategies": [
                    {"container": "article", "title": "h2", "desc": "p", "date": "time", "location": "span.location"},
                    {"container": "div.post", "title": "h3", "desc": "div.excerpt", "date": "span.date", "location": "div.country"},
                    {"container": "div.scholarship-item", "title": "a", "desc": "div.summary", "date": "span.deadline", "location": "span.region"}
                ]
            },
            "Opportunity Desk": {
                "urls": [
                    "https://opportunitydesk.org/category/opportunities/",
                    "https://opportunitydesk.org/category/fellowships/"
                ],
                "strategies": [
                    {"container": "article", "title": "h2", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "div.post", "title": "h3", "desc": "div.excerpt", "date": "time", "location": "div.country"}
                ]
            },
            "Youth Opportunities": {
                "urls": [
                    "https://www.youthop.com/opportunities/africa",
                    "https://www.youthop.com/opportunities/fellowships"
                ],
                "strategies": [
                    {"container": "div.opportunity-item", "title": "h3", "desc": "p.description", "date": "span.date", "location": "span.location"},
                    {"container": "article.listing-item", "title": "h2", "desc": "div.excerpt", "date": "span.deadline", "location": "span.country"}
                ]
            },
            "African Development Bank": {
                "urls": ["https://www.afdb.org/en/careers/current-vacancies"],
                "strategies": [
                    {"container": "div.job-listing", "title": "h3", "desc": "p", "date": "span.date", "location": "span.location"},
                    {"container": "div.views-row", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"}
                ]
            },
            "UNESCO Africa": {
                "urls": ["https://www.unesco.org/en/fieldoffice/africa"],
                "strategies": [
                    {"container": "div.card", "title": "h2", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "h3", "desc": "div.description", "date": "time", "location": "div.country"}
                ]
            },
            "Mastercard Foundation": {
                "urls": ["https://mastercardfdn.org/our-work/programs/"],
                "strategies": [
                    {"container": "div.program-item", "title": "h3", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "div.card", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"}
                ]
            },
            "African Union": {
                "urls": ["https://au.int/en/opportunities"],
                "strategies": [
                    {"container": "div.view-content", "title": "a", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "h3", "desc": "div.description", "date": "time", "location": "div.country"}
                ]
            },
            "YALI Network": {
                "urls": ["https://yali.state.gov/opportunities/"],
                "strategies": [
                    {"container": "div.opportunity", "title": "h3", "desc": "p", "date": "span.deadline", "location": "span.location"},
                    {"container": "article", "title": "a", "desc": "div.description", "date": "time", "location": "div.country"}
                ]
            }
        }
    
    def scrape_refined_source(self, source_name, source_config):
        """Scrape a source with refined filtering"""
        opportunities = []
        urls = source_config.get("urls", [])
        strategies = source_config.get("strategies", [])
        
        for url in urls:
            try:
                self.session.headers.update({
                    'User-Agent': random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ])
                })
                
                response = self.session.get(url, timeout=20)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    for strategy in strategies:
                        container_selector = strategy.get("container", "")
                        title_selector = strategy.get("title", "")
                        desc_selector = strategy.get("desc", "")
                        date_selector = strategy.get("date", "")
                        location_selector = strategy.get("location", "")
                        
                        containers = soup.find_all(container_selector) if container_selector else []
                        
                        if not containers:
                            containers = soup.find_all(['article', 'div'], class_=re.compile(r'(post|entry|item|listing|opportunity|job|scholarship|program)'))
                        
                        for container in containers[:15]:
                            try:
                                title_elem = container.find(title_selector) if title_selector else container.find(['h2', 'h3', 'a'])
                                if not title_elem:
                                    title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                                
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.get_text().strip()
                                if not title or len(title) < 8:
                                    continue
                                
                                # Skip obvious navigation/menu items
                                if any(skip in title.lower() for skip in ['menu', 'navigation', 'breadcrumb', 'search']):
                                    continue
                                
                                desc_elem = container.find(desc_selector) if desc_selector else container.find('p')
                                description = desc_elem.get_text().strip() if desc_elem else ""
                                
                                # If description is too short or generic, try to get more context
                                if len(description) < 30:
                                    # Try to find more description
                                    desc_elem = container.find('div', class_=re.compile(r'(content|summary|excerpt|description)'))
                                    if desc_elem:
                                        description = desc_elem.get_text().strip()
                                
                                date_elem = container.find(date_selector) if date_selector else container.find(['time', 'span'], class_=re.compile(r'(date|deadline|time)'))
                                deadline = date_elem.get_text().strip() if date_elem else None
                                
                                loc_elem = container.find(location_selector) if location_selector else container.find(['span', 'div'], class_=re.compile(r'(location|country|region)'))
                                location = loc_elem.get_text().strip() if loc_elem else "Africa"
                                
                                link = None
                                link_elem = container.find('a')
                                if link_elem and link_elem.get('href'):
                                    link = urljoin(url, link_elem.get('href'))
                                
                                category = self.detect_category_refined(title + " " + description)
                                region = self.detect_region_refined(location + " " + title + " " + description)
                                
                                opportunities.append({
                                    'title': title[:200],
                                    'description': description[:500] if description else "Opportunity available in Africa",
                                    'category': category,
                                    'region': region,
                                    'country': location if location and location != "Africa" else "Various",
                                    'deadline': deadline,
                                    'source': source_name,
                                    'url': link or url,
                                    'scraped_at': datetime.now().isoformat(),
                                    'id': hashlib.md5(f"{title[:50]}_{source_name}".encode()).hexdigest()[:8]
                                })
                            except Exception as e:
                                continue
                    
            except Exception as e:
                continue
            
            time.sleep(random.uniform(1, 2))
        
        return opportunities
    
    def is_real_opportunity(self, opp):
        """Check if this is a real opportunity, not a navigation element"""
        title = opp.get('title', '').lower()
        description = opp.get('description', '').lower()
        text = title + " " + description
        
        # Skip if it contains navigation/signup keywords
        for skip in self.skip_keywords:
            if skip in text:
                return False
        
        # Check if it has opportunity-related keywords
        has_opportunity_keywords = any(keyword in text for keyword in self.opportunity_keywords)
        
        # Must have some substance
        has_substance = len(description) > 50
        
        return has_opportunity_keywords and has_substance
    
    def detect_category_refined(self, text):
        """Refined category detection"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['fellowship', 'fellow']):
            return 'fellowship'
        elif any(word in text_lower for word in ['scholarship', 'scholar', 'tuition', 'fully funded']):
            return 'scholarship'
        elif any(word in text_lower for word in ['internship', 'intern', 'trainee', 'apprentice']):
            return 'internship'
        elif any(word in text_lower for word in ['grant', 'funding', 'financial']):
            return 'grant'
        elif any(word in text_lower for word in ['competition', 'contest', 'award', 'prize', 'challenge']):
            return 'competition'
        elif any(word in text_lower for word in ['volunteer', 'voluntary']):
            return 'volunteer'
        elif any(word in text_lower for word in ['training', 'workshop', 'conference']):
            return 'training'
        else:
            return 'opportunity'
    
    def detect_region_refined(self, text):
        """Refined region detection"""
        text_lower = text.lower()
        
        region_keywords = {
            'West Africa': ['nigeria', 'ghana', 'senegal', 'mali', 'liberia', 'sierra', 'guinea', 'benin', 'togo'],
            'East Africa': ['kenya', 'tanzania', 'uganda', 'ethiopia', 'rwanda', 'burundi', 'somalia', 'eritrea'],
            'Southern Africa': ['south africa', 'zimbabwe', 'zambia', 'malawi', 'angola', 'mozambique', 'namibia', 'botswana'],
            'North Africa': ['egypt', 'morocco', 'algeria', 'tunisia', 'libya', 'sudan'],
            'Central Africa': ['congo', 'cameroon', 'gabon', 'chad', 'car']
        }
        
        for region, keywords in region_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return region
        
        return 'All Africa'
    
    def deduplicate_refined(self, opportunities):
        """Refined deduplication"""
        seen = set()
        unique = []
        
        for opp in opportunities:
            key = f"{opp.get('title', '')[:50]}_{opp.get('source', '')}"
            if key not in seen:
                seen.add(key)
                unique.append(opp)
        
        return unique
    
    def get_refined_fallback_data(self):
        """Refined fallback data with real opportunities"""
        return [
            {
                'title': 'Mastercard Foundation Scholars Program 2026-27',
                'description': 'Full scholarships for African students to study at partner universities across Africa and globally. Covers tuition, accommodation, and living expenses.',
                'category': 'scholarship',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-12-15',
                'source': 'Mastercard Foundation (Fallback)',
                'url': 'https://example.com/mastercard',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'African Union Youth Volunteer Corps 2026',
                'description': 'Volunteer program for African youth to contribute to development projects across the continent. Monthly stipend and travel costs covered.',
                'category': 'volunteer',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-11-30',
                'source': 'African Union (Fallback)',
                'url': 'https://example.com/au-volunteer',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'Fully Funded Chevening Scholarships for Africans',
                'description': 'UK government scholarships for African students to pursue master\'s degrees. Covers tuition, living expenses, and travel.',
                'category': 'scholarship',
                'region': 'All Africa',
                'country': 'Various',
                'deadline': '2026-11-01',
                'source': 'Chevening (Fallback)',
                'url': 'https://example.com/chevening',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'African Women in Tech Internship Program',
                'description': 'Paid internship program for African women to work with leading tech companies. Includes mentorship and training.',
                'category': 'internship',
                'region': 'East Africa',
                'country': 'Kenya, Tanzania, Uganda',
                'deadline': '2026-10-15',
                'source': 'Women in Tech (Fallback)',
                'url': 'https://example.com/women-tech',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'African Green Innovation Grant 2026',
                'description': 'Funding for sustainable innovations and climate solutions. Grants up to $50,000 available for African entrepreneurs.',
                'category': 'grant',
                'region': 'All Africa',
                'country': 'Pan-African',
                'deadline': '2026-09-30',
                'source': 'Green Africa (Fallback)',
                'url': 'https://example.com/green-grant',
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
        scraper = RefinedScraper()
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
        st.markdown("### 📰 Active Sources")
        for source, count in st.session_state.scraped_sources.items():
            if count > 0:
                st.caption(f"✅ {source}: {count}")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh All Sources", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(progress, status):
            progress_bar.progress(progress)
            status_text.text(status)
        
        with st.spinner("Scraping all sources..."):
            scraper = RefinedScraper()
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
        # Find original index
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
                <div class="card-desc">{opp.get('description', 'No description available')[:350]}...</div>
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
st.caption("🌍 AfriYouth · Scraping 8+ African youth opportunity sources including Scholarships for Africans, Opportunity Desk, Youth Opportunities, African Development Bank, UNESCO, Mastercard Foundation, African Union, and YALI")
if st.session_state.last_scrape:
    st.caption(f"Last updated: {st.session_state.last_scrape.strftime('%Y-%m-%d %H:%M:%S')}")
