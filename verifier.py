"""
Opportunity Verifier - Verifies and validates opportunities
"""

import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)


class Verifier:
    """Verify opportunity authenticity and quality"""
    
    def __init__(self):
        """Initialize the verifier"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Blocked domains
        self.blocked_domains = {
            'facebook.com', 'www.facebook.com', 'fb.com',
            'linkedin.com', 'www.linkedin.com',
            'medium.com', 'www.medium.com',
            'reddit.com', 'www.reddit.com',
            'blogspot.com', 'wordpress.com',
            'youtube.com', 'www.youtube.com',
            'twitter.com', 'www.twitter.com',
            'instagram.com', 'www.instagram.com'
        }
        
        # Trusted domains
        self.trusted_domains = {
            'africanunion.org', 'un.org', 'worldbank.org', 'afdb.org',
            'mastercardfdn.org', 'google.com', 'microsoft.com',
            'youthhubafrica.org', 'opportunitiesforafrica.org',
            'unicef.org', 'unesco.org', 'undp.org',
            'britishcouncil.org', 'commonwealth.org',
            '.edu', '.gov', '.org'
        }
    
    def verify_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a single opportunity
        
        Args:
            opportunity: Opportunity dictionary
            
        Returns:
            Verified opportunity with verification status
        """
        verified = False
        verification_details = []
        
        # Check URL
        url = opportunity.get('official_url', '')
        if not url:
            verification_details.append("No URL provided")
            opportunity['verified'] = False
            opportunity['verification_details'] = verification_details
            return opportunity
        
        # Parse URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check HTTPS
        if parsed_url.scheme != 'https':
            verification_details.append("Not HTTPS")
        
        # Check domain
        if self._is_blocked_domain(domain):
            verification_details.append(f"Blocked domain: {domain}")
            opportunity['verified'] = False
            opportunity['verification_details'] = verification_details
            return opportunity
        
        # Check if domain is trusted
        is_trusted = self._is_trusted_domain(domain)
        if is_trusted:
            verification_details.append("Trusted domain")
        
        # Check response status
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                verification_details.append("Response OK")
                
                # Check content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for application page indicators
                is_application_page = self._is_application_page(soup, url)
                if is_application_page:
                    verification_details.append("Application page detected")
                    verified = True
                else:
                    verification_details.append("Not an application page")
                    
                # Check for official indicators
                has_official = self._check_official_indicators(soup, domain)
                if has_official:
                    verification_details.append("Official indicators found")
                    verified = True
                    
            else:
                verification_details.append(f"Response status: {response.status_code}")
                
        except Exception as e:
            verification_details.append(f"Error checking URL: {str(e)}")
        
        # Final verification decision
        opportunity['verified'] = verified and len(verification_details) >= 2
        opportunity['verification_details'] = verification_details
        opportunity['verified_date'] = datetime.now().isoformat()
        
        return opportunity
    
    def verify_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verify multiple opportunities
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            List of verified opportunities
        """
        verified_opportunities = []
        
        for opp in opportunities:
            verified = self.verify_opportunity(opp)
            verified_opportunities.append(verified)
        
        return verified_opportunities
    
    def _is_blocked_domain(self, domain: str) -> bool:
        """Check if domain is blocked"""
        domain = domain.lower()
        
        for blocked in self.blocked_domains:
            if blocked in domain or domain in blocked:
                return True
        
        return False
    
    def _is_trusted_domain(self, domain: str) -> bool:
        """Check if domain is trusted"""
        domain = domain.lower()
        
        for trusted in self.trusted_domains:
            if domain.endswith(trusted) or trusted in domain:
                return True
        
        return False
    
    def _is_application_page(self, soup: BeautifulSoup, url: str) -> bool:
        """Check if page is an application page"""
        # Look for application indicators
        text = soup.get_text().lower()
        
        application_keywords = [
            'apply now', 'application', 'apply here', 'submit application',
            'online application', 'application form', 'apply online',
            'submit your application', 'application deadline', 'how to apply'
        ]
        
        # Check for application keywords
        for keyword in application_keywords:
            if keyword in text:
                return True
        
        # Check for forms
        forms = soup.find_all('form')
        if forms:
            for form in forms:
                action = form.get('action', '')
                if 'apply' in action.lower() or 'application' in action.lower():
                    return True
        
        # Check for apply buttons
        buttons = soup.find_all(['button', 'a'], text=re.compile(r'apply|application', re.I))
        if buttons:
            return True
        
        return False
    
    def _check_official_indicators(self, soup: BeautifulSoup, domain: str) -> bool:
        """Check for official organization indicators"""
        # Look for official indicators
        text = soup.get_text().lower()
        
        official_keywords = [
            'official', 'organization', 'foundation', 'program',
            'initiative', 'department', 'ministry', 'commission'
        ]
        
        # Check for official keywords
        for keyword in official_keywords:
            if keyword in text:
                return True
        
        # Check for organization logos or headers
        headers = soup.find_all(['h1', 'h2', 'h3'])
        for header in headers:
            header_text = header.get_text().lower()
            for org in ['foundation', 'organization', 'initiative', 'program']:
                if org in header_text:
                    return True
        
        return False
    
    def extract_application_url(self, url: str) -> str:
        """
        Extract the actual application URL if the page is an aggregator
        
        Args:
            url: URL to check
            
        Returns:
            Extracted application URL
        """
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for application links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                text = link.get_text().lower()
                
                if 'apply' in text or 'application' in text:
                    if href.startswith('http'):
                        return href
                    elif href.startswith('/'):
                        parsed = urlparse(url)
                        return f"{parsed.scheme}://{parsed.netloc}{href}"
            
            # Check for external application links
            external_links = soup.find_all('a', href=True)
            for link in external_links:
                href = link.get('href', '')
                if href.startswith('http') and any(trusted in href for trusted in self.trusted_domains):
                    return href
            
        except Exception as e:
            logger.error(f"Error extracting application URL: {str(e)}")
        
        return url
