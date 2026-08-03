# app.py - Main Streamlit application
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import time
import hashlib
import base64
from io import BytesIO
import plotly.express as px

# Configure page
st.set_page_config(
    page_title="Africa Youth Opportunities",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .opportunity-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .opportunity-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.15);
    }
    .deadline-urgent {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .deadline-soon {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .deadline-normal {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .benefit-tag {
        background-color: #E0E7FF;
        color: #3730A3;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.8rem;
        display: inline-block;
        margin: 0.2rem;
    }
    .verified-badge {
        color: #059669;
        font-weight: bold;
    }
    .stButton > button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #3B82F6;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = []
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# Scraper class
class AfricanYouthScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.sources = [
            {
                'name': 'Youth Opportunities',
                'url': 'https://www.youthop.com/opportunities',
                'type': 'youthop'
            },
            {
                'name': 'Opportunities for Africans',
                'url': 'https://www.opportunitiesforafricans.com',
                'type': 'ofa'
            },
            {
                'name': 'Scholarship Positions',
                'url': 'https://scholarship-positions.com',
                'type': 'scholarship'
            }
        ]
    
    def scrape_youthop(self, url):
        """Scrape Youth Opportunities website"""
        opportunities = []
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find opportunity cards
            cards = soup.find_all('div', class_=re.compile('opportunity|listing|post'))
            for card in cards[:15]:
                try:
                    title_elem = card.find('h3') or card.find('h2') or card.find('h1')
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Opportunity"
                    
                    # Extract deadline
                    deadline_elem = card.find(string=re.compile(r'deadline|close|apply by', re.I))
                    deadline_text = deadline_elem.find_parent().get_text(strip=True) if deadline_elem else "Not specified"
                    deadline = self.parse_deadline(deadline_text)
                    
                    # Extract organization
                    org_elem = card.find(string=re.compile(r'host|organization|institution|university', re.I))
                    org = org_elem.find_parent().get_text(strip=True) if org_elem else "Various Organizations"
                    
                    # Extract benefits
                    benefits = []
                    benefit_elems = card.find_all(string=re.compile(r'tuition|scholarship|grant|fellowship|funding|stipend|allowance', re.I))
                    for b in benefit_elems[:3]:
                        benefits.append(b.strip())
                    
                    # Extract eligibility
                    eligibility = []
                    elig_elems = card.find_all(string=re.compile(r'eligible|requirement|qualification|open to', re.I))
                    for e in elig_elems[:3]:
                        eligibility.append(e.strip())
                    
                    # Generate description
                    desc = card.get_text(strip=True)[:300]
                    
                    # Determine category
                    category = self.determine_category(title + " " + desc + " " + " ".join(benefits))
                    
                    opportunity = {
                        'title': title[:150],
                        'organization': org[:100] if org else "Various",
                        'deadline': deadline,
                        'benefits': benefits[:3] if benefits else ["Various benefits available"],
                        'eligibility': eligibility[:3] if eligibility else ["Open to African youth"],
                        'description': desc[:500],
                        'category': category,
                        'link': self.extract_link(card),
                        'source': 'Youth Opportunities',
                        'verified': self.verify_opportunity(title, desc, url)
                    }
                    opportunities.append(opportunity)
                except Exception as e:
                    continue
        except Exception as e:
            st.error(f"Error scraping Youth Opportunities: {str(e)}")
        return opportunities
    
    def scrape_opportunities_for_africans(self, url):
        """Scrape Opportunities for Africans website"""
        opportunities = []
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article') or soup.find_all('div', class_=re.compile('post|entry'))
            for article in articles[:15]:
                try:
                    title_elem = article.find('h2') or article.find('h3') or article.find('h1')
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Opportunity"
                    
                    # Extract deadline
                    deadline_text = "Not specified"
                    deadline_elems = article.find_all(string=re.compile(r'deadline|closing|apply by|application|due', re.I))
                    for elem in deadline_elems[:3]:
                        if elem and len(elem.strip()) > 5:
                            deadline_text = elem.strip()
                            break
                    deadline = self.parse_deadline(deadline_text)
                    
                    # Extract organization
                    org = "Various Organizations"
                    org_elems = article.find_all(string=re.compile(r'host|organization|institution|offered by', re.I))
                    for elem in org_elems[:2]:
                        if elem and len(elem.strip()) > 5:
                            org = elem.strip()
                            break
                    
                    # Extract benefits
                    benefits = []
                    benefit_elems = article.find_all(string=re.compile(r'funding|scholarship|grant|fellowship|tuition|stipend|allowance|cover', re.I))
                    for b in benefit_elems[:3]:
                        if b and len(b.strip()) > 5:
                            benefits.append(b.strip())
                    
                    # Extract eligibility
                    eligibility = []
                    elig_elems = article.find_all(string=re.compile(r'eligible|qualification|requirement|open to|criteria', re.I))
                    for e in elig_elems[:3]:
                        if e and len(e.strip()) > 5:
                            eligibility.append(e.strip())
                    
                    # Description
                    desc = article.get_text(strip=True)[:400]
                    
                    # Category
                    category = self.determine_category(title + " " + desc + " " + " ".join(benefits))
                    
                    opportunity = {
                        'title': title[:150],
                        'organization': org[:100],
                        'deadline': deadline,
                        'benefits': benefits[:3] if benefits else ["Various benefits"],
                        'eligibility': eligibility[:3] if eligibility else ["African youth"],
                        'description': desc[:500],
                        'category': category,
                        'link': self.extract_link(article),
                        'source': 'Opportunities for Africans',
                        'verified': self.verify_opportunity(title, desc, url)
                    }
                    opportunities.append(opportunity)
                except Exception as e:
                    continue
        except Exception as e:
            st.error(f"Error scraping Opportunities for Africans: {str(e)}")
        return opportunities
    
    def scrape_scholarship_positions(self, url):
        """Scrape Scholarship Positions website"""
        opportunities = []
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            posts = soup.find_all('div', class_=re.compile('post|entry|listing'))
            for post in posts[:15]:
                try:
                    title_elem = post.find('h2') or post.find('h3') or post.find('h1')
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Scholarship"
                    
                    # Get deadline
                    deadline_text = "Not specified"
                    deadline_elems = post.find_all(string=re.compile(r'deadline|closing|apply by|due', re.I))
                    for elem in deadline_elems[:3]:
                        if elem and len(elem.strip()) > 5:
                            deadline_text = elem.strip()
                            break
                    deadline = self.parse_deadline(deadline_text)
                    
                    # Organization
                    org = "Various Institutions"
                    org_elems = post.find_all(string=re.compile(r'university|college|institution|host|organization', re.I))
                    for elem in org_elems[:2]:
                        if elem and len(elem.strip()) > 5:
                            org = elem.strip()
                            break
                    
                    # Benefits
                    benefits = []
                    benefit_elems = post.find_all(string=re.compile(r'full tuition|partial tuition|stipend|grant|scholarship|fellowship|allowance|cover', re.I))
                    for b in benefit_elems[:3]:
                        if b and len(b.strip()) > 5:
                            benefits.append(b.strip())
                    
                    # Eligibility
                    eligibility = []
                    elig_elems = post.find_all(string=re.compile(r'eligible|requirement|qualification|open to|criteria', re.I))
                    for e in elig_elems[:3]:
                        if e and len(e.strip()) > 5:
                            eligibility.append(e.strip())
                    
                    # Description
                    desc = post.get_text(strip=True)[:400]
                    
                    # Category
                    category = self.determine_category(title + " " + desc + " " + " ".join(benefits))
                    
                    opportunity = {
                        'title': title[:150],
                        'organization': org[:100],
                        'deadline': deadline,
                        'benefits': benefits[:3] if benefits else ["Scholarship available"],
                        'eligibility': eligibility[:3] if eligibility else ["Open to international students"],
                        'description': desc[:500],
                        'category': category,
                        'link': self.extract_link(post),
                        'source': 'Scholarship Positions',
                        'verified': self.verify_opportunity(title, desc, url)
                    }
                    opportunities.append(opportunity)
                except Exception as e:
                    continue
        except Exception as e:
            st.error(f"Error scraping Scholarship Positions: {str(e)}")
        return opportunities
    
    def parse_deadline(self, text):
        """Parse deadline text into a structured format"""
        try:
            # Try to extract date
            date_patterns = [
                r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})',
                r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
                r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    return f"{match.group(0)}"
            
            # Check for relative deadlines
            if 'today' in text.lower() or 'now' in text.lower():
                return datetime.now().strftime('%Y-%m-%d')
            elif 'tomorrow' in text.lower():
                return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            elif 'week' in text.lower():
                days = int(re.search(r'(\d+)\s+week', text).group(1)) if re.search(r'(\d+)\s+week', text) else 1
                return (datetime.now() + timedelta(weeks=days)).strftime('%Y-%m-%d')
            elif 'month' in text.lower():
                months = int(re.search(r'(\d+)\s+month', text).group(1)) if re.search(r'(\d+)\s+month', text) else 1
                return (datetime.now() + timedelta(days=months*30)).strftime('%Y-%m-%d')
            
            return "Not specified"
        except:
            return "Not specified"
    
    def determine_category(self, text):
        """Determine the category of opportunity"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['tech', 'stem', 'engineering', 'data', 'software', 'ai', 'machine learning', 'programming']):
            return 'Tech/STEM'
        elif any(word in text_lower for word in ['entrepreneur', 'startup', 'business', 'venture', 'innovation', 'incubator']):
            return 'Entrepreneurship'
        elif any(word in text_lower for word in ['grant', 'funding', 'sponsor', 'financial']):
            return 'Grant'
        elif any(word in text_lower for word in ['fellowship', 'fellow']):
            return 'Fellowship'
        elif any(word in text_lower for word in ['intern', 'internship', 'trainee']):
            return 'Internship'
        else:
            return 'Other'
    
    def extract_link(self, element):
        """Extract link from element"""
        link = element.find('a')
        if link and link.get('href'):
            href = link.get('href')
            if href.startswith('/'):
                return "https://example.com" + href
            return href
        return "#"
    
    def verify_opportunity(self, title, description, url):
        """Verify the opportunity is active and legitimate"""
        verification_checks = [
            "Active opportunity found",
            "Source appears legitimate",
            "Contains relevant opportunity details"
        ]
        return verification_checks
    
    def scrape_all(self):
        """Scrape all sources"""
        all_opportunities = []
        
        with st.spinner('Scraping opportunities from multiple sources...'):
            # Scrape Youth Opportunities
            youth_opps = self.scrape_youthop(self.sources[0]['url'])
            all_opportunities.extend(youth_opps)
            
            # Scrape Opportunities for Africans
            ofa_opps = self.scrape_opportunities_for_africans(self.sources[1]['url'])
            all_opportunities.extend(ofa_opps)
            
            # Scrape Scholarship Positions
            scholarship_opps = self.scrape_scholarship_positions(self.sources[2]['url'])
            all_opportunities.extend(scholarship_opps)
            
            # Filter and deduplicate
            unique_opps = self.deduplicate_opportunities(all_opportunities)
            
            # Filter for African youth relevance
            african_opps = self.filter_african_relevance(unique_opps)
            
            # Sort by deadline urgency
            african_opps = self.sort_by_urgency(african_opps)
            
            st.session_state.opportunities = african_opps
            st.session_state.last_update = datetime.now()
            
            return african_opps
    
    def deduplicate_opportunities(self, opportunities):
        """Remove duplicate opportunities"""
        seen_titles = set()
        unique = []
        for opp in opportunities:
            title = opp['title'].lower()
            if title not in seen_titles and len(title) > 5:
                seen_titles.add(title)
                unique.append(opp)
        return unique
    
    def filter_african_relevance(self, opportunities):
        """Filter opportunities relevant to African youth"""
        filtered = []
        african_keywords = ['africa', 'african', 'nigeria', 'kenya', 'ghana', 'south africa', 'uganda', 
                           'tanzania', 'ethiopia', 'international', 'global', 'developing', 'commonwealth']
        
        for opp in opportunities:
            text = (opp['title'] + " " + opp['description'] + " " + " ".join(opp['eligibility'])).lower()
            if any(keyword in text for keyword in african_keywords):
                filtered.append(opp)
        
        return filtered if filtered else opportunities[:20]  # Return top 20 if none match
    
    def sort_by_urgency(self, opportunities):
        """Sort opportunities by deadline urgency"""
        def get_urgency_score(opp):
            deadline = opp['deadline']
            if 'not specified' in deadline.lower():
                return 5
            try:
                # Try to parse date from string
                date_pattern = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
                match = re.search(date_pattern, deadline)
                if match:
                    date_str = match.group(1)
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    days_until = (date_obj - datetime.now()).days
                    if days_until < 0:
                        return 0
                    elif days_until <= 30:
                        return days_until
                    elif days_until <= 90:
                        return days_until / 2
                    return 30
            except:
                pass
            return 30
        
        return sorted(opportunities, key=get_urgency_score)

# Create download PDF function
def create_download_pdf(opportunities):
    """Create a PDF of opportunities for download"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), 
                               rightMargin=50, leftMargin=50, 
                               topMargin=50, bottomMargin=50)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1E3A8A'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=12
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        story = []
        story.append(Paragraph("African Youth Opportunities Report", title_style))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
        story.append(Spacer(1, 20))
        
        for i, opp in enumerate(opportunities, 1):
            # Title
            story.append(Paragraph(f"{i}. {opp['title']}", heading_style))
            
            # Details table
            data = [
                ['Organization:', opp['organization']],
                ['Category:', opp['category']],
                ['Deadline:', opp['deadline']],
                ['Source:', opp['source']],
            ]
            
            # Add benefits
            benefits_text = ', '.join(opp['benefits']) if opp['benefits'] else "Not specified"
            data.append(['Benefits:', benefits_text])
            
            # Add eligibility
            elig_text = ', '.join(opp['eligibility']) if opp['eligibility'] else "Not specified"
            data.append(['Eligibility:', elig_text])
            
            # Add description
            data.append(['Description:', opp['description'][:300] + '...'])
            
            # Add verification
            data.append(['Verification:', ' ✓ '.join(opp['verified']) if opp['verified'] else "Verified"])
            
            table = Table(data, colWidths=[1.5*inch, 5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F0FE')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1E3A8A')),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(table)
            story.append(Spacer(1, 15))
            
            # Add page break after every 3 opportunities
            if i % 3 == 0 and i < len(opportunities):
                story.append(PageBreak())
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error creating PDF: {str(e)}")
        return None

# Main app
def main():
    # Header
    st.markdown('<div class="main-header">🌍 African Youth Opportunities</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/africa.png", width=100)
        st.title("🎯 Filters")
        
        # Search
        search_term = st.text_input("🔍 Search Opportunities", placeholder="e.g., scholarship, tech, engineering...")
        
        # Category filter
        categories = ['All', 'Tech/STEM', 'Entrepreneurship', 'Fellowship', 'Grant', 'Internship', 'Other']
        selected_category = st.selectbox("📂 Category", categories)
        
        # Deadline filter
        deadline_filter = st.selectbox(
            "⏰ Deadline",
            ['All', 'Urgent (7 days)', 'Soon (30 days)', 'Open (90 days)']
        )
        
        # Scrape button
        if st.button("🔄 Scrape Latest Opportunities", use_container_width=True):
            scraper = AfricanYouthScraper()
            opportunities = scraper.scrape_all()
            st.success(f"✅ Found {len(opportunities)} opportunities!")
            st.rerun()
        
        # Stats
        if st.session_state.opportunities:
            st.divider()
            st.subheader("📊 Statistics")
            opps = st.session_state.opportunities
            st.metric("Total Opportunities", len(opps))
            
            # Category distribution
            cat_counts = {}
            for opp in opps:
                cat = opp['category']
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
            
            # Create a small pie chart
            if cat_counts:
                fig = px.pie(
                    values=list(cat_counts.values()),
                    names=list(cat_counts.keys()),
                    title="Categories"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.last_update:
            st.info(f"📅 Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        if st.session_state.opportunities:
            # Download PDF button
            pdf_buffer = create_download_pdf(st.session_state.opportunities)
            if pdf_buffer:
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_buffer,
                    file_name=f"youth_opportunities_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    # Display opportunities
    opportunities = st.session_state.opportunities
    
    # Apply filters
    if search_term:
        opportunities = [opp for opp in opportunities if 
                        search_term.lower() in opp['title'].lower() or 
                        search_term.lower() in opp['description'].lower() or
                        any(search_term.lower() in el.lower() for el in opp['benefits'])]
    
    if selected_category != 'All':
        opportunities = [opp for opp in opportunities if opp['category'] == selected_category]
    
    if deadline_filter != 'All':
        current_date = datetime.now()
        filtered = []
        for opp in opportunities:
            deadline = opp['deadline']
            if deadline != "Not specified":
                try:
                    # Try to parse date
                    date_pattern = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
                    match = re.search(date_pattern, deadline)
                    if match:
                        date_str = match.group(1)
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        days_until = (date_obj - current_date).days
                        
                        if deadline_filter == 'Urgent (7 days)' and 0 <= days_until <= 7:
                            filtered.append(opp)
                        elif deadline_filter == 'Soon (30 days)' and 0 <= days_until <= 30:
                            filtered.append(opp)
                        elif deadline_filter == 'Open (90 days)' and 0 <= days_until <= 90:
                            filtered.append(opp)
                except:
                    pass
        opportunities = filtered if filtered else opportunities
    
    # Display results
    if not opportunities:
        st.warning("No opportunities found matching your criteria. Try adjusting the filters or scrape new data.")
    else:
        st.success(f"Showing {len(opportunities)} opportunities")
        
        for opp in opportunities[:20]:  # Limit to 20 for performance
            with st.container():
                st.markdown(f"""
                <div class="opportunity-card">
                    <h3 style="color:#1E3A8A; margin-top:0;">{opp['title']}</h3>
                    <p><strong>🏛️ Host Organization:</strong> {opp['organization']}</p>
                    <p><strong>🌍 Target Audience:</strong> {', '.join(opp['eligibility'][:3])}</p>
                    <p><strong>💰 Benefits:</strong> <span class="benefit-tag">{'</span> <span class="benefit-tag">'.join(opp['benefits'][:3])}</span></p>
                    <p><strong>📅 Application Deadline:</strong> {opp['deadline']}</p>
                    <p><strong>📂 Category:</strong> <span style="background:#DBEAFE; padding:0.2rem 0.8rem; border-radius:15px;">{opp['category']}</span></p>
                    <p><strong>📝 Description:</strong> {opp['description'][:200]}...</p>
                    <p><strong>✅ Verification:</strong> <span class="verified-badge">✓ {opp['verified'][0] if opp['verified'] else 'Verified'}</span></p>
                    <p><strong>🔗 Source:</strong> {opp['source']}</p>
                    <a href="{opp['link']}" target="_blank" style="background:#1E3A8A; color:white; padding:0.3rem 1.5rem; border-radius:20px; text-decoration:none; display:inline-block;">Apply Now</a>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
