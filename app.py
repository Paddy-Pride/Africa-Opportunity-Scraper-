# app.py - Main Flask application with real web scraping
import os
import re
import json
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Store opportunities in memory with thread safety
opportunities_lock = threading.Lock()
opportunities = []
saved_opportunities = set()
last_scrape_time = None
is_scraping = False

class OpportunityScraper:
    """Real web scraper for African youth opportunities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def scrape_opportunity_sources(self):
        """Scrape multiple sources for African youth opportunities"""
        all_opportunities = []
        
        # Source 1: Youth Opportunities Hub (example real source)
        try:
            youth_opps = self.scrape_youth_opportunities()
            all_opportunities.extend(youth_opps)
            logger.info(f"Scraped {len(youth_opps)} from Youth Opportunities")
        except Exception as e:
            logger.error(f"Error scraping Youth Opportunities: {str(e)}")
        
        # Source 2: African Development Bank opportunities
        try:
            afdb_opps = self.scrape_afdb_opportunities()
            all_opportunities.extend(afdb_opps)
            logger.info(f"Scraped {len(afdb_opps)} from African Development Bank")
        except Exception as e:
            logger.error(f"Error scraping AfDB: {str(e)}")
        
        # Source 3: UNESCO Africa opportunities
        try:
            unesco_opps = self.scrape_unesco_africa()
            all_opportunities.extend(unesco_opps)
            logger.info(f"Scraped {len(unesco_opps)} from UNESCO Africa")
        except Exception as e:
            logger.error(f"Error scraping UNESCO: {str(e)}")
        
        # Source 4: Mastercard Foundation opportunities
        try:
            mastercard_opps = self.scrape_mastercard_foundation()
            all_opportunities.extend(mastercard_opps)
            logger.info(f"Scraped {len(mastercard_opps)} from Mastercard Foundation")
        except Exception as e:
            logger.error(f"Error scraping Mastercard Foundation: {str(e)}")
        
        # Source 5: African Union opportunities
        try:
            au_opps = self.scrape_african_union()
            all_opportunities.extend(au_opps)
            logger.info(f"Scraped {len(au_opps)} from African Union")
        except Exception as e:
            logger.error(f"Error scraping African Union: {str(e)}")
        
        # Remove duplicates based on title and description similarity
        unique_opps = self.deduplicate_opportunities(all_opportunities)
        logger.info(f"Total unique opportunities: {len(unique_opps)}")
        
        return unique_opps
    
    def scrape_youth_opportunities(self):
        """Scrape from Youth Opportunities platform"""
        opportunities = []
        urls = [
            'https://www.youthop.com/opportunities/africa',
            'https://www.youthop.com/opportunities/fellowships',
            'https://www.youthop.com/opportunities/scholarships'
        ]
        
        for url in urls:
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find opportunity listings
                    listings = soup.find_all('div', class_='opportunity-item')
                    if not listings:
                        # Try alternative selectors
                        listings = soup.find_all('article', class_='listing-item')
                    
                    for listing in listings[:10]:  # Limit to 10 per page
                        try:
                            title_elem = listing.find('h3') or listing.find('h2') or listing.find('a')
                            title = title_elem.get_text().strip() if title_elem else "Unknown Opportunity"
                            
                            # Extract description
                            desc_elem = listing.find('p', class_='description') or listing.find('div', class_='excerpt')
                            description = desc_elem.get_text().strip() if desc_elem else "Youth opportunity in Africa"
                            
                            # Extract deadline
                            date_elem = listing.find('span', class_='date') or listing.find('div', class_='deadline')
                            deadline = date_elem.get_text().strip() if date_elem else None
                            
                            # Extract location/region
                            location_elem = listing.find('span', class_='location') or listing.find('div', class_='country')
                            location = location_elem.get_text().strip() if location_elem else "Africa"
                            
                            # Determine category
                            category = "scholarship"
                            if 'fellowship' in title.lower() or 'fellow' in title.lower():
                                category = "fellowship"
                            elif 'intern' in title.lower() or 'trainee' in title.lower():
                                category = "internship"
                            elif 'grant' in title.lower() or 'fund' in title.lower():
                                category = "grant"
                            elif 'competition' in title.lower() or 'award' in title.lower():
                                category = "competition"
                            
                            opportunities.append({
                                'title': title[:200],
                                'description': description[:500],
                                'category': category,
                                'region': self.detect_region(location),
                                'country': location,
                                'deadline': deadline,
                                'source': 'Youth Opportunities',
                                'url': url,
                                'saved': False,
                                'scraped_at': datetime.now().isoformat()
                            })
                        except Exception as e:
                            logger.warning(f"Error parsing listing: {str(e)}")
                            continue
            except Exception as e:
                logger.warning(f"Error scraping {url}: {str(e)}")
                continue
        
        return opportunities
    
    def scrape_afdb_opportunities(self):
        """Scrape from African Development Bank"""
        opportunities = []
        try:
            url = 'https://www.afdb.org/en/careers'
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                job_listings = soup.find_all('div', class_='job-listing')
                if not job_listings:
                    job_listings = soup.find_all('article', class_='job')
                
                for job in job_listings[:8]:
                    try:
                        title_elem = job.find('h3') or job.find('a')
                        title = title_elem.get_text().strip() if title_elem else "AfDB Opportunity"
                        
                        desc_elem = job.find('p') or job.find('div', class_='description')
                        description = desc_elem.get_text().strip() if desc_elem else "African Development Bank career opportunity"
                        
                        opportunities.append({
                            'title': title[:200],
                            'description': description[:500],
                            'category': 'internship',
                            'region': 'all',
                            'country': 'Various (Africa)',
                            'deadline': None,
                            'source': 'African Development Bank',
                            'url': url,
                            'saved': False,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Error scraping AfDB: {str(e)}")
        
        return opportunities
    
    def scrape_unesco_africa(self):
        """Scrape from UNESCO Africa"""
        opportunities = []
        try:
            url = 'https://www.unesco.org/en/fieldoffice/africa'
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for opportunities or news items
                items = soup.find_all('div', class_='card') or soup.find_all('article')
                
                for item in items[:8]:
                    try:
                        title_elem = item.find('h2') or item.find('h3')
                        title = title_elem.get_text().strip() if title_elem else "UNESCO Africa Opportunity"
                        
                        desc_elem = item.find('p') or item.find('div', class_='excerpt')
                        description = desc_elem.get_text().strip() if desc_elem else "UNESCO opportunity in Africa"
                        
                        opportunities.append({
                            'title': title[:200],
                            'description': description[:500],
                            'category': 'scholarship',
                            'region': 'all',
                            'country': 'Various (Africa)',
                            'deadline': None,
                            'source': 'UNESCO Africa',
                            'url': url,
                            'saved': False,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Error scraping UNESCO: {str(e)}")
        
        return opportunities
    
    def scrape_mastercard_foundation(self):
        """Scrape from Mastercard Foundation"""
        opportunities = []
        try:
            url = 'https://mastercardfdn.org/our-work/programs/'
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                programs = soup.find_all('div', class_='program-item') or soup.find_all('div', class_='card')
                
                for program in programs[:8]:
                    try:
                        title_elem = program.find('h3') or program.find('a')
                        title = title_elem.get_text().strip() if title_elem else "Mastercard Foundation Opportunity"
                        
                        desc_elem = program.find('p') or program.find('div', class_='description')
                        description = desc_elem.get_text().strip() if desc_elem else "Mastercard Foundation opportunity in Africa"
                        
                        opportunities.append({
                            'title': title[:200],
                            'description': description[:500],
                            'category': 'scholarship',
                            'region': 'all',
                            'country': 'Various (Africa)',
                            'deadline': None,
                            'source': 'Mastercard Foundation',
                            'url': url,
                            'saved': False,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Error scraping Mastercard Foundation: {str(e)}")
        
        return opportunities
    
    def scrape_african_union(self):
        """Scrape from African Union"""
        opportunities = []
        try:
            url = 'https://au.int/en/opportunities'
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                listings = soup.find_all('div', class_='view-content') or soup.find_all('article')
                
                for listing in listings[:8]:
                    try:
                        title_elem = listing.find('a') or listing.find('h3')
                        title = title_elem.get_text().strip() if title_elem else "African Union Opportunity"
                        
                        desc_elem = listing.find('p') or listing.find('div', class_='description')
                        description = desc_elem.get_text().strip() if desc_elem else "African Union opportunity"
                        
                        opportunities.append({
                            'title': title[:200],
                            'description': description[:500],
                            'category': 'fellowship',
                            'region': 'all',
                            'country': 'Various (Africa)',
                            'deadline': None,
                            'source': 'African Union',
                            'url': url,
                            'saved': False,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Error scraping African Union: {str(e)}")
        
        return opportunities
    
    def detect_region(self, location):
        """Detect African region from location string"""
        location_lower = location.lower()
        if any(country in location_lower for country in ['nigeria', 'ghana', 'senegal', 'mali', 'côte', 'ivory', 'liberia', 'sierra']):
            return 'west'
        elif any(country in location_lower for country in ['kenya', 'tanzania', 'uganda', 'ethiopia', 'rwanda', 'burundi']):
            return 'east'
        elif any(country in location_lower for country in ['south africa', 'zimbabwe', 'zambia', 'malawi', 'angola']):
            return 'south'
        elif any(country in location_lower for country in ['egypt', 'morocco', 'algeria', 'tunisia', 'libya']):
            return 'north'
        elif any(country in location_lower for country in ['congo', 'cameroon', 'gabon', 'chad', 'car']):
            return 'central'
        else:
            return 'all'
    
    def deduplicate_opportunities(self, opportunities):
        """Remove duplicate opportunities based on title similarity"""
        unique = []
        seen_titles = set()
        
        for opp in opportunities:
            title_key = opp['title'].lower().strip()
            # Simple deduplication
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique.append(opp)
            else:
                # If duplicate, keep the one with more information
                existing = next((o for o in unique if o['title'].lower().strip() == title_key), None)
                if existing and len(opp['description']) > len(existing['description']):
                    unique.remove(existing)
                    unique.append(opp)
        
        return unique

def scrape_opportunities():
    """Wrapper function to scrape and update opportunities"""
    global opportunities, last_scrape_time, is_scraping
    
    with opportunities_lock:
        if is_scraping:
            logger.info("Scraping already in progress, skipping")
            return
        
        is_scraping = True
    
    try:
        logger.info("Starting opportunity scraping...")
        scraper = OpportunityScraper()
        new_opportunities = scraper.scrape_opportunity_sources()
        
        # Preserve saved status for existing opportunities
        with opportunities_lock:
            existing_opps = {opp['title']: opp for opp in opportunities}
            for opp in new_opportunities:
                if opp['title'] in existing_opps and existing_opps[opp['title']].get('saved', False):
                    opp['saved'] = True
            
            opportunities = new_opportunities
            last_scrape_time = datetime.now()
            
            # Remove expired opportunities (older than 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            opportunities = [
                opp for opp in opportunities 
                if not opp.get('deadline') or self.parse_deadline(opp['deadline']) > cutoff_date
            ]
            
        logger.info(f"Scraping completed. Total opportunities: {len(opportunities)}")
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
    finally:
        with opportunities_lock:
            is_scraping = False

def parse_deadline(deadline_str):
    """Parse deadline string to datetime object"""
    if not deadline_str:
        return datetime.now() + timedelta(days=365)
    
    try:
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%b %d, %Y', '%d %b %Y', '%m/%d/%Y']:
            try:
                return datetime.strptime(deadline_str, fmt)
            except:
                continue
    except:
        pass
    
    return datetime.now() + timedelta(days=30)  # Default to 30 days if parsing fails

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/api/opportunities')
def get_opportunities():
    """API endpoint to get filtered opportunities"""
    category = request.args.get('category', 'all')
    region = request.args.get('region', 'all')
    search = request.args.get('search', '').lower()
    
    with opportunities_lock:
        filtered = opportunities.copy()
    
    # Apply filters
    if category != 'all':
        filtered = [o for o in filtered if o.get('category') == category]
    
    if region != 'all':
        filtered = [o for o in filtered if o.get('region') == region]
    
    if search:
        filtered = [
            o for o in filtered 
            if search in o['title'].lower() or search in o['description'].lower()
        ]
    
    # Sort by scraped_at (newest first)
    filtered.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
    
    return jsonify({
        'opportunities': filtered,
        'total': len(filtered),
        'last_scrape': last_scrape_time.isoformat() if last_scrape_time else None,
        'sources': list(set(o.get('source', 'Unknown') for o in filtered))
    })

@app.route('/api/save/<int:index>', methods=['POST'])
def save_opportunity(index):
    """Save an opportunity"""
    with opportunities_lock:
        if 0 <= index < len(opportunities):
            opportunities[index]['saved'] = True
            return jsonify({'success': True, 'message': 'Opportunity saved'})
    return jsonify({'success': False, 'message': 'Opportunity not found'}), 404

@app.route('/api/unsave/<int:index>', methods=['POST'])
def unsave_opportunity(index):
    """Unsave an opportunity"""
    with opportunities_lock:
        if 0 <= index < len(opportunities):
            opportunities[index]['saved'] = False
            return jsonify({'success': True, 'message': 'Opportunity unsaved'})
    return jsonify({'success': False, 'message': 'Opportunity not found'}), 404

@app.route('/api/refresh', methods=['POST'])
def refresh_opportunities():
    """Trigger a manual scrape refresh"""
    threading.Thread(target=scrape_opportunities, daemon=True).start()
    return jsonify({'success': True, 'message': 'Scraping started'})

@app.route('/api/stats')
def get_stats():
    """Get scraping statistics"""
    with opportunities_lock:
        stats = {
            'total_opportunities': len(opportunities),
            'saved_count': sum(1 for o in opportunities if o.get('saved', False)),
            'last_scrape': last_scrape_time.isoformat() if last_scrape_time else None,
            'sources': list(set(o.get('source', 'Unknown') for o in opportunities))
        }
    return jsonify(stats)

# Create templates directory and index.html
os.makedirs('templates', exist_ok=True)

# Write the HTML template
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AfriYouth · African Opportunity Scraper</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
        
        body {
            background: #f0f4f8;
            min-height: 100vh;
            padding: 2rem 1.5rem;
        }
        
        .app-container {
            max-width: 1440px;
            margin: 0 auto;
        }
        
        .header {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #e8edf3;
        }
        
        .brand h1 {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #0a2e42, #1d5a7a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .brand span {
            font-weight: 400;
            font-size: 1rem;
            color: #2c6b8a;
            -webkit-text-fill-color: #2c6b8a;
        }
        
        .badge-live {
            background: #e6f0f5;
            padding: 0.5rem 1.2rem;
            border-radius: 60px;
            font-size: 0.85rem;
            color: #0f3b4f;
            border: 1px solid #bfd7e3;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .pulse-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #1f9b5e;
            border-radius: 50%;
            animation: pulse 1.8s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 0.4; transform: scale(0.9); }
            50% { opacity: 1; transform: scale(1.2); }
            100% { opacity: 0.4; transform: scale(0.9); }
        }
        
        .toolbar {
            background: white;
            padding: 1.2rem 1.5rem;
            border-radius: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 1rem 2rem;
        }
        
        .filter-group {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.8rem 1.5rem;
            flex: 2 1 300px;
        }
        
        .filter-group label {
            font-size: 0.85rem;
            font-weight: 500;
            color: #1f4457;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .filter-group select, .filter-group input {
            background: #f3f8fc;
            border: 1px solid #dde7ef;
            padding: 0.5rem 1rem;
            border-radius: 40px;
            font-size: 0.9rem;
            color: #0d2c3b;
            outline: none;
            transition: 0.15s;
            min-width: 130px;
        }
        
        .filter-group select:focus, .filter-group input:focus {
            border-color: #2e7d9c;
            background: white;
            box-shadow: 0 0 0 3px rgba(30,100,130,0.1);
        }
        
        .action-group {
            display: flex;
            gap: 0.6rem;
            margin-left: auto;
            flex-wrap: wrap;
        }
        
        .btn {
            background: white;
            border: 1px solid #d9e4ed;
            padding: 0.5rem 1.2rem;
            border-radius: 40px;
            font-weight: 500;
            font-size: 0.85rem;
            color: #1b4053;
            cursor: pointer;
            transition: 0.15s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: #1d4a5f;
            border-color: #1d4a5f;
            color: white;
        }
        
        .btn-primary:hover {
            background: #123b4e;
        }
        
        .btn:hover {
            background: #f2f8fe;
            border-color: #b6cedd;
        }
        
        .opportunity-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 1.8rem;
        }
        
        .opportunity-card {
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
            border: 1px solid #e9f0f5;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
        }
        
        .opportunity-card:hover {
            box-shadow: 0 8px 24px rgba(15,60,80,0.08);
            transform: translateY(-2px);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.8rem;
        }
        
        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #0c2d3d;
            line-height: 1.3;
        }
        
        .card-badge {
            background: #e3edf5;
            padding: 0.2rem 0.7rem;
            border-radius: 40px;
            font-size: 0.7rem;
            font-weight: 600;
            color: #144a60;
            white-space: nowrap;
            border: 1px solid #cadeec;
        }
        
        .card-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem 1.2rem;
            margin: 0.6rem 0 0.9rem 0;
            font-size: 0.8rem;
            color: #315d72;
        }
        
        .card-meta i {
            width: 1.1rem;
            color: #35758f;
        }
        
        .card-desc {
            font-size: 0.9rem;
            line-height: 1.5;
            color: #1e4053;
            margin: 0.4rem 0 1.2rem 0;
            flex: 1;
        }
        
        .card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid #ecf3f8;
            padding-top: 1rem;
        }
        
        .card-footer .deadline {
            font-size: 0.75rem;
            color: #3c6f86;
            background: #f0f7fc;
            padding: 0.2rem 0.8rem;
            border-radius: 30px;
        }
        
        .card-actions {
            display: flex;
            gap: 0.4rem;
        }
        
        .card-actions button {
            background: transparent;
            border: 1px solid transparent;
            padding: 0.3rem 0.7rem;
            border-radius: 30px;
            font-size: 0.8rem;
            color: #265b72;
            cursor: pointer;
            transition: 0.1s;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .card-actions button:hover {
            background: #e3eef7;
            border-color: #c5dae8;
        }
        
        .card-actions .save-btn.saved {
            color: #0f7b3a;
            background: #e2f3e9;
            border-color: #b5dac8;
        }
        
        .empty-state {
            grid-column: 1 / -1;
            text-align: center;
            padding: 4rem 1rem;
            background: #f9fcfe;
            border-radius: 40px;
            border: 1px dashed #c2dae8;
            color: #2b5f78;
        }
        
        .loading-spinner {
            text-align: center;
            padding: 3rem;
            color: #2c6b8a;
            grid-column: 1 / -1;
        }
        
        .stats-bar {
            margin-top: 2rem;
            padding: 1rem 1.5rem;
            background: white;
            border-radius: 16px;
            display: flex;
            flex-wrap: wrap;
            gap: 2rem;
            font-size: 0.9rem;
            color: #1f4457;
            border: 1px solid #e9f0f5;
        }
        
        .stats-bar span {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        @media (max-width: 700px) {
            .header { flex-direction: column; align-items: start; gap: 0.8rem; }
            .toolbar { flex-direction: column; align-items: stretch; }
            .filter-group { flex-direction: column; align-items: stretch; }
            .action-group { margin-left: 0; }
        }
    </style>
</head>
<body>
<div class="app-container">
    <header class="header">
        <div class="brand">
            <h1>AfriYouth <span>opportunity scraper</span></h1>
        </div>
        <div class="badge-live">
            <span class="pulse-dot"></span> live scraping
            <i class="fas fa-rotate-right" style="margin-left: 6px; opacity: 0.7;"></i>
        </div>
    </header>
    
    <div class="toolbar">
        <div class="filter-group">
            <label><i class="fas fa-tag"></i> Category
                <select id="categoryFilter">
                    <option value="all">All</option>
                    <option value="fellowship">Fellowship</option>
                    <option value="scholarship">Scholarship</option>
                    <option value="internship">Internship</option>
                    <option value="grant">Grant</option>
                    <option value="competition">Competition</option>
                </select>
            </label>
            <label><i class="fas fa-location-dot"></i> Region
                <select id="regionFilter">
                    <option value="all">All Africa</option>
                    <option value="west">West Africa</option>
                    <option value="east">East Africa</option>
                    <option value="south">Southern Africa</option>
                    <option value="north">North Africa</option>
                    <option value="central">Central Africa</option>
                </select>
            </label>
            <label><i class="fas fa-search"></i>
                <input type="text" id="searchInput" placeholder="Search opportunities..." />
            </label>
        </div>
        <div class="action-group">
            <button class="btn" id="resetBtn"><i class="fas fa-undo"></i> Reset</button>
            <button class="btn btn-primary" id="refreshBtn"><i class="fas fa-cloud-upload-alt"></i> Refresh</button>
        </div>
    </div>
    
    <div id="opportunityGrid" class="opportunity-grid">
        <div class="loading-spinner">
            <i class="fas fa-spinner fa-pulse fa-2x"></i>
            <p style="margin-top: 1rem;">Loading opportunities...</p>
        </div>
    </div>
    
    <div class="stats-bar" id="statsBar">
        <span><i class="fas fa-list"></i> Total: <strong id="totalCount">0</strong></span>
        <span><i class="fas fa-bookmark"></i> Saved: <strong id="savedCount">0</strong></span>
        <span><i class="fas fa-clock"></i> Last scrape: <span id="lastScrape">Never</span></span>
    </div>
</div>

<script>
    // State
    let opportunities = [];
    let savedIds = new Set();
    let currentFilters = {
        category: 'all',
        region: 'all',
        search: ''
    };
    
    // DOM Elements
    const grid = document.getElementById('opportunityGrid');
    const categoryFilter = document.getElementById('categoryFilter');
    const regionFilter = document.getElementById('regionFilter');
    const searchInput = document.getElementById('searchInput');
    const resetBtn = document.getElementById('resetBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const totalCount = document.getElementById('totalCount');
    const savedCount = document.getElementById('savedCount');
    const lastScrape = document.getElementById('lastScrape');
    
    // Fetch opportunities from API
    async function fetchOpportunities() {
        try {
            const params = new URLSearchParams({
                category: currentFilters.category,
                region: currentFilters.region,
                search: currentFilters.search
            });
            
            const response = await fetch(`/api/opportunities?${params}`);
            const data = await response.json();
            
            opportunities = data.opportunities;
            savedIds = new Set(opportunities.filter(o => o.saved).map((_, i) => i));
            
            // Update stats
            totalCount.textContent = data.total;
            savedCount.textContent = opportunities.filter(o => o.saved).length;
            lastScrape.textContent = data.last_scrape ? new Date(data.last_scrape).toLocaleString() : 'Never';
            
            renderOpportunities();
        } catch (error) {
            console.error('Error fetching opportunities:', error);
            grid.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Error loading opportunities</p></div>`;
        }
    }
    
    // Render opportunities
    function renderOpportunities() {
        if (opportunities.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-compass" style="font-size:2.5rem; color:#34758f; margin-bottom:1rem; display:block;"></i>
                    <p style="font-size:1.2rem; font-weight:500;">No opportunities found</p>
                    <p style="color:#4f7b92;">Try adjusting filters or refresh the scraper</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        opportunities.forEach((opp, index) => {
            const isSaved = savedIds.has(index);
            const deadlineDisplay = opp.deadline || 'No deadline';
            const source = opp.source || 'Unknown source';
            
            html += `
                <div class="opportunity-card" data-index="${index}">
                    <div class="card-header">
                        <div class="card-title">${escapeHtml(opp.title)}</div>
                        <span class="card-badge">${opp.category || 'opportunity'}</span>
                    </div>
                    <div class="card-meta">
                        <span><i class="fas fa-map-pin"></i> ${opp.country || opp.region || 'Africa'}</span>
                        <span><i class="fas fa-tag"></i> ${opp.category || 'opportunity'}</span>
                        <span><i class="fas fa-source"></i> ${escapeHtml(source)}</span>
                    </div>
                    <div class="card-desc">${escapeHtml(opp.description || 'No description available')}</div>
                    <div class="card-footer">
                        <span class="deadline"><i class="far fa-calendar-alt"></i> ${escapeHtml(deadlineDisplay)}</span>
                        <div class="card-actions">
                            <button class="save-btn ${isSaved ? 'saved' : ''}" data-index="${index}">
                                <i class="fas fa-bookmark"></i> ${isSaved ? 'Saved' : 'Save'}
                            </button>
                            <button class="share-btn" data-index="${index}">
                                <i class="fas fa-share-alt"></i> Share
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        grid.innerHTML = html;
        
        // Attach event listeners
        document.querySelectorAll('.save-btn').forEach(btn => {
            btn.addEventListener('click', async function(e) {
                e.stopPropagation();
                const index = parseInt(this.dataset.index);
                await toggleSave(index);
            });
        });
        
        document.querySelectorAll('.share-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const index = parseInt(this.dataset.index);
                const opp = opportunities[index];
                if (opp) {
                    const shareText = `${opp.title} - ${opp.description}`;
                    if (navigator.share) {
                        navigator.share({ title: opp.title, text: shareText });
                    } else {
                        navigator.clipboard?.writeText(shareText).then(() => {
                            alert('Opportunity details copied to clipboard!');
                        }).catch(() => {
                            alert(`Share: ${shareText}`);
                        });
                    }
                }
            });
        });
    }
    
    // Toggle save status
    async function toggleSave(index) {
        const opp = opportunities[index];
        if (!opp) return;
        
        const isSaved = savedIds.has(index);
        const endpoint = isSaved ? '/api/unsave' : '/api/save';
        
        try {
            const response = await fetch(`${endpoint}/${index}`, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                if (isSaved) {
                    savedIds.delete(index);
                    opp.saved = false;
                } else {
                    savedIds.add(index);
                    opp.saved = true;
                }
                savedCount.textContent = opportunities.filter(o => o.saved).length;
                renderOpportunities();
            }
        } catch (error) {
            console.error('Error toggling save:', error);
        }
    }
    
    // Refresh opportunities
    async function refreshOpportunities() {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-pulse"></i> Scraping...';
        
        try {
            const response = await fetch('/api/refresh', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                // Wait a moment for scraping to complete
                setTimeout(() => {
                    fetchOpportunities();
                }, 2000);
            }
        } catch (error) {
            console.error('Error refreshing:', error);
        } finally {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-cloud-upload-alt"></i> Refresh';
        }
    }
    
    // Reset filters
    function resetFilters() {
        categoryFilter.value = 'all';
        regionFilter.value = 'all';
        searchInput.value = '';
        currentFilters = { category: 'all', region: 'all', search: '' };
        fetchOpportunities();
    }
    
    // Utility: escape HTML
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Event listeners
    categoryFilter.addEventListener('change', function() {
        currentFilters.category = this.value;
        fetchOpportunities();
    });
    
    regionFilter.addEventListener('change', function() {
        currentFilters.region = this.value;
        fetchOpportunities();
    });
    
    searchInput.addEventListener('input', function() {
        currentFilters.search = this.value;
        fetchOpportunities();
    });
    
    resetBtn.addEventListener('click', resetFilters);
    refreshBtn.addEventListener('click', refreshOpportunities);
    
    // Initial fetch
    fetchOpportunities();
    
    // Auto-refresh every 60 seconds
    setInterval(() => {
        fetchOpportunities();
    }, 60000);
</script>
</body>
</html>
''')

if __name__ == '__main__':
    # Initial scrape on startup
    logger.info("Starting initial scrape...")
    scrape_opportunities()
    
    # Schedule periodic scraping every 30 minutes
    def scheduled_scrape():
        while True:
            time.sleep(1800)  # 30 minutes
            scrape_opportunities()
    
    # Start background scraper thread
    scraper_thread = threading.Thread(target=scheduled_scrape, daemon=True)
    scraper_thread.start()
    
    # Run Flask app
    app.run(debug=False, host='0.0.0.0', port=5000)
