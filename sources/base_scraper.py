"""
Base Scraper Class
"""

import logging
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base scraper class with common functionality"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 30
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape opportunities - to be overridden by subclasses
        
        Returns:
            List of opportunity dictionaries
        """
        return self._get_sample_data()
    
    def _safe_request(self, url: str) -> requests.Response:
        """Make a safe request with retry logic"""
        try:
            time.sleep(1)  # Be polite to servers
            return self.session.get(url, timeout=self.timeout)
        except Exception as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            raise
    
    def _parse_date(self, date_string: str) -> str:
        """Parse and format date string"""
        if not date_string:
            return 'N/A'
        try:
            # Try common date formats
            date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%b %d, %Y', '%d %b %Y', '%B %d, %Y']
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_string, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return date_string
        except Exception:
            return date_string
    
    def _create_opportunity(self, title: str, url: str, description: str = '', 
                           category: str = 'General', country: str = 'Africa', 
                           deadline: str = 'N/A') -> Dict[str, Any]:
        """Create a standardized opportunity dictionary"""
        return {
            'title': title,
            'organization': self.name,
            'category': category,
            'country': country,
            'deadline': deadline,
            'description': description[:500] if description else 'No description available',
            'official_url': url,
            'source': self.name,
            'verified': False,
            'date_scraped': datetime.now().isoformat()
        }
    
    def _get_sample_data(self) -> List[Dict[str, Any]]:
        """Get sample data as fallback"""
        return [self._create_opportunity(
            f"{self.name} Opportunities",
            self.base_url,
            f"Various opportunities available at {self.name}. Check the official website for more details.",
            'General',
            'Africa'
        )]
