"""qwen/qwen3-4b-2507 Model Configuration for FNA Backend via LM Studio.

This module handles the setup and configuration of the qwen/qwen3-4b-2507 model
hosted on LM Studio server for API-based inference.
"""

import json
from typing import Optional, Dict, Any, List
import requests
from pydantic import BaseSettings


class ModelSettings(BaseSettings):
    """Model configuration settings from environment variables."""
    
    model_name: str = "qwen/qwen3-4b-2507"
    api_url: str = "http://127.0.0.1:1234"
    api_timeout: int = 30
    max_tokens: int = 512
    temperature: float = 0.1
    top_p: float = 0.9
    
    class Config:
        env_prefix = "MODEL_"


class LMStudioAPIError(Exception):
    """Exception raised when LM Studio API calls fail."""
    pass


class Qwen3ModelManager:
    """Manages the qwen/qwen3-4b-2507 model via LM Studio API."""
    
    def __init__(self, settings: Optional[ModelSettings] = None):
        self.settings = settings or ModelSettings()
        self._is_connected = False
    
    def check_connection(self) -> bool:
        """Check if LM Studio server is accessible.
        
        Returns:
            bool: True if server is accessible, False otherwise
        """
        try:
            # Test connection to LM Studio API
            response = requests.get(
                f"{self.settings.api_url}/v1/models",
                timeout=self.settings.api_timeout
            )
            
            if response.status_code == 200:
                models = response.json()
                print(f"✅ Connected to LM Studio at {self.settings.api_url}")
                print(f"Available models: {len(models.get('data', []))}")
                self._is_connected = True
                return True
            else:
                print(f"❌ LM Studio returned status {response.status_code}")
                return False
                
        except requests.ConnectionError:
            print(f"❌ Cannot connect to LM Studio at {self.settings.api_url}")
            print("💡 Make sure LM Studio is running and the model is loaded")
            return False
        except Exception as e:
            print(f"❌ Error connecting to LM Studio: {e}")
            return False
    
    def load_model(self) -> bool:
        """Check connection to LM Studio server.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        return self.check_connection()
    
    def generate_response(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate response using LM Studio API.
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate (overrides default)
            temperature: Sampling temperature (overrides default)
            top_p: Top-p sampling (overrides default)
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
            
        Raises:
            LMStudioAPIError: If API call fails
        """
        if not self._is_connected:
            if not self.check_connection():
                raise LMStudioAPIError("Not connected to LM Studio. Call load_model() first.")
        
        try:
            # Prepare request payload
            payload = {
                "model": self.settings.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens or self.settings.max_tokens,
                "temperature": temperature if temperature is not None else self.settings.temperature,
                "top_p": top_p if top_p is not None else self.settings.top_p,
                "stream": False
            }
            
            # Add any additional kwargs
            payload.update(kwargs)
            
            # Make API request
            response = requests.post(
                f"{self.settings.api_url}/v1/chat/completions",
                json=payload,
                timeout=self.settings.api_timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_msg = f"LM Studio API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg += f" - {error_data['error']}"
                except:
                    pass
                raise LMStudioAPIError(error_msg)
                
        except requests.RequestException as e:
            raise LMStudioAPIError(f"Network error calling LM Studio API: {e}")
        except Exception as e:
            raise LMStudioAPIError(f"Error generating response: {e}")
    
    def is_loaded(self) -> bool:
        """Check if connected to LM Studio."""
        return self._is_connected
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the LM Studio configuration."""
        return {
            "model_name": self.settings.model_name,
            "is_connected": self._is_connected,
            "api_url": self.settings.api_url,
            "api_timeout": self.settings.api_timeout,
            "max_tokens": self.settings.max_tokens,
            "temperature": self.settings.temperature,
            "top_p": self.settings.top_p
        }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from LM Studio.
        
        Returns:
            List of available models with their details
            
        Raises:
            LMStudioAPIError: If API call fails
        """
        try:
            response = requests.get(
                f"{self.settings.api_url}/v1/models",
                timeout=self.settings.api_timeout
            )
            
            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                raise LMStudioAPIError(f"Failed to get models: {response.status_code}")
                
        except requests.RequestException as e:
            raise LMStudioAPIError(f"Network error getting models: {e}")


# Global model instance (singleton pattern)
_model_manager: Optional[Qwen3ModelManager] = None


def get_model_manager() -> Qwen3ModelManager:
    """Get the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = Qwen3ModelManager()
    return _model_manager


def initialize_model() -> bool:
    """Initialize connection to LM Studio on application startup."""
    manager = get_model_manager()
    return manager.load_model()


def generate_text(prompt: str, **kwargs) -> str:
    """Convenience function to generate text using the global model manager."""
    manager = get_model_manager()
    return manager.generate_response(prompt, **kwargs)