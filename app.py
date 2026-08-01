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

st.set_page_config(page_title="FutureFinder Africa", layout="wide")

st.title("FutureFinder Africa")
st.subheader("Verified Opportunities for African Youth")
st.markdown("---")

# Sidebar
st.sidebar.markdown("About")
st.sidebar.info("Automatically finds and verifies scholarships, jobs, grants, fellowships for African youth")
st.sidebar.markdown("Sources")
st.sidebar.text("One Young World")
st.sidebar.text("DAAD")
st.sidebar.text("Mastercard Foundation")
st.sidebar.text("African Union")
st.sidebar.text("UNDP")
st.sidebar.text("MyJobMag")
st.sidebar.text("Remotive")

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
    search_term = st.text_input("Search by title, company, or description")
    if search_term:
        df = df[df['title'].str.contains(search_term, case=False) | 
                df['company'].str.contains(search_term, case=False) |
                df['description'].str.contains(search_term, case=False)]

    # Display
    st.markdown(f"### Found {len(df)} Opportunities")
    
    for idx, row in df.iterrows():
        with st.container():
            # Get link safely
            link = row.get('original_apply_link', row.get('link', '#'))
            
            # Title as clickable link with type badge
            st.markdown(f"**[{row['title']}]({link})**")
            st.caption(f"🏷️ Type: {row['type']} | Source: {row['source']}")
            
            # Company
            if 'company' in row and row['company'] != 'N/A':
                st.caption(f"🏢 {row['company']}")
            
            # Description (cleaned)
            description = row.get('description', 'N/A')
            if description != 'N/A' and len(description) > 300:
                description = description[:300] + "..."
            st.caption(f"📝 {description}")
            
            # Date
            posted_date = row.get('posted_date', 'N/A')
            st.caption(f"📅 {posted_date}")
            
            st.divider()

    # Download buttons
    st.markdown("---")
    st.markdown("### Download Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        def create_pdf(df):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a5276'),
                alignment=1,
                spaceAfter=20
            )
            elements.append(Paragraph("FutureFinder Africa Opportunities Report", title_style))
            
            date_style = ParagraphStyle(
                'CustomDate',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=1,
                spaceAfter=20
            )
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", date_style))
            
            summary_style = ParagraphStyle(
                'CustomSummary',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=6
            )
            elements.append(Paragraph(f"Total Opportunities: {len(df)}", summary_style))
            
            type_counts = df['type'].value_counts()
            type_text = " | ".join([f"{k}: {v}" for k, v in type_counts.items()])
            elements.append(Paragraph(f"Categories: {type_text}", summary_style))
            elements.append(Spacer(1, 20))
            
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
            
            table_data = [
                [
                    Paragraph("Title", header_style),
                    Paragraph("Company", header_style),
                    Paragraph("Category", header_style),
                    Paragraph("Date", header_style),
                    Paragraph("Apply Link", header_style)
                ]
            ]
            
            for idx, row in df.iterrows():
                link_url = row.get('original_apply_link', row.get('link', '#'))
                
                title_text = str(row['title'])[:30] + '...' if len(str(row['title'])) > 30 else str(row['title'])
                title_cell = Paragraph(f'<a href="{link_url}" color="blue">{title_text}</a>', link_style)
                
                company_text = str(row.get('company', 'N/A'))[:20] + '...' if len(str(row.get('company', 'N/A'))) > 20 else str(row.get('company', 'N/A'))
                company_cell = Paragraph(company_text, cell_style)
                
                category_cell = Paragraph(str(row['type']), cell_style)
                date_cell = Paragraph(str(row.get('posted_date', 'N/A')), cell_style)
                
                link_display = link_url[:40] + '...' if len(link_url) > 40 else link_url
                link_cell = Paragraph(f'<a href="{link_url}" color="blue">{link_display}</a>', link_style)
                
                table_data.append([title_cell, company_cell, category_cell, date_cell, link_cell])
            
            table = Table(table_data, colWidths=[1.6*inch, 1.0*inch, 0.8*inch, 1.2*inch, 1.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('LEADING', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')]),
            ]))
            
            elements.append(table)
            
            note_style = ParagraphStyle(
                'NoteStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=1,
                spaceBefore=20
            )
            elements.append(Paragraph("Note: All titles and links are clickable. Opportunities are verified from official sources.", note_style))
            
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
