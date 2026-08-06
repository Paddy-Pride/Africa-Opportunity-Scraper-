"""
Africa Opportunity Finder - Production Streamlit Application
Enterprise-grade opportunity discovery platform for African youth
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

from scraper import DatabaseManager, OpportunityScraper

# Page configuration
st.set_page_config(
    page_title="Africa Opportunity Finder",
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
            color: #1a3c6e;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #4a6fa5;
            margin-bottom: 2rem;
        }
        .opportunity-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 5px solid #1a3c6e;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-card {
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stButton > button {
            width: 100%;
            background-color: #1a3c6e;
            color: white;
            font-weight: 600;
            border-radius: 8px;
            padding: 10px;
        }
        .verified-badge {
            background-color: #28a745;
            color: white;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
        }
        .source-tag {
            background-color: #e9ecef;
            padding: 2px 10px;
            border-radius: 15px;
            font-size: 0.75rem;
            color: #495057;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize services
@st.cache_resource
def init_services():
    db = DatabaseManager()
    scraper = OpportunityScraper(db)
    return db, scraper

db_manager, scraper = init_services()

# Session state
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = db_manager.get_opportunities(limit=200)
if 'last_scrape' not in st.session_state:
    st.session_state.last_scrape = None
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False

def main():
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/africa.png", width=80)
        st.markdown("### Africa Opportunity Finder")
        st.markdown("---")
        
        if st.button("Scrape All", use_container_width=True):
            st.session_state.scraping_in_progress = True
            with st.spinner("Scraping all sources..."):
                try:
                    result = scraper.scrape_all_sources()
                    st.session_state.last_scrape = datetime.now()
                    st.session_state.opportunities = db_manager.get_opportunities(limit=200)
                    st.success(f"Found {result['total_opportunities']} new opportunities")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            st.session_state.scraping_in_progress = False
            st.rerun()
        
        st.markdown("---")
        
        pages = ["Home", "Browse", "Dashboard", "Sources"]
        selection = st.radio("Navigation", pages)
        st.session_state.page = selection.lower()
        
        st.markdown("---")
        
        st.markdown("### Your Profile")
        user_profile = st.text_area(
            "Skills, interests, goals",
            value=st.session_state.user_profile,
            placeholder="Example: Computer Science student interested in AI internships",
            height=80
        )
        if st.button("Update Profile", use_container_width=True):
            st.session_state.user_profile = user_profile
            st.success("Profile updated!")
            st.rerun()
        
        st.markdown("---")
        st.caption(f"Last updated: {st.session_state.last_scrape.strftime('%Y-%m-%d %H:%M') if st.session_state.last_scrape else 'Never'}")
        st.caption(f"Total: {len(st.session_state.opportunities)}")
    
    # Page routing
    page = st.session_state.page
    if page == "home":
        render_home()
    elif page == "browse":
        render_browse()
    elif page == "dashboard":
        render_dashboard()
    elif page == "sources":
        render_sources()

def render_home():
    st.markdown('<p class="main-header">Latest African Opportunities</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Discover verified opportunities for African youth</p>', unsafe_allow_html=True)
    
    if not st.session_state.opportunities:
        st.info("No opportunities found. Click 'Scrape All' to fetch opportunities.")
        return
    
    stats = db_manager.get_statistics()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['total_opportunities']}</h3>
                <p>Total Opportunities</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['verified']}</h3>
                <p>Verified</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['active_sources']}</h3>
                <p>Active Sources</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if st.session_state.last_scrape:
            hours = (datetime.now() - st.session_state.last_scrape).total_seconds() / 3600
            st.markdown(f"""
                <div class="metric-card">
                    <h3>{int(hours)}h</h3>
                    <p>Since Last Update</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    display_count = min(10, len(st.session_state.opportunities))
    st.subheader(f"Recent Opportunities ({display_count})")
    
    for opp in st.session_state.opportunities[:display_count]:
        display_opportunity_card(opp)

def render_browse():
    st.markdown('<p class="main-header">Browse Opportunities</p>', unsafe_allow_html=True)
    
    if not st.session_state.opportunities:
        st.info("No opportunities available. Please scrape sources first.")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("Search", placeholder="Search by title...")
    
    with col2:
        categories = list(set(opp.get('category', 'Other') for opp in st.session_state.opportunities))
        categories.sort()
        category_filter = st.selectbox("Category", ["All"] + categories)
    
    with col3:
        countries = list(set(opp.get('country', 'Africa') for opp in st.session_state.opportunities if opp.get('country')))
        countries = [c for c in countries if c and c != 'Global']
        countries.sort()
        country_filter = st.selectbox("Country", ["All"] + countries)
    
    # Apply filters
    filtered = st.session_state.opportunities.copy()
    
    if search_query:
        search_lower = search_query.lower()
        filtered = [opp for opp in filtered if 
                   search_lower in opp.get('title', '').lower() or 
                   search_lower in opp.get('organization', '').lower()]
    
    if category_filter != "All":
        filtered = [opp for opp in filtered if opp.get('category') == category_filter]
    
    if country_filter != "All":
        filtered = [opp for opp in filtered if opp.get('country') == country_filter]
    
    st.markdown(f"### Found {len(filtered)} opportunities")
    st.markdown("---")
    
    # Pagination
    page_size = 10
    total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
    
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("Previous") and st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()
        with col2:
            st.write(f"Page {st.session_state.current_page} of {total_pages}")
        with col3:
            if st.button("Next") and st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                st.rerun()
    
    start_idx = (st.session_state.current_page - 1) * page_size
    end_idx = min(start_idx + page_size, len(filtered))
    
    for opp in filtered[start_idx:end_idx]:
        display_opportunity_card(opp)

def render_dashboard():
    st.markdown('<p class="main-header">Analytics Dashboard</p>', unsafe_allow_html=True)
    
    stats = db_manager.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Opportunities", stats['total_opportunities'])
    with col2:
        st.metric("Verified", stats['verified'])
    with col3:
        st.metric("Active Sources", stats['active_sources'])
    with col4:
        st.metric("Categories", len(stats.get('categories', [])))
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if stats.get('categories'):
            st.subheader("By Category")
            df_cat = pd.DataFrame(stats['categories'])
            df_cat.columns = ['Category', 'Count']
            st.bar_chart(df_cat.set_index('Category'))
    
    with col2:
        if stats.get('top_countries'):
            st.subheader("Top Countries")
            df_country = pd.DataFrame(stats['top_countries'])
            df_country.columns = ['Country', 'Count']
            st.bar_chart(df_country.set_index('Country'))
    
    st.subheader("Source Performance")
    sources = db_manager.get_all_sources()
    if sources:
        df_sources = pd.DataFrame(sources)
        df_display = df_sources[['name', 'category', 'country', 'opportunities_count', 'error_count', 'is_active']]
        df_display.columns = ['Name', 'Category', 'Country', 'Opportunities', 'Errors', 'Active']
        df_display['Active'] = df_display['Active'].apply(lambda x: 'Yes' if x else 'No')
        st.dataframe(df_display, use_container_width=True, hide_index=True)

def render_sources():
    st.markdown('<p class="main-header">Source Management</p>', unsafe_allow_html=True)
    
    with st.expander("Add New Source", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            source_name = st.text_input("Source Name")
            source_url = st.text_input("Source URL")
        with col2:
            source_category = st.selectbox("Category", ["Government", "Employment", "Education", "Funding", "Internship", "Volunteer", "Youth"])
            source_country = st.selectbox("Country", ["Africa", "East Africa", "West Africa", "North Africa", "Southern Africa", "Global"])
        
        if st.button("Add Source", type="primary"):
            if source_name and source_url:
                if db_manager.add_source(source_name, source_url, source_category, source_country):
                    st.success(f"Source '{source_name}' added!")
                    st.rerun()
                else:
                    st.error("Failed to add source.")
            else:
                st.error("Please fill all fields.")
    
    st.subheader("All Sources")
    
    sources = db_manager.get_all_sources()
    if not sources:
        st.info("No sources found.")
        return
    
    search = st.text_input("Search Sources", placeholder="Search by name...")
    if search:
        sources = [s for s in sources if search.lower() in s['name'].lower()]
    
    df = pd.DataFrame(sources)
    df_display = df[['id', 'name', 'url', 'category', 'country', 'is_active', 'opportunities_count']]
    df_display.columns = ['ID', 'Name', 'URL', 'Category', 'Country', 'Active', 'Opps']
    df_display['Active'] = df_display['Active'].apply(lambda x: 'Yes' if x else 'No')
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Source management
    st.markdown("---")
    st.subheader("Manage Sources")
    
    source_options = [f"{s['id']} - {s['name']}" for s in sources]
    if source_options:
        selected = st.selectbox("Select Source", source_options)
        if selected:
            source_id = int(selected.split(' - ')[0])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Toggle Status"):
                    db_manager.toggle_source(source_id)
                    st.rerun()
            with col2:
                if st.button("Delete"):
                    db_manager.delete_source(source_id)
                    st.rerun()

def display_opportunity_card(opportunity: Dict):
    """Display a single opportunity card"""
    verified = opportunity.get('verified', False)
    
    st.markdown(f"""
        <div class="opportunity-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 5px 0;">{opportunity.get('title', 'Unknown Opportunity')}</h3>
                    <div style="margin-bottom: 8px;">
                        <span style="font-weight: 600;">{opportunity.get('organization', 'Unknown')}</span>
                        <span class="source-tag" style="margin-left: 8px;">{opportunity.get('source_name', 'Unknown')}</span>
                        <span class="source-tag" style="margin-left: 4px;">{opportunity.get('category', 'Other')}</span>
                        <span class="source-tag" style="margin-left: 4px;">{opportunity.get('country', 'Africa')}</span>
                    </div>
                    <div style="margin-bottom: 8px; font-size: 0.9rem;">
                        {opportunity.get('deadline', 'No deadline')}
                        {' '}<span class="verified-badge">{'Verified' if verified else 'Unverified'}</span>
                    </div>
                    <div style="font-size: 0.9rem; color: #666; margin-top: 8px;">
                        {opportunity.get('description', '')[:200]}{'...' if len(opportunity.get('description', '')) > 200 else ''}
                    </div>
                </div>
                <div style="text-align: right; min-width: 120px; margin-left: 20px;">
                    <div style="margin-top: 12px;">
                        <a href="{opportunity.get('official_url', '#')}" target="_blank">
                            <button style="background-color: #1a3c6e; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600;">
                                Apply Now
                            </button>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
