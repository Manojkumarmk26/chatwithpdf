import requests
import json
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class OllamaModel:
    """Ultra-optimized Ollama model for fast responses on simple queries."""
    
    def __init__(
        self, 
        model_name: str = "mistral",
        base_url: str = "http://localhost:11434",
        timeout: int = 60  # REDUCED from 300 to 60 seconds
    ):
        """Initialize Ollama model client.
        
        Args:
            model_name: Ollama model name (mistral, neural-chat, orca-mini)
            base_url: Ollama server URL
            timeout: Request timeout in seconds (60 for fast responses)
        """
        self.model_name = model_name
        self.base_url = base_url
        self.timeout = timeout
        self.api_endpoint = f"{base_url}/api/generate"
        
        logger.info("=" * 60)
        logger.info(f"🔄 Initializing Ollama Model: {model_name}")
        logger.info(f"📍 Server: {base_url}")
        logger.info(f"⏱️  Timeout: {timeout}s (optimized for speed)")
        logger.info("=" * 60)
        
        # Test connection
        if not self._test_connection():
            error_msg = (
                f"\n❌ ERROR: Cannot connect to Ollama at {base_url}\n"
                f"\n📋 SOLUTION:\n"
                f"1. Make sure Ollama is running:\n"
                f"   ollama serve\n"
                f"2. Check model is available:\n"
                f"   ollama pull mistral\n"
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        
        logger.info("✅ Connected to Ollama successfully!")
    
    def _test_connection(self) -> bool:
        """Test if Ollama server is running."""
        try:
            logger.info("🔍 Testing Ollama connection...")
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 128,  # REDUCED from 256
        temperature: float = 0.5,  # REDUCED from 0.7 for faster generation
        top_p: float = 0.8  # REDUCED from 0.9
    ) -> str:
        """Generate text FAST using Ollama.
        
        Optimizations:
        - Shorter prompts (max 1000 chars)
        - Fewer tokens (max 128)
        - Lower temperature (0.5)
        - Minimal parameters
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens (128 for speed)
            temperature: Randomness (0.5 for fast)
            top_p: Nucleus sampling (0.8)
            
        Returns:
            Generated text or error message
        """
        try:
            # FAST: Quick validation
            if not prompt or not isinstance(prompt, str):
                return "Invalid prompt"
            
            # FAST: Aggressive prompt truncation
            if len(prompt) > 1000:
                prompt = prompt[:1000]
            
            # FAST: Clamp parameters for speed
            temperature = max(0.1, min(0.8, temperature))
            max_tokens = min(max_tokens, 128)  # Max 128 tokens for speed
            
            logger.info(f"🚀 FAST generation: {self.model_name}")
            
            # FAST: Minimal payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
                "top_k": 20,  # REDUCED from 40
                "repeat_penalty": 1.0,  # REDUCED from 1.1
                "num_thread": 8
            }
            
            # No timeout for API requests
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=None  # No timeout at all
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Error: {response.status_code}")
                return "Error generating response"
            
            # FAST: Extract answer
            result = response.json()
            answer = result.get("response", "").strip()
            
            return answer if answer else "Unable to generate response"
            
        except requests.exceptions.Timeout:
            logger.error("⏱️ Timeout - try simpler question")
            return "Request timeout. Try a simpler question."
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to Ollama")
            return "Cannot connect to Ollama"
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return f"Error: {str(e)[:50]}"
    
    
    def answer_question(
        self,
        question: str,
        context: str = "",
        max_tokens: int = 128  # REDUCED from 256
    ) -> str:
        """Answer question FAST.
        
        Optimizations:
        - Minimal context (max 800 chars)
        - Short max_tokens (128)
        - Fast temperature (0.5)
        
        Args:
            question: Question to answer
            context: Optional context (limited)
            max_tokens: Max response (128)
            
        Returns:
            Answer
        """
        try:
            # FAST: Build minimal prompt
            if context:
                # FAST: Aggressive context limit
                context = context[:800]  # REDUCED from 1500
                prompt = f"""Context:
{context}

Q: {question}

A:"""
            else:
                # FAST: Direct question
                prompt = f"""Q: {question}

A:"""
            
            logger.info(f"💬 FAST answer: {question[:30]}...")
            
            return self.generate_text(
                prompt,
                max_tokens=max_tokens,
                temperature=0.5
            )
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return "Error answering"

