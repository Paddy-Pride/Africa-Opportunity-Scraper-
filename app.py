"""
Africa Opportunity Finder - Simple Working Version
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import json
import os

# Set page config
st.set_page_config(
    page_title="Africa Opportunity Finder",
    page_icon="🌍",
    layout="wide"
)

# Sample opportunities (fallback if scraping fails)
SAMPLE_OPPORTUNITIES = [
    {
        'title': 'African Union Internship Program 2024',
        'organization': 'African Union',
        'category': 'Internships',
        'country': 'Ethiopia',
        'deadline': '2024-12-31',
        'description': 'The African Union offers internship opportunities for young Africans to gain professional experience.',
        'url': 'https://www.africanunion.org/internships'
    },
    {
        'title': 'UN Young Professionals Programme',
        'organization': 'United Nations',
        'category': 'Jobs',
        'country': 'Various',
        'deadline': '2024-09-30',
        'description': 'The UN Young Professionals Programme offers opportunities for qualified individuals to start a career.',
        'url': 'https://www.un.org/young-professionals'
    },
    {
        'title': 'World Bank Junior Professional Associates Program',
        'organization': 'World Bank',
        'category': 'Jobs',
        'country': 'Various',
        'deadline': '2024-10-15',
        'description': 'The JPA program provides recent graduates with opportunities to gain professional experience.',
        'url': 'https://www.worldbank.org/jpa'
    },
    {
        'title': 'Mastercard Foundation Scholars Program',
        'organization': 'Mastercard Foundation',
        'category': 'Scholarships',
        'country': 'Various',
        'deadline': '2025-01-15',
        'description': 'Scholarships for talented young Africans to pursue higher education.',
        'url': 'https://www.mastercardfdn.org/scholars'
    },
    {
        'title': 'Google Africa Internship Program',
        'organization': 'Google',
        'category': 'Internships',
        'country': 'Various',
        'deadline': '2024-12-01',
        'description': 'Google offers internship opportunities for African students in technology and business.',
        'url': 'https://careers.google.com/africa-internships'
    },
    {
        'title': 'Microsoft Africa Development Center Internships',
        'organization': 'Microsoft',
        'category': 'Internships',
        'country': 'Various',
        'deadline': '2024-11-15',
        'description': 'Microsoft offers internship opportunities for African students in software engineering.',
        'url': 'https://careers.microsoft.com/africa-internships'
    },
    {
        'title': 'UNICEF Internship Program',
        'organization': 'UNICEF',
        'category': 'Internships',
        'country': 'Various',
        'deadline': '2024-12-15',
        'description': 'UNICEF offers internship opportunities for students interested in child welfare.',
        'url': 'https://www.unicef.org/careers/internships'
    },
    {
        'title': 'British Council Scholarships',
        'organization': 'British Council',
        'category': 'Scholarships',
        'country': 'Various',
        'deadline': '2025-01-31',
        'description': 'British Council offers various scholarships and programs for African students.',
        'url': 'https://www.britishcouncil.org/study-uk/scholarships'
    }
]

class SimpleScraper:
    """Simple scraper that actually works"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_opportunity(self, url, name, org_type):
        """Scrape a single opportunity page"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Look for opportunity content
                content = soup.get_text()[:1000]
                
                # Try to find deadline
                deadline = 'N/A'
                deadline_keywords = ['deadline', 'closing date', 'apply by', 'due date']
                for keyword in deadline_keywords:
                    for text in soup.find_all(text=True):
                        if keyword in text.lower():
                            # Extract date if possible
                            words = text.split()
                            for word in words:
                                if '/' in word or '-' in word:
                                    deadline = word
                                    break
                            break
                
                return {
                    'title': soup.title.string if soup.title else f'{name} Opportunity',
                    'organization': name,
                    'category': org_type,
                    'country': 'Africa',
                    'deadline': deadline,
                    'description': content[:500],
                    'url': url,
                    'verified': True if 'apply' in content.lower() else False
                }
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        return None
    
    def scrape_multiple(self, urls):
        """Scrape multiple URLs"""
        opportunities = []
        
        for url in urls:
            # Extract name from URL
            name = url.replace('https://', '').replace('http://', '').split('/')[0].split('.')[0]
            if '.' in name:
                name = name.split('.')[0].capitalize()
            
            # Try to scrape
            opp = self.scrape_opportunity(url, name, 'General')
            if opp:
                opportunities.append(opp)
            
            # Don't overwhelm servers
            import time
            time.sleep(0.5)
        
        return opportunities

def main():
    st.title("🌍 Africa Opportunity Finder")
    st.markdown("### Discover Opportunities for African Youth")
    
    # Initialize scraper
    scraper = SimpleScraper()
    
    # Sources to scrape
    SOURCES = [
        ('https://www.africanunion.org', 'African Union', 'Grants'),
        ('https://www.un.org', 'United Nations', 'Jobs'),
        ('https://www.worldbank.org', 'World Bank', 'Jobs'),
        ('https://www.afdb.org', 'African Development Bank', 'Jobs'),
        ('https://www.mastercardfdn.org', 'Mastercard Foundation', 'Scholarships'),
        ('https://www.google.com', 'Google', 'Jobs'),
        ('https://www.microsoft.com', 'Microsoft', 'Jobs'),
        ('https://www.unicef.org', 'UNICEF', 'Jobs'),
        ('https://www.unesco.org', 'UNESCO', 'Jobs'),
        ('https://www.undp.org', 'UNDP', 'Jobs'),
        ('https://www.britishcouncil.org', 'British Council', 'Scholarships'),
    ]
    
    # Scrape button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        scrape_now = st.button("🔍 Scrape Latest Opportunities", use_container_width=True)
    
    # Load opportunities
    if 'opportunities' not in st.session_state:
        st.session_state.opportunities = SAMPLE_OPPORTUNITIES
    
    if scrape_now:
        with st.spinner("🌐 Scraping opportunities..."):
            opportunities = []
            
            # Try to scrape each source
            for url, name, category in SOURCES:
                try:
                    opp = scraper.scrape_opportunity(url, name, category)
                    if opp:
                        opportunities.append(opp)
                except Exception as e:
                    print(f"Error: {e}")
            
            # If we got some opportunities, use them; otherwise use sample
            if opportunities:
                st.session_state.opportunities = opportunities
                st.success(f"✅ Found {len(opportunities)} opportunities!")
            else:
                st.warning("⚠️ Using sample data. Could not scrape websites.")
                st.session_state.opportunities = SAMPLE_OPPORTUNITIES
    
    # Display opportunities
    opportunities = st.session_state.opportunities
    
    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Opportunities", len(opportunities))
    with col2:
        verified = sum(1 for o in opportunities if o.get('verified', False))
        st.metric("Verified", verified)
    with col3:
        orgs = len(set(o.get('organization', '') for o in opportunities))
        st.metric("Organizations", orgs)
    with col4:
        categories = len(set(o.get('category', '') for o in opportunities))
        st.metric("Categories", categories)
    
    st.divider()
    
    # Search and filter
    search = st.text_input("🔍 Search opportunities", placeholder="Search by title, organization, or category...")
    
    # Filter
    filtered = opportunities
    if search:
        search_lower = search.lower()
        filtered = [o for o in opportunities if 
                   search_lower in o.get('title', '').lower() or
                   search_lower in o.get('organization', '').lower() or
                   search_lower in o.get('category', '').lower() or
                   search_lower in o.get('country', '').lower()]
    
    # Display cards
    if not filtered:
        st.info("No opportunities found. Try adjusting your search.")
    else:
        for opp in filtered:
            with st.container():
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"### {opp.get('title', 'Untitled')}")
                    st.caption(f"🏢 {opp.get('organization', 'Unknown')} | 📂 {opp.get('category', 'General')}")
                    st.caption(f"🌍 {opp.get('country', 'Africa')} | ⏰ {opp.get('deadline', 'No deadline')}")
                    st.write(opp.get('description', '')[:300] + '...')
                    
                    url = opp.get('url', '#')
                    st.markdown(f"[📝 Apply Now]({url})")
                    
                    if opp.get('verified', False):
                        st.caption("✅ Verified")
                    else:
                        st.caption("⚠️ Not Verified")
                
                with cols[1]:
                    # Source
                    st.caption(f"Source: {opp.get('organization', 'Unknown')}")
                
                st.divider()

if __name__ == "__main__":
    main()
