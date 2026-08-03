"""
AI provider module for Docker Doctor.

Provides standardized interface for interacting with different AI providers.
"""

from .base import get_ai_provider, AIProvider
from .ollama import OllamaClient

__all__ = [
    'AIProvider',
    'OllamaClient',
    'get_ai_provider',
]

# For backward compatibility with existing imports
from .base import AIProviderFactory