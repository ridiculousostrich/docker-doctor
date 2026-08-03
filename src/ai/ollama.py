"""
Ollama AI client implementation for Docker Doctor.

Uses the Ollama API to generate AI summaries from Docker logs.
"""

import logging
import ollama
from typing import Dict, Any
from .base import AIProvider

logger = logging.getLogger(__name__)

class OllamaClient(AIProvider):
    """Ollama AI provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Ollama client with configuration.
        
        Args:
            config (dict): Configuration dictionary with 'host', 'model', 'temperature'
        """
        super().__init__(config)
        host = config.get('host', 'http://localhost:11434')
        self.client = ollama.Client(host=host)
        
    def generate_summary(self, prompt: str, **kwargs) -> str:
        """Generate a summary using Ollama.
        
        Args:
            prompt (str): The prompt to send to the AI
            **kwargs: Additional arguments (ignored in Ollama)
            
        Returns:
            str: The AI-generated summary
        """
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={'temperature': self.temperature}
            )
            return response['message']['content'].strip()
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            return f"AI summary unavailable: {str(e)}"
        
    def is_available(self) -> bool:
        """Check if Ollama service is available.
        
        Returns:
            bool: True if service is available, False otherwise
        """
        try:
            # Test connection with a simple request
            self.client.list()
            return True
        except Exception:
            return False
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured model.
        
        Returns:
            dict: Model information or empty dict if error
        """
        try:
            models = self.client.list()
            for model in models.get('models', []):
                if model.get('name') == self.model:
                    return model
            return {}  # Model not found
        except Exception:
            return {}
        
    def set_model(self, model_name: str):
        """Change the model being used.
        
        Args:
            model_name (str): Name of the new model
        """
        self.model = model_name