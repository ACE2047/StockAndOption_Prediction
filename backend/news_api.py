import requests
import os
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any, Optional

# Import configuration
try:
    from config import AppConfig
    NEWS_API_KEY = AppConfig.NEWS_API_KEY
except ImportError:
    # Fallback if config is not available
    from dotenv import load_dotenv
    load_dotenv()
    NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

class NewsAPIClient:
    """Client for fetching and categorizing news articles related to stocks."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the NewsAPI client.
        
        Args:
            api_key: API key for NewsAPI. If None, uses the NEWS_API_KEY from environment.
        """
        self.api_key = api_key or NEWS_API_KEY
        if not self.api_key:
            print("WARNING: News API key not set. Please set NEWS_API_KEY in .env file.")
        
        # Define categories and their related keywords
        self.categories = {
            'technology': ['tech', 'technology', 'software', 'hardware', 'ai', 'artificial intelligence', 
                          'cloud', 'computing', 'digital', 'internet', 'cybersecurity', 'data'],
            'finance': ['finance', 'banking', 'investment', 'stock market', 'wall street', 'economy',
                       'financial', 'trading', 'market', 'economic', 'fed', 'federal reserve'],
            'healthcare': ['healthcare', 'health', 'medical', 'medicine', 'biotech', 'pharmaceutical',
                          'drug', 'therapy', 'clinical', 'hospital', 'patient', 'disease'],
            'energy': ['energy', 'oil', 'gas', 'renewable', 'solar', 'wind', 'power', 'electricity',
                      'fossil fuel', 'climate', 'carbon', 'clean energy'],
            'consumer': ['retail', 'consumer', 'shopping', 'e-commerce', 'product', 'brand', 'customer',
                        'sales', 'store', 'goods', 'service', 'market'],
            'manufacturing': ['manufacturing', 'industrial', 'factory', 'production', 'supply chain',
                            'materials', 'equipment', 'machinery', 'automotive', 'aerospace'],
            'defense': ['defense', 'military', 'weapon', 'security', 'aerospace', 'contractor',
                       'war', 'army', 'navy', 'air force', 'missile', 'combat']
        }
    
    def get_news_for_ticker(self, ticker: str, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch news articles related to a specific stock ticker.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back for news
            
        Returns:
            List of news articles with categorization
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Format dates for API
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        # Company name lookup would be better, but for simplicity we'll use the ticker
        query = f"{ticker} stock OR {ticker} company OR {ticker} earnings"
        
        url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&to={to_date}&language=en&sortBy=relevancy&apiKey={self.api_key}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            # Process and categorize articles
            processed_articles = []
            for article in articles:
                # Categorize the article
                article_categories = self._categorize_article(article)
                
                processed_articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'categories': article_categories,
                    'ticker': ticker
                })
            
            return processed_articles
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return []
    
    def get_market_news(self, days: int = 3) -> List[Dict[str, Any]]:
        """Fetch general market news.
        
        Args:
            days: Number of days to look back for news
            
        Returns:
            List of market news articles with categorization
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Format dates for API
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        query = "stock market OR wall street OR investing OR economy"
        
        url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&to={to_date}&language=en&sortBy=relevancy&apiKey={self.api_key}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            # Process and categorize articles
            processed_articles = []
            for article in articles:
                # Categorize the article
                article_categories = self._categorize_article(article)
                
                processed_articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'categories': article_categories
                })
            
            return processed_articles
        except Exception as e:
            print(f"Error fetching market news: {e}")
            return []
    
    def get_category_news(self, category: str, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch news articles for a specific category.
        
        Args:
            category: Category name (technology, finance, healthcare, etc.)
            days: Number of days to look back for news
            
        Returns:
            List of news articles in the specified category
        """
        if category not in self.categories:
            return []
        
        # Get keywords for the category
        keywords = self.categories[category]
        query = " OR ".join(keywords[:5])  # Use first 5 keywords to avoid too long URL
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Format dates for API
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&to={to_date}&language=en&sortBy=relevancy&apiKey={self.api_key}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            # Process articles
            processed_articles = []
            for article in articles:
                processed_articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'category': category
                })
            
            return processed_articles
        except Exception as e:
            print(f"Error fetching {category} news: {e}")
            return []
    
    def _categorize_article(self, article: Dict[str, Any]) -> List[str]:
        """Categorize an article based on its content.
        
        Args:
            article: News article data
            
        Returns:
            List of categories the article belongs to
        """
        # Combine title and description for analysis
        content = f"{article.get('title', '')} {article.get('description', '')}"
        content = content.lower()
        
        article_categories = []
        
        # Check each category
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in content:
                    article_categories.append(category)
                    break
        
        # If no categories found, mark as 'general'
        if not article_categories:
            article_categories = ['general']
        
        return article_categories