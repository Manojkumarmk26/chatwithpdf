"""
Integration Manager
Centralized management of all system components
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from embedding.faiss_manager import FAISSManager
from embedding.cache import EmbeddingCache
from embedding.reranker import SearchReranker
from session_manager import SessionManager
from error_handler import ErrorHandler, retry_with_backoff, STANDARD_RETRY
from document_processor.table_extractor import TableExtractor

logger = logging.getLogger(__name__)

class IntegrationManager:
    """Centralized management of all system components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize integration manager."""
        self.config = config or {}
        
        # Initialize components
        self.faiss_managers: Dict[str, FAISSManager] = {}
        self.embedding_cache = EmbeddingCache(
            Path(self.config.get('cache_dir', './embedding_cache'))
        )
        self.reranker = SearchReranker()
        self.session_manager = SessionManager(
            Path(self.config.get('sessions_dir', './sessions'))
        )
        self.table_extractor = TableExtractor()
        self.error_handler = ErrorHandler()
        
        logger.info("✅ IntegrationManager initialized")
    
    def get_faiss_manager(self, chat_id: str) -> FAISSManager:
        """Get or create FAISS manager for session."""
        if chat_id not in self.faiss_managers:
            self.faiss_managers[chat_id] = FAISSManager(
                dimension=int(self.config.get('embedding_dim', 768)),
                index_type=self.config.get('index_type', 'flat_ip')
            )
        return self.faiss_managers[chat_id]
    
    def save_session_state(self, chat_id: str) -> bool:
        """Save current session state."""
        try:
            session_data = {
                'chat_id': chat_id,
                'faiss_stats': self.get_faiss_manager(chat_id).get_index_stats() if chat_id in self.faiss_managers else {},
                'cache_stats': self.embedding_cache.get_cache_stats()
            }
            return self.session_manager.save_session(chat_id, session_data)
        except Exception as e:
            logger.error(f"❌ Failed to save session state: {e}")
            return False
    
    def load_session_state(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Load session state."""
        try:
            return self.session_manager.load_session(chat_id)
        except Exception as e:
            logger.error(f"❌ Failed to load session state: {e}")
            return None
    
    @retry_with_backoff(STANDARD_RETRY)
    def extract_and_cache_tables(self, text: str) -> List[Dict[str, Any]]:
        """Extract tables and cache results."""
        try:
            tables = self.table_extractor.extract_tables_from_text(text)
            logger.info(f"✅ Extracted {len(tables)} tables")
            return tables
        except Exception as e:
            logger.error(f"❌ Table extraction failed: {e}")
            return []
    
    def rerank_search_results(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Rerank search results."""
        try:
            reranked = self.reranker.rerank_chunks(query, chunks, top_k)
            logger.info(f"✅ Reranked {len(chunks)} chunks")
            return reranked
        except Exception as e:
            logger.error(f"❌ Reranking failed: {e}")
            return chunks[:top_k] if top_k else chunks
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "faiss_managers": len(self.faiss_managers),
            "embedding_cache": self.embedding_cache.get_cache_stats(),
            "reranker": self.reranker.get_model_info(),
            "sessions": len(self.session_manager.list_sessions())
        }
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # Save all sessions
            for chat_id in self.faiss_managers.keys():
                self.save_session_state(chat_id)
            
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
