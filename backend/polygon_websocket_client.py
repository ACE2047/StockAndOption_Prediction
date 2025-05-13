import websocket
import json
import threading
import time
import logging
from typing import Dict, List, Callable, Any, Optional
import os

# Import configuration
try:
    from config import AppConfig
    POLYGON_API_KEY = AppConfig.POLYGON_API_KEY
except ImportError:
    # Fallback if config is not available
    from dotenv import load_dotenv
    load_dotenv()
    POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("polygon_websocket")

class PolygonWebSocketClient:
    """Client for Polygon.io WebSocket API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Polygon WebSocket client.
        
        Args:
            api_key: Polygon.io API key. If None, uses POLYGON_API_KEY from environment.
        """
        self.api_key = api_key or POLYGON_API_KEY
        if not self.api_key:
            raise ValueError("Polygon API key not set. Please set POLYGON_API_KEY in .env file.")
        
        self.ws = None
        self.running = False
        self.subscribed_symbols = set()
        self.callbacks = {}
        self.reconnect_delay = 1  # Start with 1 second delay
        self.max_reconnect_delay = 60  # Maximum delay of 60 seconds
        self.ws_thread = None
        
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages.
        
        Args:
            ws: WebSocket connection
            message: Message received from WebSocket
        """
        try:
            data = json.loads(message)
            
            # Handle different message types
            if isinstance(data, list):
                for item in data:
                    self._process_message(item)
            else:
                self._process_message(data)
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _process_message(self, message: Dict[str, Any]):
        """Process a single message from the WebSocket.
        
        Args:
            message: Message data
        """
        event_type = message.get('ev')
        
        if event_type == 'status':
            status = message.get('status')
            if status == 'connected':
                logger.info("Connected to Polygon WebSocket")
                # Re-subscribe to symbols after reconnection
                if self.subscribed_symbols:
                    self._subscribe_to_symbols(list(self.subscribed_symbols))
            elif status == 'auth_success':
                logger.info("Authentication successful")
            elif status == 'auth_failed':
                logger.error("Authentication failed")
        
        elif event_type in self.callbacks:
            # Call the registered callback for this event type
            for callback in self.callbacks.get(event_type, []):
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error in callback for {event_type}: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors.
        
        Args:
            ws: WebSocket connection
            error: Error that occurred
        """
        logger.error(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close.
        
        Args:
            ws: WebSocket connection
            close_status_code: Status code for close
            close_msg: Close message
        """
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        
        # Attempt to reconnect if we were running
        if self.running:
            logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
            time.sleep(self.reconnect_delay)
            
            # Exponential backoff for reconnect delay
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
            
            self._connect()
    
    def _on_open(self, ws):
        """Handle WebSocket connection open.
        
        Args:
            ws: WebSocket connection
        """
        logger.info("WebSocket connection established")
        
        # Authenticate with API key
        auth_message = {
            "action": "auth",
            "params": self.api_key
        }
        ws.send(json.dumps(auth_message))
        
        # Reset reconnect delay on successful connection
        self.reconnect_delay = 1
    
    def _connect(self):
        """Establish WebSocket connection to Polygon.io."""
        # Close existing connection if any
        if self.ws:
            self.ws.close()
        
        # Create new WebSocket connection
        self.ws = websocket.WebSocketApp(
            "wss://socket.polygon.io/stocks",
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
    
    def _subscribe_to_symbols(self, symbols: List[str]):
        """Subscribe to stock symbols.
        
        Args:
            symbols: List of stock symbols to subscribe to
        """
        if not self.ws:
            logger.error("WebSocket not connected")
            return
        
        # Format symbols for subscription
        formatted_symbols = [f"T.{symbol}" for symbol in symbols]  # T.* for trades
        
        # Send subscription message
        subscribe_message = {
            "action": "subscribe",
            "params": ", ".join(formatted_symbols)
        }
        
        self.ws.send(json.dumps(subscribe_message))
        logger.info(f"Subscribed to symbols: {symbols}")
    
    def start(self):
        """Start the WebSocket client."""
        if self.running:
            logger.warning("WebSocket client already running")
            return
        
        self.running = True
        self._connect()
        
        # Run WebSocket in a separate thread
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        logger.info("Polygon WebSocket client started")
    
    def stop(self):
        """Stop the WebSocket client."""
        self.running = False
        
        if self.ws:
            self.ws.close()
            self.ws = None
        
        logger.info("Polygon WebSocket client stopped")
    
    def subscribe(self, symbols: List[str]):
        """Subscribe to stock symbols.
        
        Args:
            symbols: List of stock symbols to subscribe to
        """
        # Add symbols to our tracking set
        for symbol in symbols:
            self.subscribed_symbols.add(symbol.upper())
        
        # If connected, send subscription
        if self.ws and self.running:
            self._subscribe_to_symbols(symbols)
    
    def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from stock symbols.
        
        Args:
            symbols: List of stock symbols to unsubscribe from
        """
        if not self.ws:
            logger.error("WebSocket not connected")
            return
        
        # Format symbols for unsubscription
        formatted_symbols = [f"T.{symbol}" for symbol in symbols]  # T.* for trades
        
        # Send unsubscription message
        unsubscribe_message = {
            "action": "unsubscribe",
            "params": ", ".join(formatted_symbols)
        }
        
        self.ws.send(json.dumps(unsubscribe_message))
        
        # Remove symbols from our tracking set
        for symbol in symbols:
            self.subscribed_symbols.discard(symbol.upper())
        
        logger.info(f"Unsubscribed from symbols: {symbols}")
    
    def register_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for a specific event type.
        
        Args:
            event_type: Event type to register callback for (e.g., 'T' for trades)
            callback: Function to call when event is received
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        
        self.callbacks[event_type].append(callback)
    
    def unregister_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Unregister a callback for a specific event type.
        
        Args:
            event_type: Event type to unregister callback from
            callback: Function to unregister
        """
        if event_type in self.callbacks and callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)

# Example usage
if __name__ == "__main__":
    # Define a callback for trade events
    def handle_trade(trade_data):
        symbol = trade_data.get('sym')
        price = trade_data.get('p')
        size = trade_data.get('s')
        timestamp = trade_data.get('t')
        print(f"Trade: {symbol} - Price: ${price}, Size: {size}, Time: {timestamp}")
    
    # Create client
    client = PolygonWebSocketClient()
    
    # Register callback for trade events
    client.register_callback('T', handle_trade)
    
    # Start client
    client.start()
    
    # Subscribe to some symbols
    client.subscribe(['AAPL', 'MSFT', 'GOOGL'])
    
    try:
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop client on keyboard interrupt
        client.stop()