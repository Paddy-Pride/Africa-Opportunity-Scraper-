"""
Africa Opportunity Finder - Main Streamlit Application
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any
import logging

from scraper import ScraperController
from verifier import Verifier
from nlp_matcher import OpportunityMatcher
from utils.exporter import Exporter
from utils.helpers import (
    format_deadline, truncate_text, get_status_color,
    display_metric_cards, display_opportunity_card
)
from sources.source_manager import SourceManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
@st.cache_resource
def init_components():
    """Initialize and cache application components"""
    return {
        'scraper': ScraperController(),
        'verifier': Verifier(),
        'matcher': OpportunityMatcher(),
        'source_manager': SourceManager(),
        'exporter': Exporter()
    }

def main():
    """Main application entry point"""
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
            font-size: 3rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .opportunity-card {
            padding: 1.5rem;
            border-radius: 10px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .verified-badge {
            color: #28a745;
            font-weight: bold;
        }
        .unverified-badge {
            color: #dc3545;
        }
        .deadline-urgent {
            color: #dc3545;
            font-weight: bold;
        }
        .sidebar .sidebar-content {
            background: #f8f9fa;
        }
        .stButton button {
            width: 100%;
            margin-top: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    components = init_components()
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/africa.png", width=80)
        st.title("🌍 Africa Opportunity Finder")
        
        menu = ["Home", "All Opportunities", "Source Management", "Import Sources", "Recommendations"]
        choice = st.selectbox("Navigation", menu)
        
        st.divider()
        
        # Stats in sidebar
        db_stats = components['source_manager'].get_stats()
        st.metric("Total Sources", db_stats.get('total_sources', 0))
        st.metric("Total Opportunities", db_stats.get('total_opportunities', 0))
        st.metric("Verified Opportunities", db_stats.get('verified_count', 0))
        
        st.divider()
        
        # User profile for recommendations
        with st.expander("👤 Your Profile", expanded=False):
            user_skills = st.text_area("Enter your skills", placeholder="e.g., Python, Data Science, Leadership")
            user_interests = st.text_area("Enter your interests", placeholder="e.g., Technology, Education, Entrepreneurship")
            user_course = st.text_input("Your course/field", placeholder="e.g., Computer Science")
            user_career = st.text_input("Career goals", placeholder="e.g., Software Engineer")
            
            if st.button("Update Profile"):
                st.session_state.user_profile = {
                    'skills': user_skills,
                    'interests': user_interests,
                    'course': user_course,
                    'career_goals': user_career
                }
                st.success("Profile updated!")
        
        # Filters
        with st.expander("🔍 Filters", expanded=False):
            country_filter = st.text_input("Country")
            org_filter = st.text_input("Organization")
            category_filter = st.text_input("Category")
            keyword_filter = st.text_input("Keyword")
            days_until = st.slider("Days until deadline", 0, 30, 7)
    
    # Main content
    if choice == "Home":
        home_page(components)
    elif choice == "All Opportunities":
        all_opportunities_page(components)
    elif choice == "Source Management":
        source_management_page(components)
    elif choice == "Import Sources":
        import_sources_page(components)
    elif choice == "Recommendations":
        recommendations_page(components)

def home_page(components):
    """Display the home page with latest opportunities"""
    st.markdown('<h1 class="main-header">🌍 Africa Opportunity Finder</h1>', unsafe_allow_html=True)
    
    # Auto-scrape on load
    if 'last_scrape' not in st.session_state or \
       datetime.now() - st.session_state.last_scrape > timedelta(hours=1):
        with st.spinner("🔍 Discovering latest opportunities..."):
            try:
                scrape_results = components['scraper'].scrape_all()
                components['source_manager'].save_scrape_results(scrape_results)
                st.session_state.last_scrape = datetime.now()
                st.success(f"✅ Scraped {len(scrape_results)} new opportunities!")
                time.sleep(0.5)
            except Exception as e:
                st.error(f"❌ Scrape failed: {str(e)}")
    
    # Get opportunities
    opportunities = components['source_manager'].get_verified_opportunities(limit=20)
    
    if not opportunities:
        st.info("📭 No opportunities found. Try scraping now!")
        if st.button("Scrape Now"):
            st.rerun()
        return
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Latest Opportunities", len(opportunities))
    with col2:
        verified = sum(1 for opp in opportunities if opp.get('verified', False))
        st.metric("Verified", verified)
    with col3:
        categories = len(set(opp.get('category', '') for opp in opportunities))
        st.metric("Categories", categories)
    with col4:
        countries = len(set(opp.get('country', '') for opp in opportunities if opp.get('country')))
        st.metric("Countries", countries)
    
    st.divider()
    
    # Display opportunities
    for opp in opportunities:
        display_opportunity_card(opp)

def all_opportunities_page(components):
    """Display all opportunities with search and filters"""
    st.title("📋 All Opportunities")
    
    # Get all opportunities
    opportunities = components['source_manager'].get_all_opportunities()
    
    if not opportunities:
        st.info("No opportunities found.")
        return
    
    # Create search interface
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_term = st.text_input("Search opportunities", placeholder="Search by title, organization, or category...")
    with search_col2:
        sort_by = st.selectbox("Sort by", ["date_added", "deadline", "title"])
    
    # Filter opportunities
    filtered = components['source_manager'].filter_opportunities(
        opportunities, search_term
    )
    
    # Sort
    if sort_by == "date_added":
        filtered.sort(key=lambda x: x.get('date_added', ''), reverse=True)
    elif sort_by == "deadline":
        filtered.sort(key=lambda x: x.get('deadline', ''))
    elif sort_by == "title":
        filtered.sort(key=lambda x: x.get('title', ''))
    
    # Pagination
    items_per_page = 20
    total_items = len(filtered)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    if 'page' not in st.session_state:
        st.session_state.page = 0
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Previous", disabled=st.session_state.page == 0):
            st.session_state.page = max(0, st.session_state.page - 1)
            st.rerun()
    with col2:
        st.write(f"Page {st.session_state.page + 1} of {total_pages}")
    with col3:
        if st.button("Next", disabled=st.session_state.page >= total_pages - 1):
            st.session_state.page = min(total_pages - 1, st.session_state.page + 1)
            st.rerun()
    
    # Display current page
    start_idx = st.session_state.page * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    current_items = filtered[start_idx:end_idx]
    
    for opp in current_items:
        display_opportunity_card(opp)
    
    # Export options
    if st.button("📥 Export All to CSV"):
        df = pd.DataFrame(filtered)
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "opportunities.csv",
            "text/csv"
        )

def source_management_page(components):
    """Manage sources"""
    st.title("🔧 Source Management")
    
    # Add new source
    with st.expander("➕ Add New Source", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Source Name")
            new_url = st.text_input("Source URL")
        with col2:
            new_category = st.selectbox("Category", ["Education", "Jobs", "Grants", "Training", "Internships", "Scholarships"])
            new_country = st.text_input("Country (optional)")
        
        if st.button("Add Source"):
            if new_name and new_url:
                source_id = components['source_manager'].add_source({
                    'name': new_name,
                    'url': new_url,
                    'category': new_category,
                    'country': new_country,
                    'enabled': True
                })
                if source_id:
                    st.success(f"✅ Source '{new_name}' added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add source.")
            else:
                st.warning("Please fill in all required fields.")
    
    # Existing sources
    st.subheader("Existing Sources")
    sources = components['source_manager'].get_all_sources()
    
    if not sources:
        st.info("No sources added yet.")
        return
    
    # Search sources
    search = st.text_input("Search sources", placeholder="Search by name or URL...")
    if search:
        sources = [s for s in sources if search.lower() in s.get('name', '').lower() or 
                  search.lower() in s.get('url', '').lower()]
    
    # Display sources table
    for idx, source in enumerate(sources):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            with col1:
                st.write(f"**{source.get('name', 'Unnamed')}**")
                st.caption(source.get('url', ''))
            with col2:
                st.write(f"Category: {source.get('category', 'N/A')}")
                st.write(f"Country: {source.get('country', 'N/A')}")
            with col3:
                status = "✅ Active" if source.get('enabled', True) else "❌ Disabled"
                st.write(status)
                st.write(f"Scraped: {source.get('last_scraped', 'Never')[:10] if source.get('last_scraped') else 'Never'}")
            with col4:
                opportunities_count = components['source_manager'].count_opportunities_by_source(source.get('id', 0))
                st.metric("Opportunities", opportunities_count)
            with col5:
                if st.button(f"Edit", key=f"edit_{idx}"):
                    st.session_state.edit_source = source
                if st.button(f"Delete", key=f"del_{idx}"):
                    if components['source_manager'].delete_source(source.get('id', 0)):
                        st.success("Source deleted!")
                        st.rerun()
    
    # Edit source dialog
    if 'edit_source' in st.session_state:
        source = st.session_state.edit_source
        with st.expander("✏️ Edit Source", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                edit_name = st.text_input("Name", source.get('name', ''))
                edit_url = st.text_input("URL", source.get('url', ''))
            with col2:
                edit_category = st.selectbox("Category", ["Education", "Jobs", "Grants", "Training", "Internships", "Scholarships"], 
                                            index=["Education", "Jobs", "Grants", "Training", "Internships", "Scholarships"].index(source.get('category', 'Education')))
                edit_country = st.text_input("Country", source.get('country', ''))
            edit_enabled = st.checkbox("Enabled", source.get('enabled', True))
            
            if st.button("Update Source"):
                updated = {
                    'name': edit_name,
                    'url': edit_url,
                    'category': edit_category,
                    'country': edit_country,
                    'enabled': edit_enabled
                }
                if components['source_manager'].update_source(source.get('id', 0), updated):
                    st.success("Source updated!")
                    del st.session_state.edit_source
                    st.rerun()
                else:
                    st.error("Failed to update source.")
            
            if st.button("Cancel"):
                del st.session_state.edit_source
                st.rerun()

def import_sources_page(components):
    """Import sources from CSV or Excel"""
    st.title("📥 Import Sources")
    
    st.markdown("""
    ### Instructions
    Upload a CSV or Excel file with the following columns:
    - **name** (required): Source name
    - **url** (required): Source URL
    - **category** (optional): Category (Education, Jobs, Grants, Training, Internships, Scholarships)
    - **country** (optional): Country
    - **enabled** (optional): True/False
    
    The system will automatically detect and avoid duplicates.
    """)
    
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Found {len(df)} rows in file")
            st.dataframe(df.head())
            
            if st.button("Import Sources"):
                imported = 0
                skipped = 0
                errors = 0
                
                for _, row in df.iterrows():
                    try:
                        source_data = {
                            'name': str(row.get('name', '')),
                            'url': str(row.get('url', '')),
                            'category': str(row.get('category', 'Education')),
                            'country': str(row.get('country', '')),
                            'enabled': bool(row.get('enabled', True))
                        }
                        
                        if source_data['name'] and source_data['url']:
                            # Check for duplicates
                            if not components['source_manager'].source_exists(source_data['url']):
                                if components['source_manager'].add_source(source_data):
                                    imported += 1
                            else:
                                skipped += 1
                        else:
                            errors += 1
                    except Exception as e:
                        errors += 1
                        logger.error(f"Error importing row: {e}")
                
                st.success(f"""
                ✅ Import Complete!
                - Imported: {imported} sources
                - Skipped (duplicates): {skipped}
                - Errors: {errors}
                """)
                st.rerun()
                
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

def recommendations_page(components):
    """Get personalized recommendations"""
    st.title("🎯 Personalized Recommendations")
    
    if 'user_profile' not in st.session_state or not st.session_state.user_profile:
        st.warning("Please set up your profile in the sidebar first!")
        return
    
    profile = st.session_state.user_profile
    profile_text = " ".join([profile.get('skills', ''), profile.get('interests', ''), 
                            profile.get('course', ''), profile.get('career_goals', '')])
    
    if not profile_text.strip():
        st.warning("Please enter information in your profile fields.")
        return
    
    opportunities = components['source_manager'].get_all_opportunities()
    if not opportunities:
        st.info("No opportunities found. Please scrape some opportunities first.")
        return
    
    with st.spinner("Finding best matches for you..."):
        matched = components['matcher'].rank_opportunities(profile_text, opportunities)
    
    if not matched:
        st.info("No matching opportunities found. Try adjusting your profile or scraping more opportunities.")
        return
    
    st.subheader(f"Found {len(matched)} opportunities matching your profile")
    
    # Display top matches
    for opp in matched[:20]:
        display_opportunity_card(opp, show_score=True)

if __name__ == "__main__":
    main()
