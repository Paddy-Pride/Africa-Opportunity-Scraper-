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
            # Check if original_apply_link exists
            link = row.get('original_apply_link', row.get('link', '#'))
            
            # Title as clickable link
            st.markdown(f"**[{row['title']}]({link})**")
            
            # Company
            if 'company' in row and row['company'] != 'N/A':
                st.caption(f"Company: {row['company']}")
            
            # Description (cleaned)
            description = row.get('description', 'N/A')
            if description != 'N/A' and len(description) > 300:
                description = description[:300] + "..."
            st.caption(f"Description: {description}")
            
            # Date and type
            posted_date = row.get('posted_date', 'N/A')
            st.caption(f"Date: {posted_date}  |  Type: {row['type']}")
            
            # Show original link
            st.caption(f"Apply Link: {link}")
            
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
        # PDF Download with links
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
                alignment=1,
                spaceAfter=20
            )
            elements.append(Paragraph("Africa Youth Opportunities Report", title_style))
            
            # Date
            date_style = ParagraphStyle(
                'CustomDate',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=1,
                spaceAfter=20
            )
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", date_style))
            
            # Summary
            summary_style = ParagraphStyle(
                'CustomSummary',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=6
            )
            elements.append(Paragraph(f"Total Opportunities: {len(df)}", summary_style))
            
            # Category breakdown
            type_counts = df['type'].value_counts()
            type_text = " | ".join([f"{k}: {v}" for k, v in type_counts.items()])
            elements.append(Paragraph(f"Categories: {type_text}", summary_style))
            elements.append(Spacer(1, 20))
            
            # Define styles
            header_style = ParagraphStyle(
                'HeaderStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.whitesmoke,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            
            cell_style = ParagraphStyle(
                'CellStyle',
                parent=styles['Normal'],
                fontSize=7,
                alignment=1,
                leading=10
            )
            
            link_style = ParagraphStyle(
                'LinkStyle',
                parent=styles['Normal'],
                fontSize=7,
                textColor=colors.HexColor('#1a5276'),
                alignment=1,
                fontName='Helvetica'
            )
            
            # Table headers with ALL columns
            table_data = [
                [
                    Paragraph("Title", header_style),
                    Paragraph("Company", header_style),
                    Paragraph("Category", header_style),
                    Paragraph("Date", header_style),
                    Paragraph("Apply Link", header_style)
                ]
            ]
            
            # Add rows with links - use get() to avoid KeyError
for idx, row in df.iterrows():
    # Get link safely - try original_apply_link first, then link, then fallback to #
    link_url = row.get('original_apply_link', row.get('link', '#'))
    
    # Title with link
    title_text = str(row['title'])[:35] + '...' if len(str(row['title'])) > 35 else str(row['title'])
    title_cell = Paragraph(f'<a href="{link_url}" color="blue">{title_text}</a>', link_style)
    
    # Company
    company_text = str(row.get('company', 'N/A'))[:20] + '...' if len(str(row.get('company', 'N/A'))) > 20 else str(row.get('company', 'N/A'))
    company_cell = Paragraph(company_text, cell_style)
    
    # Category
    category_cell = Paragraph(str(row['type']), cell_style)
    
    # Date
    date_text = str(row.get('posted_date', 'N/A'))
    date_cell = Paragraph(date_text, cell_style)
    
    # Apply Link - use the same link_url
    link_display = link_url[:40] + '...' if len(link_url) > 40 else link_url
    link_cell = Paragraph(f'<a href="{link_url}" color="blue">{link_display}</a>', link_style)
    
    table_data.append([title_cell, company_cell, category_cell, date_cell, link_cell])
            
            # Create table with ALL columns
            table = Table(table_data, colWidths=[1.6*inch, 1.0*inch, 0.8*inch, 1.2*inch, 1.8*inch])
            table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                # Body
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('LEADING', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')]),
            ]))
            
            elements.append(table)
            
            # Add note about clickable links
            note_style = ParagraphStyle(
                'NoteStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=1,
                spaceBefore=20
            )
            elements.append(Paragraph("Note: All titles and links are clickable in this PDF", note_style))
            
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
