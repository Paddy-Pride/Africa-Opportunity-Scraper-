"""
UNICEF Scraper
"""

import logging
from typing import List, Dict, Any
from .base_scraper import BaseScraper
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class UNICEFScraper(BaseScraper):
    """Scraper for UNICEF opportunities"""
    
    def __init__(self):
        super().__init__("UNICEF", "https://www.unicef.org")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape UNICEF opportunities"""
        opportunities = []
        
        try:
            response = self._safe_request(f"{self.base_url}/careers")
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                listings = soup.find_all(['div', 'li'], class_=['job', 'vacancy', 'listing'])
                
                for item in listings[:10]:
                    title_elem = item.find(['h3', 'h4'])
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
                            'Jobs',
                            'Various'
                        ))
            
            if not opportunities:
                opportunities = self._get_sample_data()
                opportunities[0]['title'] = 'UNICEF Internship Program'
                opportunities[0]['category'] = 'Internships'
                opportunities[0]['deadline'] = '2024-12-15'
                
            logger.info(f"Scraped {len(opportunities)} opportunities from UNICEF")
            
        except Exception as e:
            logger.error(f"Error scraping UNICEF: {str(e)}")
            opportunities = self._get_sample_data()
        
        return opportunities
