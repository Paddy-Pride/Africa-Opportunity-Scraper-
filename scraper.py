"""
Scraper Controller - Manages all source scrapers
"""

import logging
import concurrent.futures
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import os
import sys

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sources.source_manager import SourceManager

# Try to import scrapers
try:
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
except ImportError as e:
    print(f"Warning: Some scrapers could not be imported: {e}")
    # Define as None if import fails
    AfricanUnionScraper = None
    UnitedNationsScraper = None
    WorldBankScraper = None
    AfricanDevelopmentBankScraper = None
    MastercardScraper = None
    GoogleScraper = None
    MicrosoftScraper = None
    YouthHubScraper = None
    OpportunitiesForAfricaScraper = None
    UNICEFScraper = None
    UNESCOScraper = None
    UNDPScraper = None
    BritishCouncilScraper = None
    CommonwealthScraper = None

logger = logging.getLogger(__name__)


class ScraperController:
    """Controller for managing all scrapers"""
    
    def __init__(self):
        """Initialize the scraper controller"""
        self.source_manager = SourceManager()
        self.scrapers = {}
        self._init_scrapers()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _init_scrapers(self):
        """Initialize scrapers"""
        scraper_map = {
            'African Union': AfricanUnionScraper,
            'United Nations': UnitedNationsScraper,
            'World Bank': WorldBankScraper,
            'African Development Bank': AfricanDevelopmentBankScraper,
            'Mastercard Foundation': MastercardScraper,
            'Google': GoogleScraper,
            'Microsoft': MicrosoftScraper,
            'Youth Hub Africa': YouthHubScraper,
            'Opportunities For Africa': OpportunitiesForAfricaScraper,
            'UNICEF': UNICEFScraper,
            'UNESCO': UNESCOScraper,
            'UNDP': UNDPScraper,
            'British Council': BritishCouncilScraper,
            'Commonwealth': CommonwealthScraper
        }
        
        for name, scraper_class in scraper_map.items():
            if scraper_class is not None:
                try:
                    self.scrapers[name] = scraper_class()
                except Exception as e:
                    logger.warning(f"Could not initialize {name} scraper: {e}")
            else:
                logger.warning(f"{name} scraper not available")
    
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
            opportunities = []
            
            # Try to use built-in scraper first
            if source_name in self.scrapers:
                try:
                    scraper = self.scrapers[source_name]
                    opportunities = scraper.scrape()
                    logger.info(f"Used built-in scraper for {source_name}")
                except Exception as e:
                    logger.error(f"Built-in scraper failed for {source_name}: {str(e)}")
                    opportunities = []
            
            # If no opportunities from built-in scraper, try generic scrape
            if not opportunities:
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
            
            # Find links that look like opportunities
            links = soup.find_all('a', href=True)
            for link in links[:20]:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if href and len(text) > 10:
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
        try:
            db_sources = self.source_manager.get_enabled_sources()
            sources_to_scrape.extend(db_sources)
        except Exception as e:
            logger.error(f"Error getting sources from database: {str(e)}")
        
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
                    try:
                        self.source_manager.update_source_scrape_time(source.get('id', 0))
                    except Exception as e:
                        logger.error(f"Error updating scrape time: {str(e)}")
                    
                except Exception as e:
                    logger.error(f"Error scraping {source.get('name', 'Unknown')}: {str(e)}")
        
        # Deduplicate opportunities
        deduplicated = self._deduplicate_opportunities(all_opportunities)
        
        logger.info(f"Scraped {len(deduplicated)} unique opportunities from {len(sources_to_scrape)} sources")
        return deduplicated
    
    def _deduplicate_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate opportunities by URL and title"""
        seen = set()
        deduplicated = []
        
        for opp in opportunities:
            url = opp.get('official_url', '')
            title = opp.get('title', '')[:50]
            key = f"{url}:{title}"
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(opp)
        
        return deduplicated
