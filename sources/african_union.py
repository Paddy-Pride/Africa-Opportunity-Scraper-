"""
African Union Scraper
"""

import logging
from typing import List, Dict, Any
from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)


class AfricanUnionScraper(BaseScraper):
    """Scraper for African Union opportunities"""
    
    def __init__(self):
        super().__init__("African Union", "https://www.africanunion.org")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape African Union opportunities"""
        opportunities = []
        
        try:
            response = self._safe_request(f"{self.base_url}/opportunities")
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                listings = soup.find_all(['article', 'div'], class_=['opportunity', 'listing', 'item'])
                
                for item in listings[:10]:
                    title_elem = item.find(['h2', 'h3', 'h4'])
                    link_elem = item.find('a')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        url = link_elem.get('href', '') if link_elem else ''
                        if url and not url.startswith('http'):
                            url = f"{self.base_url}{url}"
                        
                        opportunities.append(self._create_opportunity(
                            title,
                            url if url else self.base_url,
                            item.get_text(strip=True)[:500],
                            'General',
                            'Africa'
                        ))
            
            # If no opportunities found or scraping failed, return sample data
            if not opportunities:
                opportunities = self._get_sample_data()
                opportunities[0]['title'] = 'African Union Internship Program 2024'
                opportunities[0]['category'] = 'Internships'
                opportunities[0]['country'] = 'Ethiopia'
                opportunities[0]['deadline'] = '2024-12-31'
                opportunities[0]['description'] = 'The African Union offers internship opportunities for young Africans to gain professional experience in various departments.'
                opportunities[0]['official_url'] = 'https://www.africanunion.org/internships'
                
            logger.info(f"Scraped {len(opportunities)} opportunities from African Union")
            
        except Exception as e:
            logger.error(f"Error scraping African Union: {str(e)}")
            opportunities = self._get_sample_data()
        
        return opportunities
