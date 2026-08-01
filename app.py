import streamlit as st
import pandas as pd
from scraper import run_scraper
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

st.set_page_config(page_title="Africa Opportunities", layout="wide")

st.title("Africa Youth Opportunity Finder")
st.markdown("---")

# Sidebar
st.sidebar.markdown("About")
st.sidebar.info("Automatically finds scholarships, jobs, grants, fellowships for African youth")
st.sidebar.markdown("Sources")
st.sidebar.text("MyJobMag Kenya")
st.sidebar.text("Remotive API")
st.sidebar.text("Curated Programs")

# Refresh button
if st.button("Refresh Data Now"):
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
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Opportunities", len(data))
    with col2:
        types = pd.DataFrame(data)['type'].value_counts()
        st.metric("Categories", len(types))
    with col3:
        st.metric("Last Updated", datetime.now().strftime("%H:%M"))

    # Filter
    st.markdown("### Filter by Type")
    df = pd.DataFrame(data)
    types_list = ['All'] + list(df['type'].unique())
    selected_type = st.selectbox("Select Category", types_list)
    
    if selected_type != 'All':
        df = df[df['type'] == selected_type]

    # Display
    st.markdown(f"### Found {len(df)} Opportunities")
    
    for idx, row in df.iterrows():
        with st.container():
            # Title as clickable link
            st.markdown(f"**[{row['title']}]({row['link']})**")
            
            # Company
            if 'company' in row and row['company'] != 'N/A':
                st.caption(f"Company: {row['company']}")
            
            # Description (cleaned)
            description = row['description']
            if description != 'N/A' and len(description) > 300:
                description = description[:300] + "..."
            st.caption(f"Description: {description}")
            
            # Date and type
            st.caption(f"Date: {row['posted_date']}  |  Type: {row['type']}")
            
            st.divider()

    # Download buttons
    st.markdown("---")
    st.markdown("### Download Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # PDF Download
        def create_pdf(df):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a5276'),
                alignment=1
            )
            elements.append(Paragraph("Africa Youth Opportunities Report", title_style))
            elements.append(Spacer(1, 12))
            
            # Date
            date_style = ParagraphStyle(
                'CustomDate',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.grey
            )
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", date_style))
            elements.append(Spacer(1, 12))
            
            # Summary
            summary_style = ParagraphStyle(
                'CustomSummary',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor('#2c3e50')
            )
            elements.append(Paragraph(f"Total Opportunities: {len(df)}", summary_style))
            elements.append(Spacer(1, 6))
            
            # Category breakdown
            type_counts = df['type'].value_counts()
            type_text = " | ".join([f"{k}: {v}" for k, v in type_counts.items()])
            elements.append(Paragraph(f"Categories: {type_text}", summary_style))
            elements.append(Spacer(1, 20))
            
            # Table data
            table_data = [['Title', 'Company', 'Category', 'Date']]
            for idx, row in df.iterrows():
                table_data.append([
                    str(row['title'])[:50] + '...' if len(str(row['title'])) > 50 else str(row['title']),
                    str(row.get('company', 'N/A'))[:30] + '...' if len(str(row.get('company', 'N/A'))) > 30 else str(row.get('company', 'N/A')),
                    str(row['type']),
                    str(row['posted_date'])[:20]
                ])
            
            # Create table
            table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(table)
            doc.build(elements)
            buffer.seek(0)
            return buffer
        
        pdf_buffer = create_pdf(df)
        st.download_button(
            label="Download PDF Report",
            data=pdf_buffer,
            file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
