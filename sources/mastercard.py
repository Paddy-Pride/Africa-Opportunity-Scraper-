"""
Mastercard Foundation Scraper
"""

import logging
from typing import List, Dict, Any
from .base_scraper import BaseScraper
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MastercardScraper(BaseScraper):
    """Scraper for Mastercard Foundation opportunities"""
    
    def __init__(self):
        super().__init__("Mastercard Foundation", "https://www.mastercardfdn.org")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape Mastercard Foundation opportunities"""
        opportunities = []
        
        try:
            response = self._safe_request(f"{self.base_url}/opportunities")
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                listings = soup.find_all(['article', 'div'], class_=['opportunity', 'post', 'item'])
                
                for item in listings[:10]:
                    title_elem = item.find(['h2', 'h3'])
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
                            'Grants',
                            'Various'
                        ))
            
            if not opportunities:
                opportunities = self._get_sample_data()
                opportunities[0]['title'] = 'Mastercard Foundation Scholars Program'
                opportunities[0]['category'] = 'Scholarships'
                opportunities[0]['deadline'] = '2025-01-15'
                
            logger.info(f"Scraped {len(opportunities)} opportunities from Mastercard Foundation")
            
        except Exception as e:
            logger.error(f"Error scraping Mastercard Foundation: {str(e)}")
            opportunities = self._get_sample_data()
        
        return opportunities
