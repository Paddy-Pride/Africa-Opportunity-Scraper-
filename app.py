import streamlit as st
import pandas as pd
from scraper import run_scraper
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

st.set_page_config(page_title="FutureFinder Africa", layout="wide")

st.title("🇺🇬 FutureFinder Africa")
st.subheader("Verified Opportunities for African Youth")
st.markdown("---")

# Sidebar
st.sidebar.markdown("### About")
st.sidebar.info("Automatically finds and verifies scholarships, jobs, grants, fellowships for African youth")

st.sidebar.markdown("### Sources")
st.sidebar.text("• One Young World")
st.sidebar.text("• DAAD")
st.sidebar.text("• Mastercard Foundation")
st.sidebar.text("• UNDP")
st.sidebar.text("• African Union")

# Refresh button
if st.button("🔄 Refresh Data Now"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)
def load_data():
    with st.spinner("Fetching latest opportunities..."):
        data = run_scraper()
        return data

# Load data
data = load_data()

if not data:
    st.warning("No opportunities found. Please try again later.")
else:
    # Metrics
    df = pd.DataFrame(data)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Opportunities", len(df))
    with col2:
        types = df['type'].value_counts()
        st.metric("Categories", len(types))
    with col3:
        sources = df['source'].nunique()
        st.metric("Sources", sources)
    with col4:
        st.metric("Last Updated", datetime.now().strftime("%H:%M"))

    # Category Breakdown
    st.markdown("### Category Breakdown")
    type_counts = df['type'].value_counts()
    st.bar_chart(type_counts)

    # Filter
    st.markdown("### Filter by Type")
    types_list = ['All'] + list(df['type'].unique())
    selected_type = st.selectbox("Select Category", types_list)
    
    if selected_type != 'All':
        df = df[df['type'] == selected_type]

    # Search
    st.markdown("### Search Opportunities")
    search_term = st.text_input("Search by title, organization, or description")
    if search_term:
        df = df[df['title'].str.contains(search_term, case=False) | 
                df['organization'].str.contains(search_term, case=False) |
                df['description'].str.contains(search_term, case=False)]

    # Display
    st.markdown(f"### Found {len(df)} Opportunities")
    
    for idx, row in df.iterrows():
        with st.container():
            link = row.get('link', '#')
            
            st.markdown(f"**{row['title']}**")
            st.caption(f"🏷️ Type: {row['type']} | Source: {row['source']}")
            
            if 'organization' in row and row['organization'] != 'N/A':
                st.caption(f"🏢 Organization: {row['organization']}")
            
            description = row.get('description', 'N/A')
            if description != 'N/A' and len(description) > 300:
                description = description[:300] + "..."
            st.caption(f"📝 {description}")
            
            st.caption(f"📅 {row.get('deadline', 'N/A')}")
            
            # Show key fields
            if row.get('eligibility') and row['eligibility'] != 'N/A':
                st.caption(f"✅ Eligibility: {row['eligibility'][:150]}...")
            
            if row.get('benefits') and row['benefits'] != 'N/A':
                st.caption(f"💰 Benefits: {row['benefits'][:150]}...")
            
            st.caption(f"🔗 [Apply Here]({link})")
            st.divider()

    # Download buttons
    st.markdown("---")
    st.markdown("### Download Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Download CSV",
            data=csv,
            file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        def create_pdf(df):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                   rightMargin=40, leftMargin=40,
                                   topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            elements = []
            
            # ====== TITLE SECTION ======
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a5276'),
                alignment=TA_CENTER,
                spaceAfter=20
            )
            elements.append(Paragraph("FutureFinder Africa", title_style))
            elements.append(Paragraph("Verified Opportunities Report", title_style))
            
            date_style = ParagraphStyle(
                'CustomDate',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", date_style))
            
            elements.append(Spacer(1, 20))
            
            # ====== SUMMARY TABLE ======
            summary_style = ParagraphStyle(
                'CustomSummary',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=6
            )
            elements.append(Paragraph(f"<b>Total Opportunities:</b> {len(df)}", summary_style))
            
            type_counts = df['type'].value_counts()
            type_text = " | ".join([f"{k}: {v}" for k, v in type_counts.items()])
            elements.append(Paragraph(f"<b>Categories:</b> {type_text}", summary_style))
            
            source_counts = df['source'].value_counts()
            source_text = " | ".join([f"{k}: {v}" for k, v in source_counts.items()])
            elements.append(Paragraph(f"<b>Sources:</b> {source_text}", summary_style))
            
            elements.append(Spacer(1, 30))
            
            # ====== HEADER STYLES ======
            header_style = ParagraphStyle(
                'HeaderStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.whitesmoke,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            cell_style = ParagraphStyle(
                'CellStyle',
                parent=styles['Normal'],
                fontSize=7,
                alignment=TA_LEFT,
                leading=10
            )
            
            link_style = ParagraphStyle(
                'LinkStyle',
                parent=styles['Normal'],
                fontSize=7,
                textColor=colors.HexColor('#1a5276'),
                alignment=TA_LEFT,
                fontName='Helvetica'
            )
            
            # ====== MAIN TABLE ======
            for idx, row in df.iterrows():
                # Opportunity title
                opp_title_style = ParagraphStyle(
                    'OppTitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.HexColor('#1a5276'),
                    spaceAfter=6
                )
                elements.append(Paragraph(f"{idx+1}. {row['title']}", opp_title_style))
                
                # Organization
                org = row.get('organization', 'N/A')
                elements.append(Paragraph(f"<b>Organization:</b> {org}", cell_style))
                
                # Type and Source
                opp_type = row.get('type', 'N/A')
                source = row.get('source', 'N/A')
                elements.append(Paragraph(f"<b>Type:</b> {opp_type} | <b>Source:</b> {source}", cell_style))
                
                # Deadline
                deadline = row.get('deadline', 'N/A')
                elements.append(Paragraph(f"<b>Deadline:</b> {deadline}", cell_style))
                
                # Description
                desc = row.get('description', 'N/A')
                if len(desc) > 500:
                    desc = desc[:500] + "..."
                elements.append(Paragraph(f"<b>Description:</b> {desc}", cell_style))
                
                # Eligibility
                eligibility = row.get('eligibility', 'N/A')
                if eligibility != 'N/A' and len(eligibility) > 300:
                    eligibility = eligibility[:300] + "..."
                elements.append(Paragraph(f"<b>Eligibility:</b> {eligibility}", cell_style))
                
                # Benefits
                benefits = row.get('benefits', 'N/A')
                if benefits != 'N/A' and len(benefits) > 300:
                    benefits = benefits[:300] + "..."
                elements.append(Paragraph(f"<b>Benefits:</b> {benefits}", cell_style))
                
                # Link
                link = row.get('link', '#')
                elements.append(Paragraph(f"<b>Apply Link:</b> <a href='{link}' color='blue'>{link}</a>", link_style))
                
                # Verification note
                elements.append(Paragraph(f"<i>Verified from official {source} website</i>", cell_style))
                
                elements.append(Spacer(1, 12))
                elements.append(Paragraph("-" * 80, cell_style))
                elements.append(Spacer(1, 12))
            
            # ====== FOOTER ======
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceBefore=20
            )
            elements.append(Paragraph("All opportunities verified from official sources. Links are clickable.", footer_style))
            elements.append(Paragraph(f"Generated by FutureFinder Africa", footer_style))
            
            doc.build(elements)
            buffer.seek(0)
            return buffer
        
        pdf_buffer = create_pdf(df)
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_buffer,
            file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )import streamlit as st
import pandas as pd
from scraper import run_scraper
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

st.set_page_config(page_title="FutureFinder Africa", layout="wide")

st.title("🇺🇬 FutureFinder Africa")
st.subheader("Verified Opportunities for African Youth")
st.markdown("---")

# Sidebar
st.sidebar.markdown("### About")
st.sidebar.info("Automatically finds and verifies scholarships, jobs, grants, fellowships for African youth")

st.sidebar.markdown("### Sources")
st.sidebar.text("• One Young World")
st.sidebar.text("• DAAD")
st.sidebar.text("• Mastercard Foundation")
st.sidebar.text("• UNDP")
st.sidebar.text("• African Union")

# Refresh button
if st.button("🔄 Refresh Data Now"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)
def load_data():
    with st.spinner("Fetching latest opportunities..."):
        data = run_scraper()
        return data

# Load data
data = load_data()

if not data:
    st.warning("No opportunities found. Please try again later.")
else:
    # Metrics
    df = pd.DataFrame(data)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Opportunities", len(df))
    with col2:
        types = df['type'].value_counts()
        st.metric("Categories", len(types))
    with col3:
        sources = df['source'].nunique()
        st.metric("Sources", sources)
    with col4:
        st.metric("Last Updated", datetime.now().strftime("%H:%M"))

    # Category Breakdown
    st.markdown("### Category Breakdown")
    type_counts = df['type'].value_counts()
    st.bar_chart(type_counts)

    # Filter
    st.markdown("### Filter by Type")
    types_list = ['All'] + list(df['type'].unique())
    selected_type = st.selectbox("Select Category", types_list)
    
    if selected_type != 'All':
        df = df[df['type'] == selected_type]

    # Search
    st.markdown("### Search Opportunities")
    search_term = st.text_input("Search by title, organization, or description")
    if search_term:
        df = df[df['title'].str.contains(search_term, case=False) | 
                df['organization'].str.contains(search_term, case=False) |
                df['description'].str.contains(search_term, case=False)]

    # Display
    st.markdown(f"### Found {len(df)} Opportunities")
    
    for idx, row in df.iterrows():
        with st.container():
            link = row.get('link', '#')
            
            st.markdown(f"**{row['title']}**")
            st.caption(f"🏷️ Type: {row['type']} | Source: {row['source']}")
            
            if 'organization' in row and row['organization'] != 'N/A':
                st.caption(f"🏢 Organization: {row['organization']}")
            
            description = row.get('description', 'N/A')
            if description != 'N/A' and len(description) > 300:
                description = description[:300] + "..."
            st.caption(f"📝 {description}")
            
            st.caption(f"📅 {row.get('deadline', 'N/A')}")
            
            # Show key fields
            if row.get('eligibility') and row['eligibility'] != 'N/A':
                st.caption(f"✅ Eligibility: {row['eligibility'][:150]}...")
            
            if row.get('benefits') and row['benefits'] != 'N/A':
                st.caption(f"💰 Benefits: {row['benefits'][:150]}...")
            
            st.caption(f"🔗 [Apply Here]({link})")
            st.divider()

    # Download buttons
    st.markdown("---")
    st.markdown("### Download Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Download CSV",
            data=csv,
            file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        def create_pdf(df):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                   rightMargin=40, leftMargin=40,
                                   topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            elements = []
            
            # ====== TITLE SECTION ======
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a5276'),
                alignment=TA_CENTER,
                spaceAfter=20
            )
            elements.append(Paragraph("FutureFinder Africa", title_style))
            elements.append(Paragraph("Verified Opportunities Report", title_style))
            
            date_style = ParagraphStyle(
                'CustomDate',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", date_style))
            
            elements.append(Spacer(1, 20))
            
            # ====== SUMMARY TABLE ======
            summary_style = ParagraphStyle(
                'CustomSummary',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=6
            )
            elements.append(Paragraph(f"<b>Total Opportunities:</b> {len(df)}", summary_style))
            
            type_counts = df['type'].value_counts()
            type_text = " | ".join([f"{k}: {v}" for k, v in type_counts.items()])
            elements.append(Paragraph(f"<b>Categories:</b> {type_text}", summary_style))
            
            source_counts = df['source'].value_counts()
            source_text = " | ".join([f"{k}: {v}" for k, v in source_counts.items()])
            elements.append(Paragraph(f"<b>Sources:</b> {source_text}", summary_style))
            
            elements.append(Spacer(1, 30))
            
            # ====== HEADER STYLES ======
            header_style = ParagraphStyle(
                'HeaderStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.whitesmoke,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            cell_style = ParagraphStyle(
                'CellStyle',
                parent=styles['Normal'],
                fontSize=7,
                alignment=TA_LEFT,
                leading=10
            )
            
            link_style = ParagraphStyle(
                'LinkStyle',
                parent=styles['Normal'],
                fontSize=7,
                textColor=colors.HexColor('#1a5276'),
                alignment=TA_LEFT,
                fontName='Helvetica'
            )
            
            # ====== MAIN TABLE ======
            for idx, row in df.iterrows():
                # Opportunity title
                opp_title_style = ParagraphStyle(
                    'OppTitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.HexColor('#1a5276'),
                    spaceAfter=6
                )
                elements.append(Paragraph(f"{idx+1}. {row['title']}", opp_title_style))
                
                # Organization
                org = row.get('organization', 'N/A')
                elements.append(Paragraph(f"<b>Organization:</b> {org}", cell_style))
                
                # Type and Source
                opp_type = row.get('type', 'N/A')
                source = row.get('source', 'N/A')
                elements.append(Paragraph(f"<b>Type:</b> {opp_type} | <b>Source:</b> {source}", cell_style))
                
                # Deadline
                deadline = row.get('deadline', 'N/A')
                elements.append(Paragraph(f"<b>Deadline:</b> {deadline}", cell_style))
                
                # Description
                desc = row.get('description', 'N/A')
                if len(desc) > 500:
                    desc = desc[:500] + "..."
                elements.append(Paragraph(f"<b>Description:</b> {desc}", cell_style))
                
                # Eligibility
                eligibility = row.get('eligibility', 'N/A')
                if eligibility != 'N/A' and len(eligibility) > 300:
                    eligibility = eligibility[:300] + "..."
                elements.append(Paragraph(f"<b>Eligibility:</b> {eligibility}", cell_style))
                
                # Benefits
                benefits = row.get('benefits', 'N/A')
                if benefits != 'N/A' and len(benefits) > 300:
                    benefits = benefits[:300] + "..."
                elements.append(Paragraph(f"<b>Benefits:</b> {benefits}", cell_style))
                
                # Link
                link = row.get('link', '#')
                elements.append(Paragraph(f"<b>Apply Link:</b> <a href='{link}' color='blue'>{link}</a>", link_style))
                
                # Verification note
                elements.append(Paragraph(f"<i>Verified from official {source} website</i>", cell_style))
                
                elements.append(Spacer(1, 12))
                elements.append(Paragraph("-" * 80, cell_style))
                elements.append(Spacer(1, 12))
            
            # ====== FOOTER ======
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceBefore=20
            )
            elements.append(Paragraph("All opportunities verified from official sources. Links are clickable.", footer_style))
            elements.append(Paragraph(f"Generated by FutureFinder Africa", footer_style))
            
            doc.build(elements)
            buffer.seek(0)
            return buffer
        
        pdf_buffer = create_pdf(df)
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_buffer,
            file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )import streamlit as st
import pandas as pd
from scraper import run_scraper
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

st.set_page_config(page_title="FutureFinder Africa", layout="wide")

st.title("🇺🇬 FutureFinder Africa")
st.subheader("Verified Opportunities for African Youth")
st.markdown("---")

# Sidebar
st.sidebar.markdown("### About")
st.sidebar.info("Automatically finds and verifies scholarships, jobs, grants, fellowships for African youth")

st.sidebar.markdown("### Sources")
st.sidebar.text("• One Young World")
st.sidebar.text("• DAAD")
st.sidebar.text("• Mastercard Foundation")
st.sidebar.text("• UNDP")
st.sidebar.text("• African Union")

# Refresh button
if st.button("🔄 Refresh Data Now"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)
def load_data():
    with st.spinner("Fetching latest opportunities..."):
        data = run_scraper()
        return data

# Load data
data = load_data()

if not data:
    st.warning("No opportunities found. Please try again later.")
else:
    # Metrics
    df = pd.DataFrame(data)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Opportunities", len(df))
    with col2:
        types = df['type'].value_counts()
        st.metric("Categories", len(types))
    with col3:
        sources = df['source'].nunique()
        st.metric("Sources", sources)
    with col4:
        st.metric("Last Updated", datetime.now().strftime("%H:%M"))

    # Category Breakdown
    st.markdown("### Category Breakdown")
    type_counts = df['type'].value_counts()
    st.bar_chart(type_counts)

    # Filter
    st.markdown("### Filter by Type")
    types_list = ['All'] + list(df['type'].unique())
    selected_type = st.selectbox("Select Category", types_list)
    
    if selected_type != 'All':
        df = df[df['type'] == selected_type]

    # Search
    st.markdown("### Search Opportunities")
    search_term = st.text_input("Search by title, organization, or description")
    if search_term:
        df = df[df['title'].str.contains(search_term, case=False) | 
                df['organization'].str.contains(search_term, case=False) |
                df['description'].str.contains(search_term, case=False)]

    # Display
    st.markdown(f"### Found {len(df)} Opportunities")
    
    for idx, row in df.iterrows():
        with st.container():
            link = row.get('link', '#')
            
            st.markdown(f"**{row['title']}**")
            st.caption(f"🏷️ Type: {row['type']} | Source: {row['source']}")
            
            if 'organization' in row and row['organization'] != 'N/A':
                st.caption(f"🏢 Organization: {row['organization']}")
            
            description = row.get('description', 'N/A')
            if description != 'N/A' and len(description) > 300:
                description = description[:300] + "..."
            st.caption(f"📝 {description}")
            
            st.caption(f"📅 {row.get('deadline', 'N/A')}")
            
            # Show key fields
            if row.get('eligibility') and row['eligibility'] != 'N/A':
                st.caption(f"✅ Eligibility: {row['eligibility'][:150]}...")
            
            if row.get('benefits') and row['benefits'] != 'N/A':
                st.caption(f"💰 Benefits: {row['benefits'][:150]}...")
            
            st.caption(f"🔗 [Apply Here]({link})")
            st.divider()

    # Download buttons
    st.markdown("---")
    st.markdown("### Download Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Download CSV",
            data=csv,
            file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        def create_pdf(df):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                   rightMargin=40, leftMargin=40,
                                   topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            elements = []
            
            # ====== TITLE SECTION ======
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a5276'),
                alignment=TA_CENTER,
                spaceAfter=20
            )
            elements.append(Paragraph("FutureFinder Africa", title_style))
            elements.append(Paragraph("Verified Opportunities Report", title_style))
            
            date_style = ParagraphStyle(
                'CustomDate',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", date_style))
            
            elements.append(Spacer(1, 20))
            
            # ====== SUMMARY TABLE ======
            summary_style = ParagraphStyle(
                'CustomSummary',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=6
            )
            elements.append(Paragraph(f"<b>Total Opportunities:</b> {len(df)}", summary_style))
            
            type_counts = df['type'].value_counts()
            type_text = " | ".join([f"{k}: {v}" for k, v in type_counts.items()])
            elements.append(Paragraph(f"<b>Categories:</b> {type_text}", summary_style))
            
            source_counts = df['source'].value_counts()
            source_text = " | ".join([f"{k}: {v}" for k, v in source_counts.items()])
            elements.append(Paragraph(f"<b>Sources:</b> {source_text}", summary_style))
            
            elements.append(Spacer(1, 30))
            
            # ====== HEADER STYLES ======
            header_style = ParagraphStyle(
                'HeaderStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.whitesmoke,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            cell_style = ParagraphStyle(
                'CellStyle',
                parent=styles['Normal'],
                fontSize=7,
                alignment=TA_LEFT,
                leading=10
            )
            
            link_style = ParagraphStyle(
                'LinkStyle',
                parent=styles['Normal'],
                fontSize=7,
                textColor=colors.HexColor('#1a5276'),
                alignment=TA_LEFT,
                fontName='Helvetica'
            )
            
            # ====== MAIN TABLE ======
            for idx, row in df.iterrows():
                # Opportunity title
                opp_title_style = ParagraphStyle(
                    'OppTitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.HexColor('#1a5276'),
                    spaceAfter=6
                )
                elements.append(Paragraph(f"{idx+1}. {row['title']}", opp_title_style))
                
                # Organization
                org = row.get('organization', 'N/A')
                elements.append(Paragraph(f"<b>Organization:</b> {org}", cell_style))
                
                # Type and Source
                opp_type = row.get('type', 'N/A')
                source = row.get('source', 'N/A')
                elements.append(Paragraph(f"<b>Type:</b> {opp_type} | <b>Source:</b> {source}", cell_style))
                
                # Deadline
                deadline = row.get('deadline', 'N/A')
                elements.append(Paragraph(f"<b>Deadline:</b> {deadline}", cell_style))
                
                # Description
                desc = row.get('description', 'N/A')
                if len(desc) > 500:
                    desc = desc[:500] + "..."
                elements.append(Paragraph(f"<b>Description:</b> {desc}", cell_style))
                
                # Eligibility
                eligibility = row.get('eligibility', 'N/A')
                if eligibility != 'N/A' and len(eligibility) > 300:
                    eligibility = eligibility[:300] + "..."
                elements.append(Paragraph(f"<b>Eligibility:</b> {eligibility}", cell_style))
                
                # Benefits
                benefits = row.get('benefits', 'N/A')
                if benefits != 'N/A' and len(benefits) > 300:
                    benefits = benefits[:300] + "..."
                elements.append(Paragraph(f"<b>Benefits:</b> {benefits}", cell_style))
                
                # Link
                link = row.get('link', '#')
                elements.append(Paragraph(f"<b>Apply Link:</b> <a href='{link}' color='blue'>{link}</a>", link_style))
                
                # Verification note
                elements.append(Paragraph(f"<i>Verified from official {source} website</i>", cell_style))
                
                elements.append(Spacer(1, 12))
                elements.append(Paragraph("-" * 80, cell_style))
                elements.append(Spacer(1, 12))
            
            # ====== FOOTER ======
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceBefore=20
            )
            elements.append(Paragraph("All opportunities verified from official sources. Links are clickable.", footer_style))
            elements.append(Paragraph(f"Generated by FutureFinder Africa", footer_style))
            
            doc.build(elements)
            buffer.seek(0)
            return buffer
        
        pdf_buffer = create_pdf(df)
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_buffer,
            file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
