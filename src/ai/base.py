"""
Base AI client interface for Docker Doctor.

Provides a standardized interface for interacting with different AI providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config
        self.model = config.get('model', 'default-model')
        self.temperature = config.get('temperature', 0.3)
        
    @abstractmethod
    def generate_summary(self, prompt: str, **kwargs) -> str:
        """Generate a summary using the AI provider.
        
        Args:
            prompt (str): The prompt to send to the AI
            **kwargs: Additional arguments specific to the provider
            
        Returns:
            str: The AI-generated summary
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI provider is available."""
        pass
        
    def get_model_name(self) -> str:
        """Get the model name configured for this provider."""
        return self.model
        
    def get_temperature(self) -> float:
        """Get the temperature configured for this provider."""
        return self.temperature
        
class AIProviderFactory:
    """Factory for creating AI providers."""
    
    @staticmethod
    def create_provider(config: Dict[str, Any]) -> AIProvider:
        """Create an AI provider based on configuration.
        
        Args:
            config (dict): Configuration dictionary with 'provider' key
            
        Returns:
            AIProvider: Configured provider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider_name = config.get('provider', 'ollama').lower()
        
        if provider_name == 'ollama':
            from .ollama import OllamaClient
            return OllamaClient(config)
        elif provider_name == 'openai':
            from .openai import OpenAIClient
            return OpenAIClient(config)
        elif provider_name == 'anthropic':
            from .anthropic import AnthropicClient
            return AnthropicClient(config)
        else:
            raise ValueError(f"Unsupported AI provider: {provider_name}")
        

# Global provider instance
_global_provider = None

def get_ai_provider(config: Dict[str, Any]) -> AIProvider:
    """Get a singleton AI provider instance.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        AIProvider: Configured provider instance
    """
    global _global_provider
    if _global_provider is None:
        _global_provider = AIProviderFactory.create_provider(config)
    return _global_provider