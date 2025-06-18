import logging
import requests

logger = logging.getLogger(__name__)

def process_user_input(user_input, news_data):
    logger.info(f"Processing user input: {user_input}")
    # Combine user input and news data
    combined_data = f"User Input: {user_input}\nNews Data: {news_data}"
    try:
        # Send combined_data to Ollama LLM for processing
        response = requests.post("http://localhost:11434/api/generate", json={"prompt": combined_data})
        if response.status_code == 200:
            return response.json().get("response", "No response from LLM.")
        else:
            logger.error(f"Error communicating with Ollama LLM: {response.status_code}")
            return "Error processing input."
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to Ollama LLM. Ensure it is running on localhost:11434.")
        return "Error: Ollama LLM is not running." 