"""
Africa Opportunity Finder - Production Streamlit Application
Enterprise-grade opportunity discovery platform for African youth
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Any
import json
import base64
from io import BytesIO
import plotly.graph_objects as go
import plotly.express as px

from scraper import DatabaseManager, OpportunityScraper
from scraper import logger

# Page configuration
st.set_page_config(
    page_title="Africa Opportunity Finder",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
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
        .opportunity-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transform: translateY(-2px);
            transition: all 0.3s ease;
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
        .stButton > button:hover {
            background-color: #2a5c8e;
            color: white;
        }
        .verified-badge {
            background-color: #28a745;
            color: white;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
        }
        .unverified-badge {
            background-color: #ffc107;
            color: #856404;
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
        .deadline-warning {
            color: #dc3545;
            font-weight: 600;
        }
        .deadline-normal {
            color: #28a745;
        }
        .match-score {
            font-size: 1.5rem;
            font-weight: 700;
        }
        .match-high {
            color: #28a745;
        }
        .match-medium {
            color: #ffc107;
        }
        .match-low {
            color: #dc3545;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize database and scraper
@st.cache_resource
def init_services():
    """Initialize services with caching"""
    db = DatabaseManager()
    scraper = OpportunityScraper(db)
    return db, scraper

db_manager, scraper = init_services()

# Session state initialization
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = []
if 'selected_opportunities' not in st.session_state:
    st.session_state.selected_opportunities = []
if 'last_scrape' not in st.session_state:
    st.session_state.last_scrape = None
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'filtered_count' not in st.session_state:
    st.session_state.filtered_count = 0
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
if 'sources' not in st.session_state:
    st.session_state.sources = db_manager.get_all_sources()
if 'page' not in st.session_state:
    st.session_state.page = "home"

def main():
    """Main application entry point"""
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/africa.png", width=80)
        st.markdown("### Africa Opportunity Finder")
        st.markdown("---")
        
        # Scrape controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Scrape All", use_container_width=True):
                st.session_state.scraping_in_progress = True
                with st.spinner("Scraping all sources..."):
                    try:
                        result = scraper.scrape_all_sources()
                        st.session_state.last_scrape = datetime.now()
                        st.session_state.opportunities = db_manager.get_opportunities(limit=500)
                        st.success(f"Found {result['total_opportunities']} opportunities")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                st.session_state.scraping_in_progress = False
                st.rerun()
        
        with col2:
            if st.button("View Stats", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
        
        st.markdown("---")
        
        # Navigation
        pages = {
            "Home": "home",
            "Browse": "browse",
            "Recommendations": "recommendations",
            "Dashboard": "dashboard",
            "Sources": "sources"
        }
        
        selection = st.radio("Navigation", list(pages.keys()), index=0)
        current_page = pages[selection]
        st.session_state.page = current_page
        
        st.markdown("---")
        
        # User Profile for recommendations
        st.markdown("### Your Profile")
        user_profile = st.text_area(
            "Skills, interests, and career goals",
            value=st.session_state.user_profile,
            placeholder="Example: Computer Science student interested in AI and machine learning internships in East Africa",
            height=80
        )
        if st.button("Update Profile", use_container_width=True):
            st.session_state.user_profile = user_profile
            st.success("Profile updated!")
            st.rerun()
        
        st.markdown("---")
        st.caption(f"Last updated: {st.session_state.last_scrape.strftime('%Y-%m-%d %H:%M') if st.session_state.last_scrape else 'Never'}")
        st.caption(f"Total opportunities: {len(st.session_state.opportunities)}")
    
    # Page routing
    if current_page == "home":
        render_home()
    elif current_page == "browse":
        render_browse()
    elif current_page == "recommendations":
        render_recommendations()
    elif current_page == "dashboard":
        render_dashboard()
    elif current_page == "sources":
        render_sources()

def render_home():
    """Render home page"""
    st.markdown('<p class="main-header">Latest African Opportunities</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Discover verified opportunities for African youth across the continent</p>', unsafe_allow_html=True)
    
    # Load opportunities if empty
    if not st.session_state.opportunities:
        with st.spinner("Loading opportunities..."):
            st.session_state.opportunities = db_manager.get_opportunities(limit=500)
            if not st.session_state.opportunities:
                st.info("No opportunities found. Click 'Scrape All' to fetch opportunities from all sources.")
                return
    
    # Statistics row
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
            time_diff = datetime.now() - st.session_state.last_scrape
            hours = time_diff.total_seconds() / 3600
            st.markdown(f"""
                <div class="metric-card">
                    <h3>{int(hours)}h</h3>
                    <p>Since Last Update</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display opportunities
    display_count = min(10, len(st.session_state.opportunities))
    st.subheader(f"Recent Opportunities ({display_count} of {len(st.session_state.opportunities)})")
    
    for opp in st.session_state.opportunities[:display_count]:
        display_opportunity_card(opp)
    
    # View all button
    if len(st.session_state.opportunities) > 10:
        if st.button("View All Opportunities", use_container_width=True):
            st.session_state.page = "browse"
            st.rerun()

def render_browse():
    """Render browse page with filters"""
    st.markdown('<p class="main-header">Browse Opportunities</p>', unsafe_allow_html=True)
    
    if not st.session_state.opportunities:
        st.info("No opportunities available. Please scrape sources first.")
        return
    
    # Filters
    st.markdown("### Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_query = st.text_input("Search", placeholder="Search by title, organization...")
    
    with col2:
        # Get categories from opportunities
        categories = list(set(opp.get('category', 'Other') for opp in st.session_state.opportunities))
        categories.sort()
        category_filter = st.selectbox("Category", ["All"] + categories)
    
    with col3:
        countries = list(set(opp.get('country', 'Global') for opp in st.session_state.opportunities))
        countries = [c for c in countries if c and c != 'Global']
        countries.sort()
        country_filter = st.selectbox("Country", ["All"] + countries)
    
    with col4:
        sort_options = ["Date Added (Newest)", "Date Added (Oldest)", "Title", "Organization", "Deadline"]
        sort_by = st.selectbox("Sort By", sort_options)
    
    # Apply filters
    filtered = st.session_state.opportunities.copy()
    
    if search_query:
        search_lower = search_query.lower()
        filtered = [opp for opp in filtered if 
                   search_lower in opp.get('title', '').lower() or 
                   search_lower in opp.get('organization', '').lower() or
                   search_lower in opp.get('description', '').lower() or
                   search_lower in opp.get('source_name', '').lower()]
    
    if category_filter != "All":
        filtered = [opp for opp in filtered if opp.get('category') == category_filter]
    
    if country_filter != "All":
        filtered = [opp for opp in filtered if opp.get('country') == country_filter]
    
    # Sort
    if sort_by == "Date Added (Newest)":
        filtered.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    elif sort_by == "Date Added (Oldest)":
        filtered.sort(key=lambda x: x.get('created_at', ''))
    elif sort_by == "Title":
        filtered.sort(key=lambda x: x.get('title', ''))
    elif sort_by == "Organization":
        filtered.sort(key=lambda x: x.get('organization', ''))
    elif sort_by == "Deadline":
        filtered.sort(key=lambda x: x.get('deadline', '9999-12-31'))
    
    st.session_state.filtered_count = len(filtered)
    
    # Results count
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
    
    # Display opportunities
    start_idx = (st.session_state.current_page - 1) * page_size
    end_idx = min(start_idx + page_size, len(filtered))
    
    for opp in filtered[start_idx:end_idx]:
        display_opportunity_card(opp)

def render_recommendations():
    """Render AI recommendations page"""
    st.markdown('<p class="main-header">AI-Powered Recommendations</p>', unsafe_allow_html=True)
    
    if not st.session_state.opportunities:
        st.info("No opportunities available. Please scrape sources first.")
        return
    
    if not st.session_state.user_profile:
        st.warning("Please set up your profile in the sidebar to get personalized recommendations.")
        
        # Show recent opportunities
        st.subheader("Recent Opportunities")
        for opp in st.session_state.opportunities[:5]:
            display_opportunity_card(opp)
        return
    
    # Simple TF-IDF based matching
    with st.spinner("Generating personalized recommendations..."):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Prepare texts
            opportunities_text = []
            for opp in st.session_state.opportunities:
                text = f"{opp.get('title', '')} {opp.get('description', '')} {opp.get('category', '')} {opp.get('organization', '')}"
                opportunities_text.append(text)
            
            # Add user profile
            all_texts = opportunities_text + [st.session_state.user_profile]
            
            # Vectorize
            vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Calculate similarities
            user_vector = tfidf_matrix[-1]
            opp_vectors = tfidf_matrix[:-1]
            similarities = cosine_similarity(user_vector, opp_vectors).flatten()
            
            # Add scores to opportunities
            for i, opp in enumerate(st.session_state.opportunities):
                opp['match_score'] = float(similarities[i] if i < len(similarities) else 0)
            
            # Sort by match score
            scored_opps = sorted(st.session_state.opportunities, 
                                key=lambda x: x.get('match_score', 0), 
                                reverse=True)
            
            # Display top recommendations
            st.subheader(f"Top Recommendations for You")
            st.caption(f"Based on: {st.session_state.user_profile[:100]}...")
            st.markdown("---")
            
            for opp in scored_opps[:10]:
                display_opportunity_card(opp)
                
        except Exception as e:
            st.error(f"Error generating recommendations: {str(e)}")
            st.info("Showing all opportunities instead")
            
            for opp in st.session_state.opportunities[:10]:
                display_opportunity_card(opp)

def render_dashboard():
    """Render analytics dashboard"""
    st.markdown('<p class="main-header">Analytics Dashboard</p>', unsafe_allow_html=True)
    
    stats = db_manager.get_statistics()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Opportunities", stats['total_opportunities'])
    with col2:
        st.metric("Verified", stats['verified'], delta=f"{stats['verified']/max(stats['total_opportunities'],1)*100:.1f}%")
    with col3:
        st.metric("Active Sources", stats['active_sources'])
    with col4:
        st.metric("Categories", len(stats.get('categories', [])))
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if stats.get('categories'):
            st.subheader("Opportunities by Category")
            df_cat = pd.DataFrame(stats['categories'])
            fig = px.pie(df_cat, values='COUNT(*)', names='category', title='Category Distribution')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if stats.get('top_countries'):
            st.subheader("Top 10 Countries")
            df_country = pd.DataFrame(stats['top_countries'])
            fig = px.bar(df_country, x='country', y='COUNT(*)', title='Opportunities by Country')
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    # Sources table
    st.subheader("Source Performance")
    sources = db_manager.get_all_sources()
    if sources:
        df_sources = pd.DataFrame(sources)
        df_sources_display = df_sources[['name', 'category', 'country', 'opportunities_count', 'error_count', 'is_active']]
        df_sources_display.columns = ['Name', 'Category', 'Country', 'Opportunities', 'Errors', 'Active']
        df_sources_display['Active'] = df_sources_display['Active'].apply(lambda x: 'Yes' if x else 'No')
        st.dataframe(df_sources_display, use_container_width=True, hide_index=True)

def render_sources():
    """Render source management page"""
    st.markdown('<p class="main-header">Source Management</p>', unsafe_allow_html=True)
    
    # Add new source
    with st.expander("Add New Source", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            source_name = st.text_input("Source Name", placeholder="Example: African Union")
            source_url = st.text_input("Source URL", placeholder="https://example.com/opportunities")
        with col2:
            source_category = st.selectbox("Category", ["Government", "Employment", "Education", "Funding", "Internship", "Volunteer", "Youth", "Other"])
            source_country = st.selectbox("Primary Country", ["Africa"] + ["East Africa", "West Africa", "North Africa", "Southern Africa", "Central Africa"] + [
                'Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi',
                'Cameroon', 'Cabo Verde', 'Central African Republic', 'Chad',
                'Comoros', 'Congo', 'Djibouti', 'Egypt', 'Equatorial Guinea',
                'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana',
                'Guinea', 'Guinea-Bissau', 'Ivory Coast', 'Kenya', 'Lesotho',
                'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania',
                'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria',
                'Rwanda', 'Sao Tome and Principe', 'Senegal', 'Seychelles',
                'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan', 'Sudan',
                'Tanzania', 'Togo', 'Tunisia', 'Uganda', 'Zambia', 'Zimbabwe'
            ])
        
        if st.button("Add Source", type="primary"):
            if source_name and source_url:
                if db_manager.add_source(source_name, source_url, source_category, source_country):
                    st.success(f"Source '{source_name}' added successfully!")
                    st.session_state.sources = db_manager.get_all_sources()
                    st.rerun()
                else:
                    st.error("Failed to add source. It may already exist.")
            else:
                st.error("Please fill in all required fields.")
    
    # Display sources
    st.subheader("All Sources")
    
    sources = db_manager.get_all_sources()
    if not sources:
        st.info("No sources found. Add a source to get started!")
        return
    
    # Search
    search_source = st.text_input("Search Sources", placeholder="Search by name or URL...")
    
    if search_source:
        sources = [s for s in sources if search_source.lower() in s['name'].lower() or search_source.lower() in s['url'].lower()]
    
    # Create display dataframe
    df = pd.DataFrame(sources)
    df_display = df[['id', 'name', 'url', 'category', 'country', 'is_active', 'opportunities_count', 'last_scrape']]
    df_display.columns = ['ID', 'Name', 'URL', 'Category', 'Country', 'Active', 'Opps', 'Last Scrape']
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
            source = db_manager.get_all_sources()
            source = next((s for s in source if s['id'] == source_id), None)
            
            if source:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Toggle Status"):
                        db_manager.toggle_source(source_id)
                        st.success("Status updated!")
                        st.session_state.sources = db_manager.get_all_sources()
                        st.rerun()
                
                with col2:
                    if st.button("Scrape Now"):
                        with st.spinner(f"Scraping {source['name']}..."):
                            result = scraper.scrape_single_source(source_id)
                            if 'error' not in result:
                                st.success(f"Found {result['found']} opportunities, saved {result['saved']}")
                            else:
                                st.error(result['error'])
                            st.rerun()
                
                with col3:
                    if st.button("Delete"):
                        if st.warning("Are you sure you want to delete this source?"):
                            db_manager.delete_source(source_id)
                            st.success("Source deleted!")
                            st.session_state.sources = db_manager.get_all_sources()
                            st.rerun()

def display_opportunity_card(opportunity: Dict):
    """Display a single opportunity card"""
    verified = opportunity.get('verified', False)
    match_score = opportunity.get('match_score', 0)
    
    # Determine match score class
    if match_score >= 0.7:
        score_class = "match-high"
        score_text = f"{int(match_score * 100)}%"
    elif match_score >= 0.4:
        score_class = "match-medium"
        score_text = f"{int(match_score * 100)}%"
    else:
        score_class = "match-low"
        score_text = f"{int(match_score * 100)}%" if match_score > 0 else "N/A"
    
    # Deadline status
    deadline = opportunity.get('deadline', '')
    deadline_html = ''
    if deadline:
        try:
            # Try to parse date
            if '/' in deadline or '-' in deadline:
                from dateutil import parser
                deadline_date = parser.parse(deadline, fuzzy=True)
                days_until = (deadline_date - datetime.now()).days
                if days_until < 0:
                    deadline_html = f'<span class="deadline-warning">Passed</span>'
                elif days_until < 7:
                    deadline_html = f'<span class="deadline-warning">{days_until} days left</span>'
                elif days_until < 30:
                    deadline_html = f'<span class="deadline-normal">{days_until} days left</span>'
                else:
                    deadline_html = f'<span>{deadline}</span>'
            else:
                deadline_html = f'<span>{deadline}</span>'
        except:
            deadline_html = f'<span>{deadline}</span>'
    
    # Build card
    st.markdown(f"""
        <div class="opportunity-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 5px 0;">{opportunity.get('title', 'Unknown Opportunity')}</h3>
                    <div style="margin-bottom: 8px;">
                        <span style="font-weight: 600;">{opportunity.get('organization', 'Unknown Organization')}</span>
                        <span class="source-tag" style="margin-left: 8px;">{opportunity.get('source_name', 'Unknown')}</span>
                        <span class="source-tag" style="margin-left: 4px;">{opportunity.get('category', 'Other')}</span>
                        <span class="source-tag" style="margin-left: 4px;">{opportunity.get('country', 'Global')}</span>
                    </div>
                    <div style="margin-bottom: 8px; font-size: 0.9rem;">
                        {deadline_html if deadline else 'No deadline specified'}
                        {' '}<span class="{'verified-badge' if verified else 'unverified-badge'}">{'Verified' if verified else 'Unverified'}</span>
                    </div>
                    <div style="font-size: 0.9rem; color: #666; margin-top: 8px;">
                        {opportunity.get('description', '')[:200]}{'...' if len(opportunity.get('description', '')) > 200 else ''}
                    </div>
                </div>
                <div style="text-align: right; min-width: 120px; margin-left: 20px;">
                    <div class="match-score {score_class}">{score_text}</div>
                    <div style="font-size: 0.8rem; color: #666;">Match Score</div>
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
