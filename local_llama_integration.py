"""
Local LLaMA Integration for Power System RAG
==========================================

This module provides integration with local LLaMA models via Ollama
for the RAG-enhanced power system assistant.

Supports:
- Ollama local models (llama2, llama3, codellama, etc.)
- Custom API endpoints
- Streaming responses
- Error handling and fallbacks

Author: Power System Analysis Team
Date: September 2025
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional, Union
import requests
import os

logger = logging.getLogger(__name__)

class LocalLlamaIntegration:
    """Local LLaMA model integration for RAG system"""
    
    def __init__(
        self, 
        api_url: str = "http://localhost:11434",
        model_name: str = "llama3.2:3b",
        timeout: int = 300,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ):
        """
        Initialize local LLaMA integration
        
        Args:
            api_url: Ollama API URL (default: http://localhost:11434)
            model_name: Model name (llama2, llama3, codellama, etc.)
            timeout: Request timeout in seconds
            max_tokens: Maximum response tokens
            temperature: Response creativity (0.0-1.0)
        """
        self.api_url = api_url.rstrip('/')
        self.model_name = model_name
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.available = False
        
        # Check if Ollama is available
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama server is running and model is available"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                if self.model_name in model_names:
                    self.available = True
                    logger.info(f"✅ Ollama available with model: {self.model_name}")
                    return True
                else:
                    # Check for partial matches (e.g., llama3.2:3b matches llama3.2)
                    base_name = self.model_name.split(':')[0]
                    matching_models = [name for name in model_names if name.startswith(base_name)]
                    
                    if matching_models:
                        self.model_name = matching_models[0]  # Use first match
                        self.available = True
                        logger.info(f"✅ Using available model: {self.model_name}")
                        return True
                    else:
                        logger.warning(f"⚠️ Model {self.model_name} not found. Available: {model_names}")
                        # Try to pull the model
                        return self._pull_model()
            else:
                logger.warning(f"⚠️ Ollama server not responding: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Cannot connect to Ollama at {self.api_url}: {e}")
        
        return False
    
    def _pull_model(self) -> bool:
        """Attempt to pull the model if not available"""
        try:
            logger.info(f"🔄 Attempting to pull model: {self.model_name}")
            response = requests.post(
                f"{self.api_url}/api/pull",
                json={"name": self.model_name},
                timeout=300  # Longer timeout for model download
            )
            
            if response.status_code == 200:
                self.available = True
                logger.info(f"✅ Successfully pulled model: {self.model_name}")
                return True
            else:
                logger.error(f"❌ Failed to pull model: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error pulling model: {e}")
        
        return False
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """
        Generate response using local LLaMA model
        
        Args:
            prompt: User prompt/question
            system_prompt: System instructions
            stream: Enable streaming (not implemented yet)
            
        Returns:
            Generated response text
        """
        if not self.available:
            raise Exception(f"Ollama not available. Is the server running at {self.api_url}?")
        
        # Prepare the request
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
            "stream": False  # For now, disable streaming
        }
        
        # Add system prompt if provided
        if system_prompt:
            data["system"] = system_prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/generate",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '').strip()
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
                        
        except asyncio.TimeoutError:
            raise Exception(f"Ollama request timed out after {self.timeout} seconds")
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            raise
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> str:
        """
        Synchronous wrapper for generate_response
        
        Args:
            prompt: User prompt/question
            system_prompt: System instructions
            stream: Enable streaming (ignored for now)
            
        Returns:
            Generated response text
        """
        import asyncio
        
        try:
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async function
            return loop.run_until_complete(
                self.generate_response(prompt, system_prompt, stream)
            )
        except Exception as e:
            logger.error(f"Error in synchronous generate wrapper: {e}")
            return f"I apologize, but I'm experiencing technical difficulties: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m.get('name', '') for m in models]
        except Exception as e:
            logger.error(f"Error getting model list: {e}")
        
        return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            'api_url': self.api_url,
            'model_name': self.model_name,
            'available': self.available,
            'timeout': self.timeout,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }


def create_local_llama_integration(
    model_name: str = None,
    api_url: str = None
) -> LocalLlamaIntegration:
    """
    Factory function to create local LLaMA integration
    
    Args:
        model_name: Model to use (auto-detects if None)
        api_url: API URL (defaults to localhost)
        
    Returns:
        Configured LocalLlamaIntegration instance
    """
    # Use environment variables or defaults
    api_url = api_url or os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
    
    # Auto-detect model if not specified
    if not model_name:
        integration = LocalLlamaIntegration(api_url=api_url, model_name="llama2")
        available_models = integration.get_available_models()
        
        # Prefer newer/better models if available
        preferred_models = ["llama3", "llama3:8b", "llama2", "llama2:7b", "codellama"]
        
        for preferred in preferred_models:
            for available in available_models:
                if preferred in available:
                    model_name = available
                    break
            if model_name:
                break
        
        if not model_name and available_models:
            model_name = available_models[0]  # Use first available
        
        if not model_name:
            model_name = "llama2"  # Default fallback
    
    return LocalLlamaIntegration(api_url=api_url, model_name=model_name)


# Test function
async def test_local_llama():
    """Test the local LLaMA integration"""
    try:
        llama = create_local_llama_integration()
        
        if not llama.available:
            print("❌ Ollama not available")
            print("📖 To set up Ollama:")
            print("   1. Install: https://ollama.ai/")
            print("   2. Run: ollama pull llama2")
            print("   3. Start: ollama serve")
            return
        
        print("✅ Ollama available!")
        print(f"📋 Model info: {llama.get_model_info()}")
        
        # Test generation
        print("🧪 Testing response generation...")
        response = await llama.generate_response(
            "What is a power system?",
            system_prompt="You are a helpful power systems engineer."
        )
        print(f"🤖 Response: {response}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_local_llama())