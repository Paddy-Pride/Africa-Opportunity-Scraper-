"""
Africa Opportunity Finder - Real Web Scraper
"""

import streamlit as st
import pandas as pd
from scraper import RealScraper
import time

st.set_page_config(
    page_title="Africa Opportunity Finder",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Africa Opportunity Finder")
st.markdown("### Real Opportunities for African Youth - Scraped Live from the Web")

# Initialize scraper
scraper = RealScraper()

# Scrape button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔍 SCRAPE REAL OPPORTUNITIES NOW", use_container_width=True, type="primary"):
        with st.spinner("🌐 Scraping live websites..."):
            opportunities = scraper.scrape_all()
            st.session_state.opportunities = opportunities
            
            if opportunities:
                st.success(f"✅ Found {len(opportunities)} real opportunities!")
                st.balloons()
            else:
                st.error("❌ No opportunities found. Try again later.")

# Load or show sample data
if 'opportunities' not in st.session_state or not st.session_state.opportunities:
    # Show sample data only if no scrape done yet
    st.info("👆 Click the button above to scrape real opportunities from the web!")
    
    # Show some sample to demonstrate UI
    sample = scraper.scrape_opportunity_desk() if False else []
    
    if not sample:
        st.markdown("""
        ### How it works:
        1. Click the **"SCRAPE REAL OPPORTUNITIES NOW"** button
        2. The app will scrape live data from:
           - Opportunity Desk
           - Youth Hub Africa
           - Opportunities For Africa
           - African Union
           - United Nations
           - Mastercard Foundation
           - UNICEF
        3. Real opportunities will appear below
        """)
else:
    opportunities = st.session_state.opportunities
    
    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Opportunities", len(opportunities))
    with col2:
        sources = len(set(o.get('source', '') for o in opportunities))
        st.metric("Sources", sources)
    with col3:
        cats = len(set(o.get('category', '') for o in opportunities))
        st.metric("Categories", cats)
    with col4:
        st.metric("Status", "✅ Real Data")
    
    st.divider()
    
    # Search
    search = st.text_input("🔍 Search", placeholder="Search by title, organization, or category...")
    
    # Filter
    filtered = opportunities
    if search:
        search_lower = search.lower()
        filtered = [o for o in opportunities if 
                   search_lower in o.get('title', '').lower() or
                   search_lower in o.get('organization', '').lower() or
                   search_lower in o.get('category', '').lower()]
    
    # Display
    if filtered:
        for opp in filtered:
            with st.container():
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"### {opp.get('title', 'Untitled')}")
                    st.caption(f"🏢 {opp.get('organization', 'Unknown')} | 📂 {opp.get('category', 'General')}")
                    st.caption(f"🌍 {opp.get('country', 'Africa')} | ⏰ {opp.get('deadline', 'No deadline')}")
                    st.write(opp.get('description', '')[:300] + ('...' if len(opp.get('description', '')) > 300 else ''))
                    
                    url = opp.get('url', '#')
                    if url and url != '#':
                        st.markdown(f"[📝 Apply Now]({url})")
                    
                    if opp.get('verified', False):
                        st.caption("✅ Verified Opportunity")
                with cols[1]:
                    st.caption(f"📡 Source: {opp.get('source', 'Unknown')}")
                    st.caption(f"✅ Real Data")
                st.divider()
    else:
        st.info("No matching opportunities found. Try different search terms.")
