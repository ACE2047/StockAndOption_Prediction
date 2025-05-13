import asyncio
import json
import websockets
import threading
import time
from typing import Dict, Set, Any, List, Optional
import logging
from datetime import datetime
import requests
import os

# Import configuration
try:
    from config import AppConfig
    POLYGON_API_KEY = AppConfig.POLYGON_API_KEY
    WS_HOST = AppConfig.WS_HOST
    WS_PORT = AppConfig.WS_PORT
except ImportError:
    # Fallback if config is not available
    from dotenv import load_dotenv
    load_dotenv()
    POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")
    WS_HOST = os.environ.get("WS_HOST", "localhost")
    WS_PORT = int(os.environ.get("WS_PORT", 8765))

# Import Polygon WebSocket client
from polygon_websocket_client import PolygonWebSocketClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("websocket_server")

class StockWebSocketServer:
    """WebSocket server for real-time stock data using Polygon.io WebSocket API."""
    
    def __init__(self, host: str = WS_HOST, port: int = WS_PORT):
        """Initialize the WebSocket server.
        
        Args:
            host: Host address to bind the server
            port: Port to bind the server
        """
        self.host = host
        self.port = port
        self.clients: Dict[websockets.WebSocketServerProtocol, Set[str]] = {}
        self.stock_data: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.server = None
        
        # Initialize Polygon WebSocket client
        self.polygon_client = PolygonWebSocketClient()
        
        # Register callback for trade events
        self.polygon_client.register_callback('T', self.handle_polygon_trade)
    
    def handle_polygon_trade(self, trade_data: Dict[str, Any]):
        """Handle trade data from Polygon WebSocket.
        
        Args:
            trade_data: Trade data from Polygon
        """
        try:
            symbol = trade_data.get('sym')
            if not symbol:
                return
                
            # Update our stock data cache
            self.stock_data[symbol] = {
                "price": trade_data.get('p', 0),
                "size": trade_data.get('s', 0),
                "timestamp": trade_data.get('t', 0),
                "exchange": trade_data.get('x', 0),
                "conditions": trade_data.get('c', []),
                "updated_at": datetime.now().isoformat()
            }
            
            # Broadcast to clients asynchronously
            asyncio.run_coroutine_threadsafe(
                self.broadcast_symbol_update(symbol), 
                asyncio.get_event_loop()
            )
        except Exception as e:
            logger.error(f"Error handling Polygon trade data: {e}")
    
    async def broadcast_symbol_update(self, symbol: str):
        """Broadcast symbol update to subscribed clients.
        
        Args:
            symbol: Symbol that was updated
        """
        if symbol not in self.stock_data:
            return
            
        data = self.stock_data[symbol]
        
        # Broadcast to subscribed clients
        for websocket, subscriptions in self.clients.items():
            if symbol in subscriptions:
                try:
                    await websocket.send(json.dumps({
                        "type": "stock_update",
                        "symbol": symbol,
                        "data": data
                    }))
                except websockets.exceptions.ConnectionClosed:
                    pass
    
    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new client connection.
        
        Args:
            websocket: WebSocket connection to register
        """
        self.clients[websocket] = set()
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
    
    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a client connection.
        
        Args:
            websocket: WebSocket connection to unregister
        """
        if websocket in self.clients:
            # Get the symbols this client was subscribed to
            symbols = list(self.clients[websocket])
            
            # Check if any symbols are no longer needed by any client
            for symbol in symbols:
                still_needed = False
                for other_client, other_subscriptions in self.clients.items():
                    if other_client != websocket and symbol in other_subscriptions:
                        still_needed = True
                        break
                
                # If no other clients need this symbol, unsubscribe from Polygon
                if not still_needed:
                    self.polygon_client.unsubscribe([symbol])
            
            # Remove the client
            del self.clients[websocket]
            
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def subscribe(self, websocket: websockets.WebSocketServerProtocol, symbol: str):
        """Subscribe a client to a stock symbol.
        
        Args:
            websocket: WebSocket connection
            symbol: Stock symbol to subscribe to
        """
        symbol = symbol.upper()
        
        if websocket in self.clients:
            # Check if this is a new subscription for this client
            is_new_subscription = symbol not in self.clients[websocket]
            
            # Add to client's subscriptions
            self.clients[websocket].add(symbol)
            
            # If this is a new subscription, subscribe to Polygon
            if is_new_subscription:
                self.polygon_client.subscribe([symbol])
            
            # Send initial data if available
            if symbol in self.stock_data:
                await websocket.send(json.dumps({
                    "type": "stock_update",
                    "symbol": symbol,
                    "data": self.stock_data[symbol]
                }))
            else:
                # Fetch initial data if not available
                data = self.fetch_stock_data(symbol)
                if data:
                    self.stock_data[symbol] = data
                    await websocket.send(json.dumps({
                        "type": "stock_update",
                        "symbol": symbol,
                        "data": data
                    }))
            
            logger.info(f"Client subscribed to {symbol}")
    
    async def unsubscribe(self, websocket: websockets.WebSocketServerProtocol, symbol: str):
        """Unsubscribe a client from a stock symbol.
        
        Args:
            websocket: WebSocket connection
            symbol: Stock symbol to unsubscribe from
        """
        symbol = symbol.upper()
        
        if websocket in self.clients and symbol in self.clients[websocket]:
            # Remove from client's subscriptions
            self.clients[websocket].remove(symbol)
            
            # Check if any other clients are still subscribed to this symbol
            still_needed = False
            for other_client, other_subscriptions in self.clients.items():
                if other_client != websocket and symbol in other_subscriptions:
                    still_needed = True
                    break
            
            # If no other clients need this symbol, unsubscribe from Polygon
            if not still_needed:
                self.polygon_client.unsubscribe([symbol])
            
            logger.info(f"Client unsubscribed from {symbol}")
    
    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Handle incoming messages from clients.
        
        Args:
            websocket: WebSocket connection
            message: Message received from client
        """
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe":
                symbol = data.get("symbol")
                if symbol:
                    await self.subscribe(websocket, symbol)
            
            elif action == "unsubscribe":
                symbol = data.get("symbol")
                if symbol:
                    await self.unsubscribe(websocket, symbol)
            
            elif action == "ping":
                await websocket.send(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
            
            else:
                logger.warning(f"Unknown action: {action}")
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle WebSocket connections.
        
        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    def fetch_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch current stock data from Polygon REST API.
        
        Args:
            symbol: Stock symbol to fetch data for
            
        Returns:
            Dictionary with stock data or None if fetch failed
        """
        url = f"https://api.polygon.io/v2/last/trade/{symbol}?apiKey={POLYGON_API_KEY}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                result = data.get('results', {})
                
                if result:
                    return {
                        "price": result.get('p', 0),
                        "size": result.get('s', 0),
                        "timestamp": result.get('t', 0),
                        "exchange": result.get('x', 0),
                        "conditions": result.get('c', []),
                        "updated_at": datetime.now().isoformat()
                    }
            return None
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    async def start_server(self):
        """Start the WebSocket server."""
        self.running = True
        
        # Start the Polygon WebSocket client
        self.polygon_client.start()
        
        # Start the WebSocket server
        self.server = await websockets.serve(self.handler, self.host, self.port)
        logger.info(f"WebSocket server started at ws://{self.host}:{self.port}")
        
        # Keep the server running
        await self.server.wait_closed()
    
    def stop(self):
        """Stop the WebSocket server."""
        self.running = False
        
        # Stop the Polygon WebSocket client
        self.polygon_client.stop()
        
        # Close the server
        if self.server:
            self.server.close()
            
        logger.info("WebSocket server stopped")

def run_server():
    """Run the WebSocket server."""
    server = StockWebSocketServer()
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()

if __name__ == "__main__":
    run_server()