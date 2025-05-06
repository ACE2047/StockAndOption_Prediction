import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class."""
    # API Keys
    POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")
    NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    
    # Flask settings
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
    PORT = int(os.environ.get("PORT", 5000))
    
    # WebSocket settings
    WS_HOST = os.environ.get("WS_HOST", "localhost")
    WS_PORT = int(os.environ.get("WS_PORT", 8765))
    
    # LLM settings
    LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")
    
    # Data fetching settings
    DEFAULT_HISTORICAL_DAYS = int(os.environ.get("DEFAULT_HISTORICAL_DAYS", 90))
    DEFAULT_NEWS_DAYS = int(os.environ.get("DEFAULT_NEWS_DAYS", 7))
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    MODELS_DIR = os.path.join(BASE_DIR, "models")
    
    @classmethod
    def validate(cls):
        """Validate the configuration."""
        missing_keys = []
        
        if not cls.POLYGON_API_KEY:
            missing_keys.append("POLYGON_API_KEY")
        
        if not cls.NEWS_API_KEY:
            missing_keys.append("NEWS_API_KEY")
        
        if not cls.OPENAI_API_KEY:
            missing_keys.append("OPENAI_API_KEY")
        
        if missing_keys:
            print(f"WARNING: The following environment variables are missing: {', '.join(missing_keys)}")
            print("Some features may not work correctly.")
        
        # Create necessary directories
        os.makedirs(cls.CACHE_DIR, exist_ok=True)
        os.makedirs(cls.MODELS_DIR, exist_ok=True)
        
        return len(missing_keys) == 0

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True

# Select configuration based on environment
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}

# Get the current environment or default to development
ENV = os.environ.get("FLASK_ENV", "development").lower()
AppConfig = config_map.get(ENV, DevelopmentConfig)

# Validate configuration
AppConfig.validate()