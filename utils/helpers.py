"""
Helper functions for the application
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
import re


def format_deadline(deadline: str) -> str:
    """
    Format deadline string
    
    Args:
        deadline: Deadline string
        
    Returns:
        Formatted deadline
    """
    if not deadline or deadline == 'N/A':
        return 'No deadline'
    
    try:
        # Try to parse and format date
        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%b %d, %Y', '%d %b %Y']
        parsed_date = None
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(deadline, fmt)
                break
            except ValueError:
                continue
        
        if parsed_date:
            return parsed_date.strftime('%B %d, %Y')
        else:
            return deadline
            
    except Exception:
        return deadline


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to max length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if not text:
        return ''
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + '...'


def get_status_color(verified: bool) -> str:
    """
    Get color for verification status
    
    Args:
        verified: Verification status
        
    Returns:
        Color string
    """
    return 'green' if verified else 'red'


def get_deadline_status(deadline: str) -> str:
    """
    Get deadline status
    
    Args:
        deadline: Deadline string
        
    Returns:
        Status string
    """
    if not deadline or deadline == 'N/A':
        return 'neutral'
    
    try:
        # Parse deadline
        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%b %d, %Y', '%d %b %Y']
        parsed_date = None
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(deadline, fmt)
                break
            except ValueError:
                continue
        
        if parsed_date:
            days_until = (parsed_date - datetime.now()).days
            
            if days_until < 0:
                return 'expired'
            elif days_until < 7:
                return 'urgent'
            elif days_until < 30:
                return 'soon'
            else:
                return 'normal'
        
    except Exception:
        pass
    
    return 'normal'


def display_metric_cards(metrics: Dict[str, Any]) -> None:
    """
    Display metric cards
    
    Args:
        metrics: Dictionary of metrics
    """
    cols = st.columns(len(metrics))
    
    for idx, (key, value) in enumerate(metrics.items()):
        with cols[idx]:
            st.metric(key, value)


def display_opportunity_card(opportunity: Dict[str, Any], show_score: bool = False) -> None:
    """
    Display an opportunity card
    
    Args:
        opportunity: Opportunity dictionary
        show_score: Whether to show match score
    """
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {opportunity.get('title', 'Untitled')}")
            
            # Organization and category
            org = opportunity.get('organization', 'Unknown')
            category = opportunity.get('category', 'General')
            st.caption(f"🏢 {org} | 📂 {category}")
            
            # Country and deadline
            country = opportunity.get('country', 'Africa')
            deadline = format_deadline(opportunity.get('deadline', 'N/A'))
            status = get_deadline_status(opportunity.get('deadline', 'N/A'))
            
            status_emoji = {
                'urgent': '🔴',
                'soon': '🟡',
                'normal': '🟢',
                'expired': '⚫',
                'neutral': '⚪'
            }
            
            st.caption(f"🌍 {country} | {status_emoji.get(status, '⚪')} {deadline}")
            
            # Description
            description = truncate_text(opportunity.get('description', 'No description available'), 300)
            st.write(description)
            
            # Apply button
            url = opportunity.get('official_url', '#')
            st.markdown(f"[📝 Apply Now]({url})")
            
            # Verification status
            verified = opportunity.get('verified', False)
            if verified:
                st.caption("✅ Verified")
            else:
                st.caption("❌ Not Verified")
        
        with col2:
            # Match score if available
            if show_score and 'match_score' in opportunity:
                score = opportunity.get('match_score', 0)
                percentage = score * 100
                
                st.metric("Match Score", f"{percentage:.1f}%")
                
                # Progress bar
                st.progress(score)
            
            # Source
            source = opportunity.get('source', 'Unknown')
            st.caption(f"Source: {source}")
            
            # Date scraped
            date_scraped = opportunity.get('date_scraped', '')
            if date_scraped:
                try:
                    date_obj = datetime.fromisoformat(date_scraped)
                    st.caption(f"Added: {date_obj.strftime('%Y-%m-%d')}")
                except:
                    pass
        
        st.divider()


def clean_url(url: str) -> str:
    """
    Clean URL
    
    Args:
        url: URL to clean
        
    Returns:
        Cleaned URL
    """
    if not url:
        return ''
    
    # Remove whitespace
    url = url.strip()
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url


def extract_domain(url: str) -> str:
    """
    Extract domain from URL
    
    Args:
        url: URL
        
    Returns:
        Domain
    """
    if not url:
        return ''
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        return domain
    except:
        return url


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid
    
    Args:
        url: URL to check
        
    Returns:
        Boolean indicating validity
    """
    if not url:
        return False
    
    import re
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(pattern.match(url))


def batch_iterator(items: List[Any], batch_size: int = 100):
    """
    Iterate over items in batches
    
    Args:
        items: List of items
        batch_size: Size of each batch
        
    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]
