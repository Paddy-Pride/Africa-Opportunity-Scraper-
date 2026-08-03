"""
Scraper Controller - Manages all source scrapers
"""

import logging
import concurrent.futures
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import requests
from bs4 import BeautifulSoup
import os
import sys

# Add the sources directory to path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sources import (
    AfricanUnionScraper,
    UnitedNationsScraper,
    WorldBankScraper,
    AfricanDevelopmentBankScraper,
    MastercardScraper,
    GoogleScraper,
    MicrosoftScraper,
    YouthHubScraper,
    OpportunitiesForAfricaScraper,
    UNICEFScraper,
    UNESCOScraper,
    UNDPScraper,
    BritishCouncilScraper,
    CommonwealthScraper
)
from sources.source_manager import SourceManager

logger = logging.getLogger(__name__)


class ScraperController:
    """Controller for managing all scrapers"""
    
    def __init__(self):
        """Initialize the scraper controller"""
        self.source_manager = SourceManager()
        self.scrapers = {
            'African Union': AfricanUnionScraper(),
            'United Nations': UnitedNationsScraper(),
            'World Bank': WorldBankScraper(),
            'African Development Bank': AfricanDevelopmentBankScraper(),
            'Mastercard Foundation': MastercardScraper(),
            'Google': GoogleScraper(),
            'Microsoft': MicrosoftScraper(),
            'Youth Hub Africa': YouthHubScraper(),
            'Opportunities For Africa': OpportunitiesForAfricaScraper(),
            'UNICEF': UNICEFScraper(),
            'UNESCO': UNESCOScraper(),
            'UNDP': UNDPScraper(),
            'British Council': BritishCouncilScraper(),
            'Commonwealth': CommonwealthScraper()
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def scrape_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scrape a single source
        
        Args:
            source: Source configuration dictionary
            
        Returns:
            List of opportunity dictionaries
        """
        source_name = source.get('name', '')
        source_url = source.get('url', '')
        
        logger.info(f"Scraping source: {source_name}")
        
        try:
            # Try to use built-in scraper first
            if source_name in self.scrapers:
                scraper = self.scrapers[source_name]
                opportunities = scraper.scrape()
            else:
                # Use generic scraper for custom sources
                opportunities = self._generic_scrape(source_url)
            
            # Add source information
            for opp in opportunities:
                opp['source'] = source_name
                opp['source_url'] = source_url
                opp['date_scraped'] = datetime.now().isoformat()
            
            logger.info(f"Scraped {len(opportunities)} opportunities from {source_name}")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {str(e)}")
            return []
    
    def _generic_scrape(self, url: str) -> List[Dict[str, Any]]:
        """
        Generic scraper for custom sources
        
        Args:
            url: URL to scrape
            
        Returns:
            List of opportunity dictionaries
        """
        opportunities = []
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for common patterns
            # This is a simplified generic scraper - would need enhancement
            # for specific website structures
            
            # Find links that look like opportunities
            links = soup.find_all('a', href=True)
            for link in links[:20]:  # Limit to 20 to avoid overload
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if href and len(text) > 10:  # Simple filter
                    opportunity = {
                        'title': text[:200],
                        'organization': 'Unknown',
                        'category': 'General',
                        'country': 'Africa',
                        'deadline': 'N/A',
                        'description': text[:500],
                        'official_url': href if href.startswith('http') else requests.compat.urljoin(url, href),
                        'source': 'Custom',
                        'verified': False,
                        'date_scraped': datetime.now().isoformat()
                    }
                    opportunities.append(opportunity)
            
        except Exception as e:
            logger.error(f"Generic scrape failed for {url}: {str(e)}")
        
        return opportunities
    
    def scrape_all(self, custom_sources: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Scrape all enabled sources
        
        Args:
            custom_sources: Optional list of custom sources to scrape
            
        Returns:
            List of all scraped opportunities
        """
        all_opportunities = []
        sources_to_scrape = []
        
        # Get sources from database
        db_sources = self.source_manager.get_enabled_sources()
        sources_to_scrape.extend(db_sources)
        
        # Add custom sources if provided
        if custom_sources:
            sources_to_scrape.extend(custom_sources)
        
        if not sources_to_scrape:
            logger.warning("No sources to scrape")
            return []
        
        # Scrape sources concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {
                executor.submit(self.scrape_source, source): source
                for source in sources_to_scrape
            }
            
            for future in concurrent.futures.as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    opportunities = future.result(timeout=60)
                    all_opportunities.extend(opportunities)
                    
                    # Update last scraped time
                    self.source_manager.update_source_scrape_time(source.get('id', 0))
                    
                except Exception as e:
                    logger.error(f"Error scraping {source.get('name', 'Unknown')}: {str(e)}")
        
        # Deduplicate opportunities
        deduplicated = self._deduplicate_opportunities(all_opportunities)
        
        logger.info(f"Scraped {len(deduplicated)} unique opportunities from {len(sources_to_scrape)} sources")
        return deduplicated
    
    def _deduplicate_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate opportunities by URL and title
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            Deduplicated list
        """
        seen = set()
        deduplicated = []
        
        for opp in opportunities:
            url = opp.get('official_url', '')
            title = opp.get('title', '')[:50]  # Use first 50 chars for matching
            key = f"{url}:{title}"
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(opp)
        
        return deduplicated
