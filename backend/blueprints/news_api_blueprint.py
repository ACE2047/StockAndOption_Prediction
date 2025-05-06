from flask import Blueprint, jsonify, request
from news_api import NewsAPIClient
from llm_processor import LLMProcessor
from stock_predictior import predict_next_price

# Import configuration
try:
    from config import AppConfig
    DEFAULT_NEWS_DAYS = AppConfig.DEFAULT_NEWS_DAYS
except ImportError:
    # Fallback if config is not available
    import os
    from dotenv import load_dotenv
    load_dotenv()
    DEFAULT_NEWS_DAYS = int(os.environ.get("DEFAULT_NEWS_DAYS", 7))

# Initialize services
news_client = NewsAPIClient()
llm_processor = LLMProcessor()

# Create blueprint
news_api_bp = Blueprint('news_api', __name__)

@news_api_bp.route('/api/news/<symbol>')
def get_stock_news(symbol):
    """
    Get news articles related to a specific stock ticker.
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        JSON with news articles related to the stock
    """
    try:
        # Get days parameter from query string or use default from config
        days = request.args.get('days', default=DEFAULT_NEWS_DAYS, type=int)
        
        # Fetch news articles
        articles = news_client.get_news_for_ticker(symbol, days=days)
        
        return jsonify(articles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_api_bp.route('/api/news/category/<category>')
def get_category_news(category):
    """
    Get news articles for a specific category.
    
    Args:
        category: News category (technology, finance, healthcare, etc.)
    
    Returns:
        JSON with news articles in the specified category
    """
    try:
        # Get days parameter from query string or use default from config
        days = request.args.get('days', default=DEFAULT_NEWS_DAYS, type=int)
        
        # Fetch category news
        articles = news_client.get_category_news(category, days=days)
        
        return jsonify(articles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_api_bp.route('/api/news/market')
def get_market_news():
    """
    Get general market news.
    
    Returns:
        JSON with market news articles
    """
    try:
        # Get days parameter from query string (default to 3 for market news)
        days = request.args.get('days', default=3, type=int)
        
        # Fetch market news
        articles = news_client.get_market_news(days=days)
        
        return jsonify(articles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_api_bp.route('/api/analysis/news/<symbol>')
def analyze_stock_news(symbol):
    """
    Analyze news articles for a specific stock using LLM.
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        JSON with news analysis
    """
    try:
        # Get days parameter from query string (default to 7)
        days = request.args.get('days', default=7, type=int)
        
        # Fetch news articles
        articles = news_client.get_news_for_ticker(symbol, days=days)
        
        if not articles:
            return jsonify({'error': f'No news articles found for {symbol}'}), 404
        
        # Analyze news articles
        analysis = llm_processor.analyze_news(articles, ticker=symbol)
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_api_bp.route('/api/analysis/market')
def analyze_market_news():
    """
    Analyze market news using LLM.
    
    Returns:
        JSON with market news analysis
    """
    try:
        # Get days parameter from query string (default to 3)
        days = request.args.get('days', default=3, type=int)
        
        # Fetch market news
        articles = news_client.get_market_news(days=days)
        
        if not articles:
            return jsonify({'error': 'No market news articles found'}), 404
        
        # Analyze market news
        analysis = llm_processor.analyze_market_trends(articles)
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_api_bp.route('/api/insights/<symbol>')
def get_trading_insights(symbol):
    """
    Generate trading insights for a stock using LLM.
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        JSON with trading insights
    """
    try:
        # Get stock prediction
        stock_data = predict_next_price(symbol)
        
        if 'error' in stock_data:
            return jsonify({"error": stock_data['error']}), 404
        
        # Get news analysis
        days = request.args.get('days', default=7, type=int)
        articles = news_client.get_news_for_ticker(symbol, days=days)
        
        if not articles:
            return jsonify({'error': f'No news articles found for {symbol}'}), 404
        
        news_analysis = llm_processor.analyze_news(articles, ticker=symbol)
        
        # Generate trading insights
        insights = llm_processor.generate_trading_insights(symbol, stock_data, news_analysis)
        
        return jsonify(insights)
    except Exception as e:
        return jsonify({'error': str(e)}), 500