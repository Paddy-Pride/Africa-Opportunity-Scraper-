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
            ('African Union', 'https://www.au.int/en/youth', 'Government', 'Africa'),
            ('United Nations', 'https://careers.un.org', 'Government', 'Global'),
            ('UNICEF', 'https://www.unicef.org/careers', 'Internship', 'Global'),
            ('UNDP', 'https://www.undp.org/careers', 'Employment', 'Global'),
            ('World Bank', 'https://www.worldbank.org/en/about/careers', 'Employment', 'Global'),
            ('African Development Bank', 'https://www.afdb.org/en/careers', 'Employment', 'Africa'),
            ('Mastercard Foundation', 'https://mastercardfoundation.org/opportunities', 'Funding', 'Africa'),
            ('Google Careers', 'https://careers.google.com', 'Employment', 'Global'),
            ('Microsoft Careers', 'https://careers.microsoft.com', 'Employment', 'Global'),
            ('British Council', 'https://www.britishcouncil.org/opportunities', 'Education', 'Africa'),
            ('Commonwealth', 'https://thecommonwealth.org/opportunities', 'Government', 'Commonwealth'),
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
                opportunity.get('description', '')[:1000],
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
            WHERE title IS NOT NULL AND title != ''
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
        
        cursor.execute("SELECT COUNT(*) FROM opportunities")
        stats['total_opportunities'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM opportunities WHERE verified = 1")
        stats['verified'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sources WHERE is_active = 1")
        stats['active_sources'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT category, COUNT(*) FROM opportunities GROUP BY category ORDER BY COUNT(*) DESC")
        stats['categories'] = [dict(row) for row in cursor.fetchall()]
        
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
        })
        self.timeout = 30
        
        # Keywords that indicate a real opportunity
        self.real_opportunity_patterns = [
            r'apply\s+now', r'apply\s+today', r'submit\s+application',
            r'job\s+opening', r'job\s+vacancy', r'career\s+opportunity',
            r'internship', r'fellowship', r'scholarship',
            r'graduate\s+program', r'trainee', r'apprentice',
            r'entry\s+level', r'junior\s+position', r'hiring',
            r'recruitment', r'position\s+available', r'we\s+are\s+hiring'
        ]
        
        # Skip patterns - content to avoid
        self.skip_patterns = [
            r'login', r'sign\s+in', r'register', r'about\s+us',
            r'contact\s+us', r'privacy\s+policy', r'terms\s+of\s+use',
            r'cookie\s+policy', r'faq', r'beneficiaries', r'alumni',
            r'copyright', r'all\s+rights\s+reserved', r'view\s+all',
            r'read\s+more', r'learn\s+more', r'see\s+more'
        ]
    
    def _strip_html_tags(self, text: str) -> str:
        """Remove all HTML tags from text"""
        if not text:
            return ''
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()
    
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
            
            # Clean and validate opportunities
            cleaned_opportunities = []
            for opp in opportunities:
                # Strip all HTML tags from title and description
                if 'title' in opp:
                    opp['title'] = self._strip_html_tags(opp['title'])
                if 'description' in opp:
                    opp['description'] = self._strip_html_tags(opp['description'])
                
                if self._validate_opportunity(opp):
                    opp['source_id'] = source['id']
                    opp['source_name'] = source['name']
                    opp['scrape_timestamp'] = datetime.now().isoformat()
                    cleaned_opportunities.append(opp)
            
            logger.info(f"Found {len(cleaned_opportunities)} opportunities from {source['name']}")
            return cleaned_opportunities, errors
            
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {str(e)}")
            errors += 1
            return opportunities, errors
    
    def _extract_opportunities(self, soup: BeautifulSoup, source: Dict) -> List[Dict]:
        """Extract opportunities from the page"""
        opportunities = []
        seen_urls = set()
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            try:
                # Get clean text without HTML tags
                text = link.get_text(strip=True)
                if not text:
                    continue
                
                href = link.get('href', '')
                if not href:
                    continue
                
                # Skip very short text
                if len(text) < 10:
                    continue
                
                # Check if this is a real opportunity
                if not self._is_opportunity_link(text, href):
                    continue
                
                # Build absolute URL
                full_url = self._make_absolute_url(href, source['url'])
                if not full_url:
                    continue
                
                # Skip if URL looks like navigation or file
                if self._should_skip_url(full_url):
                    continue
                
                # Skip duplicates
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                # Clean title - remove HTML tags
                title = self._clean_text(text)
                if not title or len(title) < 8:
                    continue
                
                # Get description - clean text without HTML
                description = self._get_description(link, soup)
                if description:
                    description = self._strip_html_tags(description)[:500]
                
                # Get deadline
                deadline = self._extract_deadline(text + description)
                
                opportunity = {
                    'title': title[:200],
                    'official_url': full_url,
                    'description': description,
                    'organization': source['name'],
                    'category': self._detect_category(text + description),
                    'country': self._detect_country(text + description + source.get('country', '')),
                    'region': self._detect_region(text + description + source.get('country', '')),
                    'deadline': deadline[:50] if deadline else ''
                }
                
                opportunities.append(opportunity)
                    
            except Exception as e:
                logger.debug(f"Error processing link: {str(e)}")
                continue
        
        # Remove duplicates by title similarity
        seen_titles = set()
        unique_opportunities = []
        for opp in opportunities:
            title_lower = opp.get('title', '').lower()
            if title_lower and title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_opportunities.append(opp)
        
        return unique_opportunities[:20]
    
    def _is_opportunity_link(self, text: str, href: str) -> bool:
        """Check if link text or href indicates a real opportunity"""
        text_lower = text.lower()
        href_lower = href.lower()
        
        # Check against real opportunity patterns
        for pattern in self.real_opportunity_patterns:
            if re.search(pattern, text_lower) or re.search(pattern, href_lower):
                # Make sure it's not a skip pattern
                for skip_pattern in self.skip_patterns:
                    if re.search(skip_pattern, text_lower) or re.search(skip_pattern, href_lower):
                        return False
                return True
        
        return False
    
    def _should_skip_url(self, url: str) -> bool:
        """Check if URL should be skipped"""
        url_lower = url.lower()
        
        # Skip file extensions
        if re.search(r'\.(pdf|doc|docx|xls|xlsx|jpg|png|gif|mp4|mp3)$', url_lower):
            return True
        
        # Skip known navigation paths
        skip_paths = ['login', 'signin', 'register', 'faq', 'privacy', 'terms', 
                     'about', 'contact', 'careers?', 'joblist', 'viewall']
        for path in skip_paths:
            if path in url_lower:
                return True
        
        return False
    
    def _make_absolute_url(self, href: str, base_url: str) -> Optional[str]:
        """Convert relative URL to absolute"""
        if not href:
            return None
        
        href = href.strip()
        
        # Skip javascript and mailto
        if href.startswith('javascript:') or href.startswith('mailto:'):
            return None
        
        # Skip anchor links
        if href.startswith('#'):
            return None
        
        try:
            if href.startswith('/'):
                parsed = urlparse(base_url)
                return f"{parsed.scheme}://{parsed.netloc}{href}"
            elif not href.startswith('http'):
                return urljoin(base_url, href)
            else:
                return href
        except Exception:
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text - strip all HTML tags"""
        if not text:
            return ''
        
        # First strip any HTML tags
        text = self._strip_html_tags(text)
        
        # Remove common prefixes/suffixes
        prefixes = ['Apply Now', 'Apply Today', 'Click Here', 'Read More', 'View More', 'Learn More']
        for prefix in prefixes:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
        
        return text
    
    def _get_description(self, link, soup: BeautifulSoup) -> str:
        """Extract description from surrounding context - clean text only"""
        description = ""
        
        # Check parent
        parent = link.parent
        if parent:
            # Check next sibling
            sibling = parent.find_next_sibling(['p', 'div'])
            if sibling:
                desc_text = sibling.get_text(strip=True)
                if len(desc_text) > 20:
                    description = desc_text
            
            # Check parent text without link
            if not description:
                parent_text = parent.get_text(strip=True)
                link_text = link.get_text(strip=True)
                if parent_text and link_text:
                    desc_text = parent_text.replace(link_text, '').strip()
                    if len(desc_text) > 20:
                        description = desc_text
        
        # Check previous paragraph
        if not description:
            para = link.find_previous('p')
            if para:
                desc_text = para.get_text(strip=True)
                if len(desc_text) > 30:
                    description = desc_text
        
        # Strip any remaining HTML tags
        if description:
            description = self._strip_html_tags(description)
        
        return description
    
    def _validate_opportunity(self, opportunity: Dict) -> bool:
        """Validate opportunity data"""
        title = opportunity.get('title', '')
        url = opportunity.get('official_url', '')
        
        # Must have title and URL
        if not title or not url:
            return False
        
        # Title must be reasonable length
        if len(title) < 8 or len(title) > 200:
            return False
        
        # Must not contain HTML tags
        if '<' in title or '>' in title:
            return False
        
        # Must not be generic navigation
        skip_phrases = ['home', 'about', 'contact', 'careers', 'jobs', 'apply']
        if any(phrase in title.lower() for phrase in skip_phrases) and len(title) < 20:
            return False
        
        # URL must be valid
        if not url.startswith(('http://', 'https://')):
            return False
        
        return True
    
    def _detect_category(self, text: str) -> str:
        """Detect opportunity category"""
        text_lower = text.lower()
        
        categories = {
            'Internship': ['intern', 'internship', 'trainee'],
            'Scholarship': ['scholarship', 'scholar', 'academic'],
            'Fellowship': ['fellow', 'fellowship'],
            'Employment': ['job', 'career', 'employment', 'position', 'vacancy', 'hiring'],
            'Volunteer': ['volunteer', 'voluntary'],
            'Grant': ['grant', 'funding'],
            'Entrepreneurship': ['entrepreneur', 'startup', 'business']
        }
        
        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category
        
        return 'Other'
    
    def _detect_country(self, text: str) -> str:
        """Detect country from text"""
        if not text:
            return 'Africa'
        
        african_countries = [
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
        
        text_lower = text.lower()
        for country in african_countries:
            if country.lower() in text_lower:
                return country
        
        return 'Africa'
    
    def _detect_region(self, text: str) -> str:
        """Detect African region"""
        if not text:
            return ''
        
        text_lower = text.lower()
        
        regions = {
            'East Africa': ['kenya', 'tanzania', 'uganda', 'rwanda', 'ethiopia'],
            'West Africa': ['nigeria', 'ghana', 'ivory coast', 'senegal', 'mali'],
            'Southern Africa': ['south africa', 'botswana', 'zambia', 'zimbabwe'],
            'North Africa': ['egypt', 'algeria', 'morocco', 'tunisia']
        }
        
        for region, countries in regions.items():
            if any(country in text_lower for country in countries):
                return region
        
        return ''
    
    def _extract_deadline(self, text: str) -> str:
        """Extract deadline from text"""
        if not text:
            return ''
        
        # Strip HTML tags first
        text = self._strip_html_tags(text)
        
        patterns = [
            r'deadline[:\s]+([^.]*?)(?:\.|$)',
            r'closing date[:\s]+([^.]*?)(?:\.|$)',
            r'apply by[:\s]+([^.]*?)(?:\.|$)',
            r'application deadline[:\s]+([^.]*?)(?:\.|$)'
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
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_source = {
                executor.submit(self.scrape_source, source): source
                for source in sources
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    opportunities, errors = future.result(timeout=60)
                    
                    if opportunities:
                        saved = self.db_manager.save_opportunities_batch(opportunities)
                        total_opportunities += saved
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
