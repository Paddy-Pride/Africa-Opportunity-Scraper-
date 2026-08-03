"""
Real Web Scraper for African Youth Opportunities
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
import json

class RealScraper:
    """Actually scrapes real websites for opportunities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.opportunities = []
    
    def scrape_opportunity_desk(self):
        """Scrape Opportunity Desk - Real opportunities"""
        print("🔍 Scraping Opportunity Desk...")
        try:
            url = "https://opportunitydesk.org/category/opportunities/"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article')
            for article in articles[:10]:
                title_elem = article.find('h2')
                link_elem = article.find('a')
                desc_elem = article.find('p')
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    desc = desc_elem.get_text(strip=True)[:300] if desc_elem else ''
                    
                    # Try to find deadline
                    deadline = 'N/A'
                    date_elem = article.find('time')
                    if date_elem:
                        deadline = date_elem.get_text(strip=True)
                    
                    self.opportunities.append({
                        'title': title,
                        'organization': 'Opportunity Desk',
                        'category': self._detect_category(title),
                        'country': 'Various',
                        'deadline': deadline,
                        'description': desc,
                        'url': link,
                        'source': 'Opportunity Desk',
                        'verified': True
                    })
            print(f"  ✅ Found {len(articles)} opportunities")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def scrape_youthhub_africa(self):
        """Scrape Youth Hub Africa"""
        print("🔍 Scraping Youth Hub Africa...")
        try:
            url = "https://www.youthhubafrica.org/opportunities"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            items = soup.find_all(['div', 'li'], class_=re.compile(r'opportunity|item|listing'))
            
            for item in items[:10]:
                title_elem = item.find(['h2', 'h3', 'h4'])
                link_elem = item.find('a')
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://www.youthhubafrica.org{link}"
                    
                    self.opportunities.append({
                        'title': title,
                        'organization': 'Youth Hub Africa',
                        'category': self._detect_category(title),
                        'country': 'Africa',
                        'deadline': 'N/A',
                        'description': item.get_text(strip=True)[:300],
                        'url': link,
                        'source': 'Youth Hub Africa',
                        'verified': True
                    })
            print(f"  ✅ Found {len(items)} opportunities")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def scrape_opportunities_for_africa(self):
        """Scrape Opportunities For Africa"""
        print("🔍 Scraping Opportunities For Africa...")
        try:
            url = "https://opportunitiesforafrica.com"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            posts = soup.find_all(['article', 'div'], class_=re.compile(r'post|entry|item'))
            
            for post in posts[:10]:
                title_elem = post.find(['h2', 'h3'])
                link_elem = post.find('a')
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    
                    self.opportunities.append({
                        'title': title,
                        'organization': 'Opportunities For Africa',
                        'category': self._detect_category(title),
                        'country': 'Africa',
                        'deadline': 'N/A',
                        'description': post.get_text(strip=True)[:300],
                        'url': link,
                        'source': 'Opportunities For Africa',
                        'verified': True
                    })
            print(f"  ✅ Found {len(posts)} opportunities")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def scrape_african_union(self):
        """Scrape African Union opportunities"""
        print("🔍 Scraping African Union...")
        try:
            # African Union careers page
            urls = [
                "https://www.africanunion.org/careers",
                "https://www.africanunion.org/opportunities"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=15)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for job/opportunity listings
                    items = soup.find_all(['div', 'li'], class_=re.compile(r'job|vacancy|career|opportunity'))
                    
                    for item in items[:5]:
                        title_elem = item.find(['h2', 'h3', 'h4'])
                        link_elem = item.find('a')
                        
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            link = link_elem.get('href', '') if link_elem else ''
                            if link and not link.startswith('http'):
                                link = f"https://www.africanunion.org{link}"
                            
                            self.opportunities.append({
                                'title': title,
                                'organization': 'African Union',
                                'category': 'Jobs',
                                'country': 'Africa',
                                'deadline': 'N/A',
                                'description': item.get_text(strip=True)[:300],
                                'url': link,
                                'source': 'African Union',
                                'verified': True
                            })
                except:
                    pass
            print(f"  ✅ Found opportunities from African Union")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def scrape_un_opportunities(self):
        """Scrape UN opportunities"""
        print("🔍 Scraping UN Opportunities...")
        try:
            url = "https://careers.un.org/lbw/Home.aspx"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for job listings
            items = soup.find_all(['tr', 'div'], class_=re.compile(r'job|vacancy|row'))
            
            for item in items[:10]:
                title_elem = item.find(['a', 'span'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 10:  # Filter out small text
                        self.opportunities.append({
                            'title': title,
                            'organization': 'United Nations',
                            'category': 'Jobs',
                            'country': 'Various',
                            'deadline': 'N/A',
                            'description': item.get_text(strip=True)[:300],
                            'url': 'https://careers.un.org',
                            'source': 'United Nations',
                            'verified': True
                        })
            print(f"  ✅ Found UN opportunities")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def scrape_mastercard(self):
        """Scrape Mastercard Foundation"""
        print("🔍 Scraping Mastercard Foundation...")
        try:
            url = "https://www.mastercardfdn.org/what-we-do/"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            items = soup.find_all(['div', 'article'], class_=re.compile(r'program|initiative|card'))
            
            for item in items[:5]:
                title_elem = item.find(['h2', 'h3'])
                link_elem = item.find('a')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '') if link_elem else ''
                    
                    self.opportunities.append({
                        'title': f"Mastercard Foundation: {title}",
                        'organization': 'Mastercard Foundation',
                        'category': self._detect_category(title),
                        'country': 'Africa',
                        'deadline': 'N/A',
                        'description': item.get_text(strip=True)[:300],
                        'url': link if link else url,
                        'source': 'Mastercard Foundation',
                        'verified': True
                    })
            print(f"  ✅ Found Mastercard opportunities")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def scrape_unicef(self):
        """Scrape UNICEF opportunities"""
        print("🔍 Scraping UNICEF...")
        try:
            url = "https://www.unicef.org/careers"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            items = soup.find_all(['div', 'li'], class_=re.compile(r'job|career|vacancy'))
            
            for item in items[:5]:
                title_elem = item.find(['h3', 'h4'])
                link_elem = item.find('a')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '') if link_elem else ''
                    if link and not link.startswith('http'):
                        link = f"https://www.unicef.org{link}"
                    
                    self.opportunities.append({
                        'title': title,
                        'organization': 'UNICEF',
                        'category': 'Jobs',
                        'country': 'Various',
                        'deadline': 'N/A',
                        'description': item.get_text(strip=True)[:300],
                        'url': link,
                        'source': 'UNICEF',
                        'verified': True
                    })
            print(f"  ✅ Found UNICEF opportunities")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def _detect_category(self, title):
        """Detect opportunity category from title"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['scholarship', 'fellowship']):
            return 'Scholarships'
        elif any(word in title_lower for word in ['intern', 'internship']):
            return 'Internships'
        elif any(word in title_lower for word in ['grant', 'funding']):
            return 'Grants'
        elif any(word in title_lower for word in ['job', 'career', 'hire', 'position']):
            return 'Jobs'
        elif any(word in title_lower for word in ['training', 'workshop', 'bootcamp']):
            return 'Training'
        else:
            return 'Opportunities'
    
    def scrape_all(self):
        """Scrape all sources"""
        print("🚀 Starting real web scraping...")
        print("="*50)
        
        # Clear previous results
        self.opportunities = []
        
        # Scrape each source
        self.scrape_opportunity_desk()
        time.sleep(1)
        self.scrape_youthhub_africa()
        time.sleep(1)
        self.scrape_opportunities_for_africa()
        time.sleep(1)
        self.scrape_african_union()
        time.sleep(1)
        self.scrape_un_opportunities()
        time.sleep(1)
        self.scrape_mastercard()
        time.sleep(1)
        self.scrape_unicef()
        
        # Remove duplicates
        unique = []
        seen_titles = set()
        for opp in self.opportunities:
            if opp['title'] not in seen_titles:
                seen_titles.add(opp['title'])
                unique.append(opp)
        
        print("="*50)
        print(f"✅ Total unique opportunities found: {len(unique)}")
        return unique
