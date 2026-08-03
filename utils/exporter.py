"""
Exporter - Export opportunities to various formats
"""

import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from io import BytesIO, StringIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class Exporter:
    """Export opportunities to various formats"""
    
    def __init__(self):
        """Initialize the exporter"""
        self.styles = getSampleStyleSheet()
        
        # Custom style for PDF
        self.styles.add(ParagraphStyle(
            name='Custom',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12
        ))
    
    def export_to_csv(self, opportunities: List[Dict[str, Any]]) -> str:
        """
        Export opportunities to CSV format
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            CSV string
        """
        if not opportunities:
            return ""
        
        try:
            # Flatten nested dictionaries
            flattened = []
            for opp in opportunities:
                flat_opp = opp.copy()
                
                # Handle nested fields
                if 'verification_details' in flat_opp:
                    flat_opp['verification_details'] = ', '.join(flat_opp['verification_details'])
                
                if 'match_score' in flat_opp:
                    flat_opp['match_percentage'] = f"{flat_opp['match_score'] * 100:.2f}%"
                
                flattened.append(flat_opp)
            
            df = pd.DataFrame(flattened)
            
            # Select and order columns
            columns = [
                'title', 'organization', 'category', 'country', 'deadline',
                'description', 'official_url', 'source', 'verified',
                'match_score', 'date_scraped'
            ]
            
            # Only include columns that exist
            existing_columns = [col for col in columns if col in df.columns]
            df = df[existing_columns]
            
            return df.to_csv(index=False)
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return ""
    
    def export_to_json(self, opportunities: List[Dict[str, Any]]) -> str:
        """
        Export opportunities to JSON format
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            JSON string
        """
        if not opportunities:
            return "[]"
        
        try:
            return json.dumps(opportunities, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            return "[]"
    
    def export_to_excel(self, opportunities: List[Dict[str, Any]]) -> BytesIO:
        """
        Export opportunities to Excel format
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            BytesIO object containing Excel file
        """
        if not opportunities:
            return BytesIO()
        
        try:
            # Flatten nested dictionaries
            flattened = []
            for opp in opportunities:
                flat_opp = opp.copy()
                
                if 'verification_details' in flat_opp:
                    flat_opp['verification_details'] = ', '.join(flat_opp['verification_details'])
                
                flattened.append(flat_opp)
            
            df = pd.DataFrame(flattened)
            
            # Create Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Opportunities', index=False)
                
                # Auto-adjust column widths
                for column in df:
                    column_width = max(df[column].astype(str).map(len).max(), len(column))
                    col_idx = df.columns.get_loc(column)
                    writer.sheets['Opportunities'].column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 50)
            
            output.seek(0)
            return output
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            return BytesIO()
    
    def export_to_pdf(self, opportunities: List[Dict[str, Any]]) -> BytesIO:
        """
        Export opportunities to PDF format
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            BytesIO object containing PDF file
        """
        if not opportunities:
            return BytesIO()
        
        try:
            output = BytesIO()
            doc = SimpleDocTemplate(output, pagesize=A4)
            
            # Create story
            story = []
            
            # Title
            title_style = self.styles['Heading1']
            story.append(Paragraph("Africa Opportunity Finder - Opportunities Report", title_style))
            story.append(Spacer(1, 0.25 * inch))
            
            # Date
            date_style = self.styles['Normal']
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
            story.append(Spacer(1, 0.25 * inch))
            
            # Summary
            story.append(Paragraph(f"Total Opportunities: {len(opportunities)}", date_style))
            story.append(Spacer(1, 0.25 * inch))
            
            # Create table data
            table_data = [['Title', 'Organization', 'Category', 'Country', 'Deadline', 'Verified']]
            
            # Add opportunity data
            for opp in opportunities[:20]:  # Limit to 20 for PDF readability
                title = opp.get('title', 'N/A')[:50]  # Truncate
                org = opp.get('organization', 'N/A')[:30]
                category = opp.get('category', 'N/A')[:20]
                country = opp.get('country', 'N/A')[:20]
                deadline = opp.get('deadline', 'N/A')[:15]
                verified = '✓' if opp.get('verified', False) else '✗'
                
                table_data.append([title, org, category, country, deadline, verified])
            
            # Create table
            table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch, 1*inch, 0.5*inch])
            
            # Add style
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            
            output.seek(0)
            return output
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            return BytesIO()
    
    def export_as_attachment(self, data: Any, filename: str, format: str) -> bytes:
        """
        Export data as attachment
        
        Args:
            data: Data to export
            filename: Filename
            format: Format (csv, json, excel, pdf)
            
        Returns:
            Bytes of the exported file
        """
        if not data:
            return b''
        
        try:
            if format == 'csv':
                content = self.export_to_csv(data)
                return content.encode('utf-8')
                
            elif format == 'json':
                content = self.export_to_json(data)
                return content.encode('utf-8')
                
            elif format == 'excel':
                content = self.export_to_excel(data)
                return content.getvalue()
                
            elif format == 'pdf':
                content = self.export_to_pdf(data)
                return content.getvalue()
                
            else:
                logger.error(f"Unsupported format: {format}")
                return b''
                
        except Exception as e:
            logger.error(f"Error exporting as attachment: {str(e)}")
            return b''
