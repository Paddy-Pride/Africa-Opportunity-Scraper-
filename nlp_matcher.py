"""
NLP Matcher - Uses TF-IDF and Cosine Similarity for opportunity matching
"""

import logging
from typing import List, Dict, Any, Optional
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class OpportunityMatcher:
    """Match opportunities to user profiles using NLP"""
    
    def __init__(self):
        """Initialize the matcher"""
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)
        )
        self._fitted = False
        self._opportunity_vectors = None
        self._opportunities = []
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for matching
        
        Args:
            text: Text to preprocess
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text
    
    def prepare_opportunity_text(self, opportunity: Dict[str, Any]) -> str:
        """
        Prepare opportunity text for vectorization
        
        Args:
            opportunity: Opportunity dictionary
            
        Returns:
            Combined text for vectorization
        """
        text_parts = []
        
        # Title
        title = opportunity.get('title', '')
        if title:
            text_parts.append(title)
        
        # Description
        description = opportunity.get('description', '')
        if description:
            text_parts.append(description)
        
        # Category
        category = opportunity.get('category', '')
        if category:
            text_parts.append(category)
        
        # Organization
        organization = opportunity.get('organization', '')
        if organization:
            text_parts.append(organization)
        
        # Country
        country = opportunity.get('country', '')
        if country:
            text_parts.append(country)
        
        return ' '.join(text_parts)
    
    def prepare_user_profile(self, user_profile: str) -> str:
        """
        Prepare user profile for matching
        
        Args:
            user_profile: User profile text
            
        Returns:
            Preprocessed user profile
        """
        return self.preprocess_text(user_profile)
    
    def fit_vectorizer(self, opportunities: List[Dict[str, Any]]) -> None:
        """
        Fit the vectorizer on opportunities
        
        Args:
            opportunities: List of opportunity dictionaries
        """
        if not opportunities:
            logger.warning("No opportunities provided for fitting")
            return
        
        # Prepare opportunity texts
        texts = []
        valid_opportunities = []
        
        for opp in opportunities:
            text = self.prepare_opportunity_text(opp)
            if text.strip():
                texts.append(text)
                valid_opportunities.append(opp)
            else:
                logger.debug(f"Skipping opportunity with empty text: {opp.get('title', 'Unknown')}")
        
        if not texts:
            logger.warning("No valid texts found for vectorization")
            return
        
        try:
            # Fit and transform
            self._opportunity_vectors = self.vectorizer.fit_transform(texts)
            self._opportunities = valid_opportunities
            self._fitted = True
            logger.info(f"Fitted vectorizer on {len(texts)} opportunities")
            
        except Exception as e:
            logger.error(f"Error fitting vectorizer: {str(e)}")
            self._fitted = False
    
    def rank_opportunities(self, user_profile: str, opportunities: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Rank opportunities by relevance to user profile
        
        Args:
            user_profile: User profile text
            opportunities: List of opportunities (uses stored if not provided)
            
        Returns:
            Ranked list of opportunities with scores
        """
        if not user_profile.strip():
            logger.info("Empty user profile provided, returning all opportunities")
            return opportunities or self._opportunities or []
        
        # Use provided opportunities or stored ones
        opportunities_to_use = opportunities if opportunities is not None else self._opportunities
        
        if not opportunities_to_use:
            logger.warning("No opportunities to rank")
            return []
        
        # Fit vectorizer if not fitted or if new opportunities provided
        if opportunities is not None:
            self.fit_vectorizer(opportunities)
        
        if not self._fitted:
            logger.warning("Vectorizer not fitted, cannot rank")
            return opportunities_to_use
        
        try:
            # Prepare user profile
            processed_profile = self.prepare_user_profile(user_profile)
            
            # Transform user profile
            user_vector = self.vectorizer.transform([processed_profile])
            
            # Calculate similarities
            similarities = cosine_similarity(user_vector, self._opportunity_vectors)
            similarity_scores = similarities.flatten()
            
            # Create ranked list
            ranked_opportunities = []
            
            for idx, score in enumerate(similarity_scores):
                if idx < len(self._opportunities):
                    opportunity = self._opportunities[idx].copy()
                    opportunity['match_score'] = float(score)
                    opportunity['match_percentage'] = round(float(score) * 100, 2)
                    ranked_opportunities.append(opportunity)
            
            # Sort by score descending
            ranked_opportunities.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            
            logger.info(f"Ranked {len(ranked_opportunities)} opportunities for user profile")
            return ranked_opportunities
            
        except Exception as e:
            logger.error(f"Error ranking opportunities: {str(e)}")
            return opportunities_to_use
    
    def get_matching_keywords(self, user_profile: str, opportunities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Get keywords matching between user profile and opportunities
        
        Args:
            user_profile: User profile text
            opportunities: List of opportunities
            
        Returns:
            Dictionary of matching keywords by opportunity
        """
        if not user_profile.strip() or not opportunities:
            return {}
        
        # Process user profile
        processed_profile = self.prepare_user_profile(user_profile)
        profile_words = set(processed_profile.split())
        
        matching_keywords = {}
        
        for opp in opportunities:
            text = self.prepare_opportunity_text(opp)
            processed_text = self.preprocess_text(text)
            text_words = set(processed_text.split())
            
            # Find common keywords
            common_words = profile_words.intersection(text_words)
            
            # Filter for meaningful keywords (length > 3)
            meaningful_words = [word for word in common_words if len(word) > 3]
            
            if meaningful_words:
                matching_keywords[opp.get('title', 'Unknown')] = meaningful_words[:10]  # Limit to 10
        
        return matching_keywords
    
    def calculate_relevance(self, user_profile: str, opportunity: Dict[str, Any]) -> float:
        """
        Calculate relevance score for a single opportunity
        
        Args:
            user_profile: User profile text
            opportunity: Opportunity dictionary
            
        Returns:
            Relevance score (0-1)
        """
        if not user_profile.strip():
            return 0.0
        
        # Fit vectorizer with this single opportunity
        self.fit_vectorizer([opportunity])
        
        if not self._fitted:
            return 0.0
        
        try:
            processed_profile = self.prepare_user_profile(user_profile)
            user_vector = self.vectorizer.transform([processed_profile])
            
            similarities = cosine_similarity(user_vector, self._opportunity_vectors)
            return float(similarities.flatten()[0])
            
        except Exception as e:
            logger.error(f"Error calculating relevance: {str(e)}")
            return 0.0
    
    def get_recommendations(self, user_profile: str, opportunities: List[Dict[str, Any]], 
                           top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get top N recommendations
        
        Args:
            user_profile: User profile text
            opportunities: List of opportunities
            top_n: Number of top recommendations to return
            
        Returns:
            Top N recommendations with scores
        """
        if not opportunities:
            return []
        
        ranked = self.rank_opportunities(user_profile, opportunities)
        
        # Filter for opportunities with positive scores
        positive_matches = [opp for opp in ranked if opp.get('match_score', 0) > 0]
        
        if not positive_matches:
            # Return top opportunities without score
            return opportunities[:top_n]
        
        return positive_matches[:top_n]
