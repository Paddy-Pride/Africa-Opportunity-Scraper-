# Table headers with original links
table_data = [
    [
        Paragraph("Title", header_style),
        Paragraph("Company", header_style),
        Paragraph("Category", header_style),
        Paragraph("Date", header_style),
        Paragraph("Apply Link (Original)", header_style)  # Changed to show original
    ]
]

# Add rows with original links
for idx, row in df.iterrows():
    # Title with link to original company site
    title_text = str(row['title'])[:40] + '...' if len(str(row['title'])) > 40 else str(row['title'])
    title_cell = Paragraph(f'<a href="{row["original_apply_link"]}" color="blue">{title_text}</a>', link_style)
    
    company_text = str(row.get('company', 'N/A'))[:25] + '...' if len(str(row.get('company', 'N/A'))) > 25 else str(row.get('company', 'N/A'))
    company_cell = Paragraph(company_text, cell_style)
    
    category_cell = Paragraph(str(row['type']), cell_style)
    date_cell = Paragraph(str(row['posted_date'])[:20], cell_style)
    
    # Show original link
    link_text = str(row['original_apply_link'])
    link_cell = Paragraph(f'<a href="{row["original_apply_link"]}" color="blue">{link_text}</a>', link_style)
    
    table_data.append([title_cell, company_cell, category_cell, date_cell, link_cell])
