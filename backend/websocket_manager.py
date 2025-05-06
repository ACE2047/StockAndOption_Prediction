import threading
import os
import websocket_server

# Import configuration
try:
    from config import AppConfig
    ENABLE_WEBSOCKET = os.environ.get('ENABLE_WEBSOCKET', 'true').lower() == 'true'
except ImportError:
    # Fallback if config is not available
    from dotenv import load_dotenv
    load_dotenv()
    ENABLE_WEBSOCKET = os.environ.get('ENABLE_WEBSOCKET', 'true').lower() == 'true'

class WebSocketManager:
    """Manages the WebSocket server lifecycle."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebSocketManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once (singleton pattern)
        if not WebSocketManager._initialized:
            self.websocket_thread = None
            self.server_running = False
            WebSocketManager._initialized = True
    
    def start_server(self):
        """Start the WebSocket server in a separate thread if not already running."""
        if not self.server_running and ENABLE_WEBSOCKET:
            self.websocket_thread = threading.Thread(target=self._run_server)
            self.websocket_thread.daemon = True
            self.websocket_thread.start()
            self.server_running = True
            print("WebSocket server started in background thread")
        elif not ENABLE_WEBSOCKET:
            print("WebSocket server is disabled by configuration")
    
    def _run_server(self):
        """Run the WebSocket server."""
        try:
            websocket_server.run_server()
        except Exception as e:
            print(f"Error running WebSocket server: {e}")
            self.server_running = False
    
    def stop_server(self):
        """Stop the WebSocket server if running."""
        if self.server_running and self.websocket_thread:
            # Implement a clean shutdown mechanism if needed
            self.server_running = False
            print("WebSocket server stopped")

# Create a singleton instance
websocket_manager = WebSocketManager()