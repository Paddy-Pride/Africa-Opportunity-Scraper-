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
import re

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
            
            # Filter out non-opportunity items
            opportunities = self._filter_opportunities(opportunities)
            
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
    
    def _filter_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out non-opportunity items
        
        Args:
            opportunities: List of opportunities to filter
            
        Returns:
            Filtered list
        """
        # Keywords that indicate this is NOT an opportunity
        exclude_keywords = [
            'skip to', 'navigation', 'menu', 'footer', 'header', 
            'search', 'login', 'register', 'sign up', 'sign in',
            'privacy policy', 'terms of service', 'cookie', 
            'about us', 'contact us', 'help', 'faq',
            'get involved', 'donate', 'support us', 'volunteer',
            'our projects', 'our strategy', 'global presence',
            'member states', 'people we serve', 'impact stories',
            'skip navigation', 'skip to content', 'skip to main'
        ]
        
        filtered = []
        
        for opp in opportunities:
            title = opp.get('title', '').lower()
            description = opp.get('description', '').lower()
            
            # Skip if title is too short (likely not an opportunity)
            if len(title) < 10:
                continue
            
            # Skip if it's a navigation or menu item
            is_excluded = False
            for keyword in exclude_keywords:
                if keyword in title or keyword in description:
                    is_excluded = True
                    break
            
            if not is_excluded:
                filtered.append(opp)
        
        return filtered
    
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
            
            # Look for common opportunity patterns
            # Find articles, posts, or list items that might be opportunities
            content_selectors = [
                'article', 'div.post', 'div.opportunity', 'div.job', 
                'div.listing', 'li', '.item', '.result', '.card'
            ]
            
            for selector in content_selectors:
                items = soup.select(selector)
                for item in items:
                    # Look for title and link
                    title_elem = item.find(['h2', 'h3', 'h4'])
                    link_elem = item.find('a')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        href = link_elem.get('href')
                        
                        # Skip if title is too short or looks like navigation
                        if len(title) < 10 or self._is_navigation(title):
                            continue
                        
                        # Get description
                        description = item.get_text(strip=True)[:500]
                        
                        # Build URL
                        if href:
                            if href.startswith('http'):
                                full_url = href
                            else:
                                full_url = requests.compat.urljoin(url, href)
                        else:
                            full_url = url
                        
                        # Only add if it looks like an opportunity
                        if self._is_opportunity_text(title, description):
                            opportunity = {
                                'title': title[:200],
                                'organization': 'Unknown',
                                'category': 'General',
                                'country': 'Africa',
                                'deadline': 'N/A',
                                'description': description,
                                'official_url': full_url,
                                'source': 'Custom',
                                'verified': False,
                                'date_scraped': datetime.now().isoformat()
                            }
                            opportunities.append(opportunity)
            
            # If we found nothing with specific selectors, try a broader approach
            if not opportunities:
                # Find all links with significant text
                links = soup.find_all('a', href=True)
                for link in links:
                    text = link.get_text(strip=True)
                    href = link.get('href')
                    
                    if len(text) > 20 and self._is_opportunity_text(text, ''):
                        if href:
                            if href.startswith('http'):
                                full_url = href
                            else:
                                full_url = requests.compat.urljoin(url, href)
                        else:
                            full_url = url
                        
                        opportunity = {
                            'title': text[:200],
                            'organization': 'Unknown',
                            'category': 'General',
                            'country': 'Africa',
                            'deadline': 'N/A',
                            'description': text[:500],
                            'official_url': full_url,
                            'source': 'Custom',
                            'verified': False,
                            'date_scraped': datetime.now().isoformat()
                        }
                        opportunities.append(opportunity)
            
        except Exception as e:
            logger.error(f"Generic scrape failed for {url}: {str(e)}")
        
        return opportunities
    
    def _is_navigation(self, text: str) -> bool:
        """Check if text looks like navigation"""
        nav_keywords = ['home', 'about', 'contact', 'menu', 'navigation', 'search', 
                       'login', 'register', 'sign up', 'sign in', 'privacy', 'terms']
        text_lower = text.lower()
        for keyword in nav_keywords:
            if keyword in text_lower:
                return True
        return False
    
    def _is_opportunity_text(self, title: str, description: str) -> bool:
        """Check if text looks like an opportunity"""
        # Keywords that indicate this is an opportunity
        opportunity_keywords = [
            'opportunity', 'program', 'scholarship', 'fellowship', 'internship',
            'grant', 'funding', 'training', 'workshop', 'conference', 'award',
            'prize', 'competition', 'apply', 'application', 'call for', 'proposal',
            'position', 'vacancy', 'career', 'job', 'recruitment', 'hiring',
            'graduate', 'undergraduate', 'phd', 'master', 'postgraduate',
            'research', 'innovation', 'leadership', 'mentorship', 'exchange'
        ]
        
        text = (title + ' ' + description).lower()
        
        for keyword in opportunity_keywords:
            if keyword in text:
                return True
        
        # If it has application-related patterns
        if 'apply' in text or 'application' in text:
            return True
        
        # If it has date patterns (deadlines)
        if re.search(r'\b(deadline|due date|closing date)\b', text, re.I):
            return True
        
        return False
    
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
