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
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
            {'name': 'African Union', 'url': 'https://www.africanunion.org', 'category': 'Grants'},
            {'name': 'United Nations', 'url': 'https://www.un.org', 'category': 'Jobs'},
            {'name': 'World Bank', 'url': 'https://www.worldbank.org', 'category': 'Jobs'},
            {'name': 'African Development Bank', 'url': 'https://www.afdb.org', 'category': 'Jobs'},
            {'name': 'Mastercard Foundation', 'url': 'https://www.mastercardfdn.org', 'category': 'Grants'},
            {'name': 'Google', 'url': 'https://careers.google.com', 'category': 'Jobs'},
            {'name': 'Microsoft', 'url': 'https://careers.microsoft.com', 'category': 'Jobs'},
            {'name': 'Youth Hub Africa', 'url': 'https://youthhubafrica.org', 'category': 'Education'},
            {'name': 'Opportunities For Africa', 'url': 'https://opportunitiesforafrica.com', 'category': 'Education'},
            {'name': 'UNICEF', 'url': 'https://www.unicef.org', 'category': 'Jobs'},
            {'name': 'UNESCO', 'url': 'https://www.unesco.org', 'category': 'Jobs'},
            {'name': 'UNDP', 'url': 'https://www.undp.org', 'category': 'Jobs'},
            {'name': 'British Council', 'url': 'https://www.britishcouncil.org', 'category': 'Education'},
            {'name': 'Commonwealth', 'url': 'https://thecommonwealth.org', 'category': 'Grants'}
        ]
        
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
        """Add a new source"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM sources WHERE url = ?", (source_data.get('url'),))
            if cursor.fetchone():
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
        """Get all sources"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sources ORDER BY name")
        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return sources
    
    def get_enabled_sources(self) -> List[Dict[str, Any]]:
        """Get enabled sources"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sources WHERE enabled = 1 ORDER BY name")
        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return sources
    
    def update_source(self, source_id: int, updates: Dict[str, Any]) -> bool:
        """Update a source"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
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
        """Delete a source"""
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
        """Check if source exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM sources WHERE url = ?", (url,))
        exists = cursor.fetchone() is not None
        conn.close()
        
        return exists
    
    def update_source_scrape_time(self, source_id: int) -> bool:
        """Update source's last scraped time"""
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
    
    def save_scrape_results(self, opportunities: List[Dict[str, Any]]) -> bool:
        """Save scraped opportunities to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for opp in opportunities:
                source_name = opp.get('source', 'Unknown')
                cursor.execute("SELECT id FROM sources WHERE name = ?", (source_name,))
                source_row = cursor.fetchone()
                source_id = source_row[0] if source_row else None
                
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
        """Get verified opportunities"""
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
        """Get all opportunities"""
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
        """Get database statistics"""
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
        """Count opportunities by source"""
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
        """Filter opportunities by search term"""
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
def clear_all_opportunities(self) -> bool:
    """Clear all opportunities from the database"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM opportunities")
        conn.commit()
        conn.close()
        logger.info("Cleared all opportunities")
        return True
    except Exception as e:
        logger.error(f"Error clearing opportunities: {str(e)}")
        return False
