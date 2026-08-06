"""
Africa Opportunity Finder - Production Scraper Module
Enterprise-grade web scraping with automatic source discovery and verification
"""

import logging
import sqlite3
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin
import time
import random

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AfricaScraper')

class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self, db_path: str = "africa_opportunities.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT,
                country TEXT,
                is_active INTEGER DEFAULT 1,
                last_scrape TEXT,
                opportunities_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(name, url)
            )
        """)
        
        # Opportunities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                organization TEXT,
                category TEXT,
                country TEXT,
                region TEXT,
                deadline TEXT,
                description TEXT,
                official_url TEXT UNIQUE,
                source_id INTEGER,
                source_name TEXT,
                verified INTEGER DEFAULT 0,
                match_score REAL DEFAULT 0,
                scrape_timestamp TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_official_url ON opportunities(official_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_id ON opportunities(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON opportunities(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_country ON opportunities(country)")
        
        # Scrape history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                total_found INTEGER,
                total_verified INTEGER,
                total_errors INTEGER,
                timestamp TEXT,
                duration_seconds REAL,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
        """)
        
        conn.commit()
        
        # Add default sources if empty
        cursor.execute("SELECT COUNT(*) FROM sources")
        if cursor.fetchone()[0] == 0:
            self.add_default_sources()
        
        conn.close()
    
    def add_default_sources(self):
        """Add default sources with regional focus"""
        default_sources = [
            # Major International Organizations
            ('African Union', 'https://www.au.int/en/youth', 'Government', 'Africa'),
            ('United Nations', 'https://careers.un.org', 'Government', 'Global'),
            ('UNICEF', 'https://www.unicef.org/careers', 'Internship', 'Global'),
            ('UNDP', 'https://www.undp.org/careers', 'Employment', 'Global'),
            ('World Bank', 'https://www.worldbank.org/en/about/careers', 'Employment', 'Global'),
            ('African Development Bank', 'https://www.afdb.org/en/careers', 'Employment', 'Africa'),
            
            # Foundations
            ('Mastercard Foundation', 'https://mastercardfoundation.org/opportunities', 'Funding', 'Africa'),
            ('Tony Elumelu Foundation', 'https://www.tonyelumelufoundation.org', 'Entrepreneurship', 'Africa'),
            
            # Corporate
            ('Google Careers', 'https://careers.google.com', 'Employment', 'Global'),
            ('Microsoft Careers', 'https://careers.microsoft.com', 'Employment', 'Global'),
            
            # Regional African Organizations
            ('East African Community', 'https://www.eac.int/opportunities', 'Government', 'East Africa'),
            
            # Youth Focused
            ('Youth Hub Africa', 'https://youthhubafrica.org', 'Youth', 'Africa'),
            
            # Cultural/Educational
            ('British Council', 'https://www.britishcouncil.org/opportunities', 'Education', 'Africa'),
            ('Commonwealth', 'https://thecommonwealth.org/opportunities', 'Government', 'Commonwealth'),
            
            # Job Portals
            ('Brighter Monday', 'https://www.brightermonday.co.ke', 'Employment', 'East Africa'),
            ('Jobberman', 'https://www.jobberman.com', 'Employment', 'Nigeria'),
            ('MyJobMag', 'https://www.myjobmag.com', 'Employment', 'Nigeria'),
            
            # Development Organizations
            ('USAID', 'https://www.usaid.gov/careers', 'Development', 'Global'),
            ('GIZ', 'https://www.giz.de/en/aboutgiz/careers.html', 'Development', 'Global'),
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        for name, url, category, country in default_sources:
            cursor.execute("""
                INSERT OR IGNORE INTO sources (name, url, category, country, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (name, url, category, country, now, now))
        
        conn.commit()
        conn.close()
        logger.info(f"Added {len(default_sources)} default sources")
    
    def add_source(self, name: str, url: str, category: str = 'Other', country: str = 'Africa') -> bool:
        """Add a new source to database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT OR IGNORE INTO sources (name, url, category, country, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (name.strip(), url.strip(), category.strip(), country.strip(), now, now))
            
            conn.commit()
            conn.close()
            logger.info(f"Added source: {name}")
            return True
        except Exception as e:
            logger.error(f"Error adding source: {str(e)}")
            return False
    
    def get_active_sources(self) -> List[Dict]:
        """Get all active sources"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, url, category, country, last_scrape, opportunities_count
            FROM sources
            WHERE is_active = 1
            ORDER BY name
        """)
        
        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sources
    
    def get_all_sources(self) -> List[Dict]:
        """Get all sources"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, url, category, country, is_active, last_scrape, opportunities_count, error_count
            FROM sources
            ORDER BY name
        """)
        
        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sources
    
    def update_source_stats(self, source_id: int, count: int, errors: int = 0):
        """Update source statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE sources 
            SET last_scrape = ?, opportunities_count = ?, error_count = ?, updated_at = ?
            WHERE id = ?
        """, (now, count, errors, now, source_id))
        
        conn.commit()
        conn.close()
    
    def save_opportunity(self, opportunity: Dict) -> bool:
        """Save a single opportunity, skip duplicates"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # Check for duplicate
            cursor.execute("SELECT id FROM opportunities WHERE official_url = ?", 
                         (opportunity.get('official_url', ''),))
            if cursor.fetchone():
                return False
            
            cursor.execute("""
                INSERT INTO opportunities (
                    title, organization, category, country, region, deadline,
                    description, official_url, source_id, source_name,
                    verified, scrape_timestamp, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opportunity.get('title', '')[:500],
                opportunity.get('organization', '')[:200],
                opportunity.get('category', 'Other')[:100],
                opportunity.get('country', 'Africa')[:100],
                opportunity.get('region', '')[:100],
                opportunity.get('deadline', '')[:50],
                opportunity.get('description', '')[:2000],
                opportunity.get('official_url', '')[:500],
                opportunity.get('source_id'),
                opportunity.get('source_name', ''),
                1 if opportunity.get('verified', False) else 0,
                opportunity.get('scrape_timestamp', now),
                now,
                now
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving opportunity: {str(e)}")
            return False
    
    def save_opportunities_batch(self, opportunities: List[Dict]) -> int:
        """Save multiple opportunities"""
        saved = 0
        for opp in opportunities:
            if self.save_opportunity(opp):
                saved += 1
        return saved
    
    def get_opportunities(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get opportunities with pagination"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, organization, category, country, region, deadline,
                   description, official_url, source_name, verified, match_score,
                   scrape_timestamp, created_at
            FROM opportunities
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        opportunities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return opportunities
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total opportunities
        cursor.execute("SELECT COUNT(*) FROM opportunities")
        stats['total_opportunities'] = cursor.fetchone()[0]
        
        # Verified opportunities
        cursor.execute("SELECT COUNT(*) FROM opportunities WHERE verified = 1")
        stats['verified'] = cursor.fetchone()[0]
        
        # Active sources
        cursor.execute("SELECT COUNT(*) FROM sources WHERE is_active = 1")
        stats['active_sources'] = cursor.fetchone()[0]
        
        # Categories
        cursor.execute("SELECT category, COUNT(*) FROM opportunities GROUP BY category ORDER BY COUNT(*) DESC")
        stats['categories'] = [dict(row) for row in cursor.fetchall()]
        
        # Countries
        cursor.execute("SELECT country, COUNT(*) FROM opportunities WHERE country IS NOT NULL AND country != '' GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10")
        stats['top_countries'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return stats
    
    def toggle_source(self, source_id: int) -> bool:
        """Toggle source active status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_active FROM sources WHERE id = ?", (source_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        
        new_status = 0 if row[0] else 1
        cursor.execute("UPDATE sources SET is_active = ? WHERE id = ?", (new_status, source_id))
        
        conn.commit()
        conn.close()
        return True
    
    def delete_source(self, source_id: int) -> bool:
        """Delete a source"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        
        conn.commit()
        conn.close()
        return True


class OpportunityScraper:
    """Core scraper with regional focus and intelligent extraction"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.timeout = 30
        
        # Keywords that indicate a real opportunity
        self.opportunity_keywords = [
            'apply', 'opportunity', 'job', 'career', 'vacancy', 'position',
            'internship', 'fellowship', 'scholarship', 'trainee', 'apprenticeship',
            'graduate', 'entry-level', 'program', 'volunteer', 'recruitment',
            'hiring', 'opening', 'posting', 'application', 'candidate'
        ]
        
        # Words that indicate navigation or non-opportunity content
        self.navigation_keywords = [
            'login', 'sign in', 'register', 'about', 'contact', 'faq', 'privacy',
            'terms', 'cookie', 'policy', 'careers|', 'frequently asked', 'view all',
            'english', 'francais', 'espanol', 'home', 'menu', 'footer', 'copyright'
        ]
        
        # African countries for detection
        self.african_countries = [
            'Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi',
            'Cameroon', 'Cabo Verde', 'Central African Republic', 'Chad',
            'Comoros', 'Congo', 'Djibouti', 'Egypt', 'Equatorial Guinea',
            'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana',
            'Guinea', 'Guinea-Bissau', 'Ivory Coast', 'Kenya', 'Lesotho',
            'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania',
            'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria',
            'Rwanda', 'Sao Tome and Principe', 'Senegal', 'Seychelles',
            'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan', 'Sudan',
            'Tanzania', 'Togo', 'Tunisia', 'Uganda', 'Zambia', 'Zimbabwe'
        ]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_url(self, url: str) -> Optional[requests.Response]:
        """Fetch URL with retry logic"""
        try:
            time.sleep(random.uniform(0.5, 1.5))
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def scrape_source(self, source: Dict) -> Tuple[List[Dict], int]:
        """Scrape a single source"""
        opportunities = []
        errors = 0
        
        try:
            logger.info(f"Scraping: {source['name']} ({source['url']})")
            response = self.fetch_url(source['url'])
            
            if not response:
                errors += 1
                return opportunities, errors
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract opportunities from the page
            opportunities = self._extract_opportunities(soup, source)
            
            # Remove navigation and irrelevant items
            opportunities = self._filter_opportunities(opportunities, source)
            
            # Add source information
            for opp in opportunities:
                opp['source_id'] = source['id']
                opp['source_name'] = source['name']
                opp['scrape_timestamp'] = datetime.now().isoformat()
            
            logger.info(f"Found {len(opportunities)} opportunities from {source['name']}")
            return opportunities, errors
            
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {str(e)}")
            errors += 1
            return opportunities, errors
    
    def _extract_opportunities(self, soup: BeautifulSoup, source: Dict) -> List[Dict]:
        """Extract opportunities from the page"""
        opportunities = []
        
        # Find all links on the page
        links = soup.find_all('a', href=True)
        
        # Look for links that might be opportunities
        for link in links:
            try:
                text = link.get_text().strip()
                href = link.get('href', '')
                
                if not text or not href:
                    continue
                
                # Skip if text or href contains navigation keywords
                text_lower = text.lower()
                href_lower = href.lower()
                
                is_navigation = any(kw in text_lower for kw in self.navigation_keywords) or \
                               any(kw in href_lower for kw in self.navigation_keywords)
                
                if is_navigation:
                    continue
                
                # Skip very short text (likely icons or buttons)
                if len(text) < 8:
                    continue
                
                # Check if this looks like an opportunity
                is_opportunity = any(kw in text_lower for kw in self.opportunity_keywords) or \
                                any(kw in href_lower for kw in self.opportunity_keywords)
                
                if not is_opportunity:
                    continue
                
                # Build absolute URL
                if href.startswith('/'):
                    href = urljoin(source['url'], href)
                elif not href.startswith('http'):
                    href = urljoin(source['url'], '/' + href)
                
                # Skip if URL is just the base domain or a fragment
                if href == source['url'] or href.endswith('#') or 'javascript:' in href:
                    continue
                
                # Get description from parent
                description = ""
                parent = link.parent
                if parent:
                    # Try to get description from parent elements
                    desc_elem = parent.find(['p', 'div'], class_=['description', 'summary', 'body'])
                    if desc_elem:
                        description = desc_elem.get_text().strip()
                    else:
                        # Get surrounding text
                        parent_text = parent.get_text().strip()
                        if len(parent_text) > len(text) + 10:
                            description = parent_text.replace(text, '').strip()
                
                # Limit description
                if description:
                    description = description[:500]
                
                opportunity = {
                    'title': text[:200],
                    'official_url': href,
                    'description': description,
                    'organization': source['name'],
                    'category': self._detect_category(text + description),
                    'country': self._detect_country(text + description + source.get('country', '')),
                    'region': self._detect_region(text + description + source.get('country', '')),
                    'deadline': self._extract_deadline(text + description)
                }
                
                opportunities.append(opportunity)
                    
            except Exception as e:
                logger.debug(f"Error extracting opportunity: {str(e)}")
                continue
        
        # Remove duplicates by URL
        seen_urls = set()
        unique_opportunities = []
        for opp in opportunities:
            url = opp.get('official_url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_opportunities.append(opp)
        
        return unique_opportunities
    
    def _filter_opportunities(self, opportunities: List[Dict], source: Dict) -> List[Dict]:
        """Filter out irrelevant opportunities"""
        filtered = []
        
        for opp in opportunities:
            # Skip if title is too short
            if len(opp.get('title', '')) < 5:
                continue
            
            # Skip if title is mostly numbers or special characters
            title = opp.get('title', '')
            if re.match(r'^[\d\s\W]+$', title):
                continue
            
            # Skip if URL is a login or registration page
            url = opp.get('official_url', '').lower()
            if 'login' in url or 'signin' in url or 'register' in url:
                continue
            
            # Skip if URL is a file download (PDF, DOC, etc.)
            if url.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
                continue
            
            # Skip if description contains only navigation text
            desc = opp.get('description', '').lower()
            if desc and len(desc) < 20:
                # Check if description is just a repeat of title
                if desc.strip() == opp.get('title', '').lower().strip():
                    continue
            
            filtered.append(opp)
        
        # Limit to reasonable number
        return filtered[:50]
    
    def _detect_category(self, text: str) -> str:
        """Detect opportunity category from text"""
        text_lower = text.lower()
        
        categories = {
            'Internship': ['intern', 'internship', 'trainee', 'training'],
            'Scholarship': ['scholarship', 'scholar', 'research', 'academic'],
            'Fellowship': ['fellow', 'fellowship', 'leadership'],
            'Employment': ['job', 'career', 'employment', 'position', 'vacancy', 'hiring'],
            'Volunteer': ['volunteer', 'voluntary', 'community'],
            'Grant': ['grant', 'funding', 'research grant'],
            'Entrepreneurship': ['entrepreneur', 'startup', 'business'],
            'Youth': ['youth', 'young', 'graduate']
        }
        
        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category
        
        return 'Other'
    
    def _detect_country(self, text: str) -> str:
        """Detect country from text"""
        if not text:
            return 'Africa'
        
        text_lower = text.lower()
        for country in self.african_countries:
            if country.lower() in text_lower:
                return country
        
        return 'Africa'
    
    def _detect_region(self, text: str) -> str:
        """Detect African region from text"""
        if not text:
            return ''
        
        text_lower = text.lower()
        
        regions = {
            'East Africa': ['kenya', 'tanzania', 'uganda', 'rwanda', 'ethiopia', 'somalia'],
            'West Africa': ['nigeria', 'ghana', 'ivory coast', 'senegal', 'mali'],
            'Southern Africa': ['south africa', 'botswana', 'zambia', 'zimbabwe'],
            'North Africa': ['egypt', 'algeria', 'morocco', 'tunisia']
        }
        
        for region, countries in regions.items():
            if any(country in text_lower for country in countries):
                return region
        
        if 'africa' in text_lower:
            return 'Africa'
        
        return ''
    
    def _extract_deadline(self, text: str) -> str:
        """Extract deadline from text"""
        if not text:
            return ''
        
        # Common deadline patterns
        patterns = [
            r'deadline[:\s]+([^.]*?)(?:\.|$)',
            r'closing date[:\s]+([^.]*?)(?:\.|$)',
            r'apply by[:\s]+([^.]*?)(?:\.|$)',
            r'application deadline[:\s]+([^.]*?)(?:\.|$)',
            r'due[:\s]+([^.]*?)(?:\.|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                deadline = match.group(1).strip()
                # Try to extract date
                date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', deadline)
                if date_match:
                    return date_match.group(0)
                return deadline[:50]
        
        return ''
    
    def scrape_all_sources(self) -> Dict[str, Any]:
        """Scrape all active sources"""
        sources = self.db_manager.get_active_sources()
        
        if not sources:
            logger.warning("No active sources found")
            return {'total_opportunities': 0, 'total_errors': 0, 'sources': []}
        
        logger.info(f"Starting scrape of {len(sources)} sources")
        total_opportunities = 0
        total_errors = 0
        results = []
        
        # Use thread pool for parallel scraping
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_source = {
                executor.submit(self.scrape_source, source): source
                for source in sources
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    opportunities, errors = future.result(timeout=60)
                    
                    # Save opportunities
                    if opportunities:
                        saved = self.db_manager.save_opportunities_batch(opportunities)
                        total_opportunities += saved
                        
                        # Update source stats
                        self.db_manager.update_source_stats(source['id'], saved, errors)
                        
                        results.append({
                            'source': source['name'],
                            'found': len(opportunities),
                            'saved': saved,
                            'errors': errors
                        })
                    else:
                        self.db_manager.update_source_stats(source['id'], 0, errors)
                        results.append({
                            'source': source['name'],
                            'found': 0,
                            'saved': 0,
                            'errors': errors
                        })
                    
                    total_errors += errors
                    
                except Exception as e:
                    logger.error(f"Error processing {source['name']}: {str(e)}")
                    total_errors += 1
                    results.append({
                        'source': source['name'],
                        'found': 0,
                        'saved': 0,
                        'errors': 1,
                        'error': str(e)
                    })
        
        logger.info(f"Scrape complete: {total_opportunities} opportunities from {len(sources)} sources")
        
        return {
            'total_opportunities': total_opportunities,
            'total_errors': total_errors,
            'sources': results
        }
    
    def scrape_single_source(self, source_id: int) -> Dict[str, Any]:
        """Scrape a single source by ID"""
        sources = self.db_manager.get_all_sources()
        source = next((s for s in sources if s['id'] == source_id), None)
        
        if not source:
            return {'error': 'Source not found'}
        
        if not source['is_active']:
            return {'error': 'Source is inactive'}
        
        opportunities, errors = self.scrape_source(source)
        
        if opportunities:
            saved = self.db_manager.save_opportunities_batch(opportunities)
            self.db_manager.update_source_stats(source['id'], saved, errors)
            
            return {
                'source': source['name'],
                'found': len(opportunities),
                'saved': saved,
                'errors': errors
            }
        
        return {
            'source': source['name'],
            'found': 0,
            'saved': 0,
            'errors': errors
        }
