"""
Embedding Cache Module
Caches embeddings to reduce redundant API calls
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Cache for storing and retrieving embeddings."""
    
    def __init__(self, cache_dir: Path = Path("./embedding_cache")):
        """Initialize embedding cache."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache: Dict[str, np.ndarray] = {}
        logger.info(f"✅ EmbeddingCache initialized at {self.cache_dir}")
    
    def _get_hash(self, text: str) -> str:
        """Generate hash for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from cache."""
        try:
            text_hash = self._get_hash(text)
            
            # Check memory cache first
            if text_hash in self.memory_cache:
                logger.debug(f"✓ Cache hit (memory): {text_hash[:8]}")
                return self.memory_cache[text_hash]
            
            # Check disk cache
            cache_file = self.cache_dir / f"{text_hash}.npy"
            if cache_file.exists():
                embedding = np.load(cache_file)
                self.memory_cache[text_hash] = embedding
                logger.debug(f"✓ Cache hit (disk): {text_hash[:8]}")
                return embedding
            
            logger.debug(f"✗ Cache miss: {text_hash[:8]}")
            return None
        except Exception as e:
            logger.error(f"❌ Cache retrieval error: {e}")
            return None
    
    def set(self, text: str, embedding: np.ndarray) -> bool:
        """Store embedding in cache."""
        try:
            text_hash = self._get_hash(text)
            
            # Store in memory cache
            self.memory_cache[text_hash] = embedding
            
            # Store on disk
            cache_file = self.cache_dir / f"{text_hash}.npy"
            np.save(cache_file, embedding)
            
            logger.debug(f"✓ Cached embedding: {text_hash[:8]}")
            return True
        except Exception as e:
            logger.error(f"❌ Cache storage error: {e}")
            return False
    
    def get_batch(self, texts: list) -> Dict[str, Optional[np.ndarray]]:
        """Get multiple embeddings from cache."""
        results = {}
        for text in texts:
            results[text] = self.get(text)
        return results
    
    def set_batch(self, texts: list, embeddings: list) -> int:
        """Store multiple embeddings in cache."""
        count = 0
        for text, embedding in zip(texts, embeddings):
            if self.set(text, embedding):
                count += 1
        return count
    
    def clear_memory_cache(self) -> None:
        """Clear in-memory cache."""
        self.memory_cache.clear()
        logger.info("✅ Memory cache cleared")
    
    def clear_disk_cache(self) -> int:
        """Clear disk cache."""
        try:
            count = 0
            for cache_file in self.cache_dir.glob("*.npy"):
                cache_file.unlink()
                count += 1
            logger.info(f"✅ Cleared {count} cached embeddings from disk")
            return count
        except Exception as e:
            logger.error(f"❌ Failed to clear disk cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            disk_files = list(self.cache_dir.glob("*.npy"))
            total_size = sum(f.stat().st_size for f in disk_files)
            
            return {
                "memory_cache_size": len(self.memory_cache),
                "disk_cache_size": len(disk_files),
                "disk_cache_bytes": total_size,
                "disk_cache_mb": total_size / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"❌ Failed to get cache stats: {e}")
            return {}
