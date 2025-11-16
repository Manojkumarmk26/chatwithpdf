"""
Search Result Reranking Module
Uses cross-encoder to rerank search results for better relevance
"""

import logging
from typing import List, Dict, Tuple, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class SearchReranker:
    """Reranks search results using cross-encoder model."""
    
    def __init__(self):
        """Initialize reranker."""
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
            logger.info("✅ SearchReranker initialized with cross-encoder model")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load cross-encoder: {e}")
            self.model = None
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Tuple[int, str, float]]:
        """
        Rerank documents by relevance to query.
        
        Args:
            query: Search query
            documents: List of documents to rerank
            top_k: Return only top k results
            
        Returns:
            List of (index, document, score) tuples
        """
        if not self.model or not documents:
            logger.warning("⚠️ Reranker unavailable or no documents")
            return [(i, doc, 0.0) for i, doc in enumerate(documents)]
        
        try:
            # Create query-document pairs
            pairs = [[query, doc] for doc in documents]
            
            # Get scores
            scores = self.model.predict(pairs)
            
            # Create results with original indices
            results = [
                (i, documents[i], float(scores[i]))
                for i in range(len(documents))
            ]
            
            # Sort by score descending
            results.sort(key=lambda x: x[2], reverse=True)
            
            # Return top k if specified
            if top_k:
                results = results[:top_k]
            
            logger.info(f"✅ Reranked {len(documents)} documents (top {len(results)})")
            return results
        except Exception as e:
            logger.error(f"❌ Reranking failed: {e}")
            return [(i, doc, 0.0) for i, doc in enumerate(documents)]
    
    def rerank_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks by relevance to query.
        
        Args:
            query: Search query
            chunks: List of chunk dicts with 'content' key
            top_k: Return only top k results
            
        Returns:
            Reranked chunks with 'rerank_score' added
        """
        if not chunks:
            return []
        
        try:
            # Extract content
            contents = [chunk.get('content', '') for chunk in chunks]
            
            # Rerank
            results = self.rerank(query, contents, top_k=None)
            
            # Map back to chunks
            reranked_chunks = []
            for orig_idx, content, score in results:
                chunk = chunks[orig_idx].copy()
                chunk['rerank_score'] = score
                reranked_chunks.append(chunk)
            
            # Return top k if specified
            if top_k:
                reranked_chunks = reranked_chunks[:top_k]
            
            logger.info(f"✅ Reranked {len(chunks)} chunks (top {len(reranked_chunks)})")
            return reranked_chunks
        except Exception as e:
            logger.error(f"❌ Chunk reranking failed: {e}")
            # Return original chunks with zero scores
            for chunk in chunks:
                chunk['rerank_score'] = 0.0
            return chunks[:top_k] if top_k else chunks
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the reranker model."""
        if self.model:
            return {
                "model_name": "cross-encoder/ms-marco-MiniLM-L-12-v2",
                "status": "loaded",
                "max_length": 512
            }
        else:
            return {
                "model_name": "cross-encoder/ms-marco-MiniLM-L-12-v2",
                "status": "not_loaded",
                "error": "Model failed to load"
            }
