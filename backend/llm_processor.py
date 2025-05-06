import os
import json
import requests
from typing import List, Dict, Any, Optional

# Import configuration
try:
    from config import AppConfig
    OPENAI_API_KEY = AppConfig.OPENAI_API_KEY
    DEFAULT_LLM_MODEL = AppConfig.LLM_MODEL
except ImportError:
    # Fallback if config is not available
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    DEFAULT_LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")

class LLMProcessor:
    """Process information using Large Language Models."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_LLM_MODEL):
        """Initialize the LLM processor.
        
        Args:
            api_key: API key for OpenAI. If None, uses the OPENAI_API_KEY from environment.
            model: The LLM model to use
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model
        
        if not self.api_key:
            print("WARNING: OpenAI API key not set. Please set OPENAI_API_KEY in .env file.")
    
    def analyze_news(self, news_articles: List[Dict[str, Any]], ticker: Optional[str] = None) -> Dict[str, Any]:
        """Analyze news articles to extract insights.
        
        Args:
            news_articles: List of news articles to analyze
            ticker: Optional stock ticker to focus analysis on
            
        Returns:
            Dictionary with analysis results
        """
        if not news_articles:
            return {"error": "No news articles provided for analysis"}
        
        # Prepare the prompt
        ticker_context = f" for {ticker} stock" if ticker else ""
        
        # Limit the number of articles to avoid token limits
        articles_to_analyze = news_articles[:10]
        
        articles_text = "\n\n".join([
            f"Title: {article.get('title', '')}\n"
            f"Date: {article.get('published_at', '')}\n"
            f"Source: {article.get('source', '')}\n"
            f"Description: {article.get('description', '')}"
            for article in articles_to_analyze
        ])
        
        prompt = f"""Analyze the following news articles{ticker_context} and provide:
1. A summary of key points
2. Potential market impact (bullish, bearish, or neutral)
3. Important events or announcements
4. Risks or concerns mentioned
5. Opportunities highlighted

News Articles:
{articles_text}

Provide your analysis in JSON format with the following structure:
{{
  "summary": "Brief summary of key points",
  "market_sentiment": "bullish/bearish/neutral",
  "sentiment_score": 0.0, // -1.0 (very bearish) to 1.0 (very bullish)
  "key_events": ["event1", "event2", ...],
  "risks": ["risk1", "risk2", ...],
  "opportunities": ["opportunity1", "opportunity2", ...],
  "analysis": "Detailed analysis of the news and its potential impact"
}}
"""
        
        try:
            response = self._call_openai_api(prompt)
            
            # Extract the JSON response
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                # If the response is not valid JSON, return it as text
                return {
                    "summary": "Analysis could not be properly formatted",
                    "raw_analysis": response
                }
                
        except Exception as e:
            print(f"Error analyzing news: {e}")
            return {"error": str(e)}
    
    def generate_trading_insights(self, ticker: str, stock_data: Dict[str, Any], 
                                 news_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading insights by combining stock data and news analysis.
        
        Args:
            ticker: Stock ticker symbol
            stock_data: Historical and predicted stock data
            news_analysis: Analysis of news articles
            
        Returns:
            Dictionary with trading insights
        """
        # Prepare the prompt with stock data and news analysis
        prompt = f"""Generate trading insights for {ticker} based on the following data:

Stock Data:
- Current Price: ${stock_data.get('current_price', 'N/A')}
- Predicted Price (Next Day): ${stock_data.get('next_day_predictions', {}).get('ransac', 'N/A')}
- Historical Volatility: {stock_data.get('volatility', 'N/A')}

News Analysis:
- Sentiment: {news_analysis.get('market_sentiment', 'N/A')}
- Key Events: {', '.join(news_analysis.get('key_events', ['None']))}
- Risks: {', '.join(news_analysis.get('risks', ['None']))}
- Opportunities: {', '.join(news_analysis.get('opportunities', ['None']))}

Provide trading insights in JSON format with the following structure:
{{
  "recommendation": "buy/sell/hold",
  "confidence": 0.0, // 0.0 to 1.0
  "time_horizon": "short_term/medium_term/long_term",
  "entry_points": ["price point 1", "price point 2", ...],
  "exit_points": ["price point 1", "price point 2", ...],
  "stop_loss": "suggested stop loss price",
  "take_profit": "suggested take profit price",
  "risk_reward_ratio": 0.0,
  "rationale": "Detailed explanation of the recommendation"
}}
"""
        
        try:
            response = self._call_openai_api(prompt)
            
            # Extract the JSON response
            try:
                insights = json.loads(response)
                return insights
            except json.JSONDecodeError:
                # If the response is not valid JSON, return it as text
                return {
                    "recommendation": "unknown",
                    "rationale": response
                }
                
        except Exception as e:
            print(f"Error generating trading insights: {e}")
            return {"error": str(e)}
    
    def analyze_market_trends(self, market_news: List[Dict[str, Any]], 
                             market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze market trends based on news and market data.
        
        Args:
            market_news: List of market news articles
            market_data: Optional market data (indices, etc.)
            
        Returns:
            Dictionary with market trend analysis
        """
        if not market_news:
            return {"error": "No market news provided for analysis"}
        
        # Limit the number of articles to avoid token limits
        articles_to_analyze = market_news[:10]
        
        articles_text = "\n\n".join([
            f"Title: {article.get('title', '')}\n"
            f"Date: {article.get('published_at', '')}\n"
            f"Source: {article.get('source', '')}\n"
            f"Description: {article.get('description', '')}"
            for article in articles_to_analyze
        ])
        
        market_data_text = ""
        if market_data:
            market_data_text = f"""
Market Data:
- S&P 500: {market_data.get('sp500', 'N/A')}
- Nasdaq: {market_data.get('nasdaq', 'N/A')}
- Dow Jones: {market_data.get('dow', 'N/A')}
- VIX: {market_data.get('vix', 'N/A')}
"""
        
        prompt = f"""Analyze the following market news and data to identify current market trends:

{market_data_text}

Market News:
{articles_text}

Provide your analysis in JSON format with the following structure:
{{
  "overall_market_sentiment": "bullish/bearish/neutral",
  "sentiment_score": 0.0, // -1.0 (very bearish) to 1.0 (very bullish)
  "key_trends": ["trend1", "trend2", ...],
  "sector_outlook": {{
    "technology": "bullish/bearish/neutral",
    "finance": "bullish/bearish/neutral",
    "healthcare": "bullish/bearish/neutral",
    "energy": "bullish/bearish/neutral",
    "consumer": "bullish/bearish/neutral"
  }},
  "market_risks": ["risk1", "risk2", ...],
  "market_opportunities": ["opportunity1", "opportunity2", ...],
  "analysis": "Detailed analysis of current market conditions"
}}
"""
        
        try:
            response = self._call_openai_api(prompt)
            
            # Extract the JSON response
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                # If the response is not valid JSON, return it as text
                return {
                    "overall_market_sentiment": "unknown",
                    "raw_analysis": response
                }
                
        except Exception as e:
            print(f"Error analyzing market trends: {e}")
            return {"error": str(e)}
    
    def _call_openai_api(self, prompt: str) -> str:
        """Call the OpenAI API with the given prompt.
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            The response text from the API
        """
        if not self.api_key:
            return "Error: OpenAI API key not set"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"API call failed with status code {response.status_code}: {response.text}")
        
        return response.json()["choices"][0]["message"]["content"]