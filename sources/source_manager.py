"""
Source Manager - Manages source database operations
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class SourceManager:
    """Manager for source database operations"""
    
    def __init__(self, db_path: str = "config/sources.db"):
        """
        Initialize the source manager
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                category TEXT,
                country TEXT,
                enabled INTEGER DEFAULT 1,
                last_scraped TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scrape_count INTEGER DEFAULT 0,
                last_error TEXT,
                custom_config TEXT
            )
        """)
        
        # Create opportunities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                title TEXT NOT NULL,
                organization TEXT,
                category TEXT,
                country TEXT,
                deadline TEXT,
                description TEXT,
                official_url TEXT,
                verified INTEGER DEFAULT 0,
                verification_details TEXT,
                match_score REAL,
                date_scraped TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
        """)
        
        # Create scrape history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                opportunities_found INTEGER,
                errors TEXT,
                duration_seconds REAL,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Initialize with default sources if empty
        self._init_default_sources()
    
    def _init_default_sources(self) -> None:
        """Initialize default sources"""
        default_sources = [
            {
                'name': 'African Union',
                'url': 'https://www.africanunion.org/opportunities',
                'category': 'Grants'
            },
            {
                'name': 'United Nations',
                'url': 'https://www.un.org/opportunities',
                'category': 'Jobs'
            },
            {
                'name': 'World Bank',
                'url': 'https://www.worldbank.org/opportunities',
                'category': 'Jobs'
            },
            {
                'name': 'African Development Bank',
                'url': 'https://www.afdb.org/opportunities',
                'category': 'Jobs'
            },
            {
                'name': 'Mastercard Foundation',
                'url': 'https://www.mastercardfdn.org/opportunities',
                'category': 'Grants'
            },
            {
                'name': 'Google',
                'url': 'https://careers.google.com',
                'category': 'Jobs'
            },
            {
                'name': 'Microsoft',
                'url': 'https://careers.microsoft.com',
                'category': 'Jobs'
            },
            {
                'name': 'Youth Hub Africa',
                'url': 'https://youthhubafrica.org/opportunities',
                'category': 'Education'
            },
            {
                'name': 'Opportunities For Africa',
                'url': 'https://opportunitiesforafrica.com',
                'category': 'Education'
            },
            {
                'name': 'UNICEF',
                'url': 'https://www.unicef.org/careers',
                'category': 'Jobs'
            },
            {
                'name': 'UNESCO',
                'url': 'https://www.unesco.org/careers',
                'category': 'Jobs'
            },
            {
                'name': 'UNDP',
                'url': 'https://www.undp.org/careers',
                'category': 'Jobs'
            },
            {
                'name': 'British Council',
                'url': 'https://www.britishcouncil.org/opportunities',
                'category': 'Education'
            },
            {
                'name': 'Commonwealth',
                'url': 'https://thecommonwealth.org/opportunities',
                'category': 'Grants'
            }
        ]
        
        # Add default sources if table is empty
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sources")
        count = cursor.fetchone()[0]
        
        if count == 0:
            for source in default_sources:
                cursor.execute("""
                    INSERT INTO sources (name, url, category, enabled)
                    VALUES (?, ?, ?, 1)
                """, (source['name'], source['url'], source['category']))
            
            conn.commit()
            logger.info(f"Initialized {len(default_sources)} default sources")
        
        conn.close()
    
    def add_source(self, source_data: Dict[str, Any]) -> Optional[int]:
        """
        Add a new source
        
        Args:
            source_data: Source data dictionary
            
        Returns:
            Source ID if successful, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if source already exists
            cursor.execute("SELECT id FROM sources WHERE url = ?", (source_data.get('url'),))
            existing = cursor.fetchone()
            
            if existing:
                logger.warning(f"Source already exists: {source_data.get('url')}")
                return None
            
            cursor.execute("""
                INSERT INTO sources (name, url, category, country, enabled, custom_config)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                source_data.get('name'),
                source_data.get('url'),
                source_data.get('category', 'General'),
                source_data.get('country', 'Africa'),
                int(source_data.get('enabled', True)),
                json.dumps(source_data.get('custom_config', {}))
            ))
            
            conn.commit()
            source_id = cursor.lastrowid
            conn.close()
            
            logger.info(f"Added source: {source_data.get('name')}")
            return source_id
            
        except Exception as e:
            logger.error(f"Error adding source: {str(e)}")
            return None
    
    def get_all_sources(self) -> List[Dict[str, Any]]:
        """
        Get all sources
        
        Returns:
            List of source dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sources ORDER BY name
        """)
        
        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return sources
    
    def get_enabled_sources(self) -> List[Dict[str, Any]]:
        """
        Get enabled sources
        
        Returns:
            List of enabled source dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sources WHERE enabled = 1 ORDER BY name
        """)
        
        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return sources
    
    def update_source(self, source_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update a source
        
        Args:
            source_id: Source ID
            updates: Updates to apply
            
        Returns:
            Boolean indicating success
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [source_id]
            
            cursor.execute(f"""
                UPDATE sources 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated source {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating source: {str(e)}")
            return False
    
    def delete_source(self, source_id: int) -> bool:
        """
        Delete a source
        
        Args:
            source_id: Source ID
            
        Returns:
            Boolean indicating success
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted source {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting source: {str(e)}")
            return False
    
    def source_exists(self, url: str) -> bool:
        """
        Check if source exists
        
        Args:
            url: Source URL
            
        Returns:
            Boolean indicating existence
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM sources WHERE url = ?", (url,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def update_source_scrape_time(self, source_id: int) -> bool:
        """
        Update source's last scraped time
        
        Args:
            source_id: Source ID
            
        Returns:
            Boolean indicating success
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sources 
                SET last_scraped = CURRENT_TIMESTAMP, scrape_count = scrape_count + 1
                WHERE id = ?
            """, (source_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating scrape time: {str(e)}")
            return False
    
    def log_scrape_history(self, source_id: int, opportunities_found: int, 
                           errors: Optional[str] = None, duration: float = 0) -> bool:
        """
        Log scrape history
        
        Args:
            source_id: Source ID
            opportunities_found: Number of opportunities found
            errors: Error messages
            duration: Scrape duration in seconds
            
        Returns:
            Boolean indicating success
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scrape_history (source_id, opportunities_found, errors, duration_seconds)
                VALUES (?, ?, ?, ?)
            """, (source_id, opportunities_found, errors, duration))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging scrape history: {str(e)}")
            return False
    
    def save_scrape_results(self, opportunities: List[Dict[str, Any]]) -> bool:
        """
        Save scraped opportunities to database
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            Boolean indicating success
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for opp in opportunities:
                # Get source ID
                source_name = opp.get('source', 'Unknown')
                cursor.execute("SELECT id FROM sources WHERE name = ?", (source_name,))
                source_row = cursor.fetchone()
                source_id = source_row[0] if source_row else None
                
                # Check if opportunity already exists
                cursor.execute("""
                    SELECT id FROM opportunities 
                    WHERE official_url = ? AND title = ?
                """, (opp.get('official_url', ''), opp.get('title', '')))
                
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO opportunities (
                            source_id, title, organization, category, country,
                            deadline, description, official_url, verified,
                            verification_details, date_scraped
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        source_id,
                        opp.get('title', ''),
                        opp.get('organization', ''),
                        opp.get('category', 'General'),
                        opp.get('country', 'Africa'),
                        opp.get('deadline', 'N/A'),
                        opp.get('description', ''),
                        opp.get('official_url', ''),
                        int(opp.get('verified', False)),
                        json.dumps(opp.get('verification_details', [])),
                        opp.get('date_scraped', datetime.now().isoformat())
                    ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(opportunities)} opportunities")
            return True
            
        except Exception as e:
            logger.error(f"Error saving scrape results: {str(e)}")
            return False
    
    def get_verified_opportunities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get verified opportunities
        
        Args:
            limit: Maximum number of opportunities
            
        Returns:
            List of verified opportunity dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM opportunities 
            WHERE verified = 1
            ORDER BY date_scraped DESC
            LIMIT ?
        """, (limit,))
        
        opportunities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return opportunities
    
    def get_all_opportunities(self) -> List[Dict[str, Any]]:
        """
        Get all opportunities
        
        Returns:
            List of opportunity dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM opportunities ORDER BY date_scraped DESC
        """)
        
        opportunities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return opportunities
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary of statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sources")
        total_sources = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM opportunities")
        total_opportunities = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM opportunities WHERE verified = 1")
        verified_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_sources': total_sources,
            'total_opportunities': total_opportunities,
            'verified_count': verified_count
        }
    
    def count_opportunities_by_source(self, source_id: int) -> int:
        """
        Count opportunities by source
        
        Args:
            source_id: Source ID
            
        Returns:
            Number of opportunities
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM opportunities WHERE source_id = ?
        """, (source_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def filter_opportunities(self, opportunities: List[Dict[str, Any]], 
                            search_term: str) -> List[Dict[str, Any]]:
        """
        Filter opportunities by search term
        
        Args:
            opportunities: List of opportunities
            search_term: Search term
            
        Returns:
            Filtered list
        """
        if not search_term:
            return opportunities
        
        search_term = search_term.lower()
        filtered = []
        
        for opp in opportunities:
            if (search_term in opp.get('title', '').lower() or
                search_term in opp.get('organization', '').lower() or
                search_term in opp.get('category', '').lower() or
                search_term in opp.get('country', '').lower() or
                search_term in opp.get('description', '').lower()):
                filtered.append(opp)
        
        return filtered
