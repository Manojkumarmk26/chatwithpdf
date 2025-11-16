import logging
from typing import List, Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class SemanticRetriever:
    def __init__(self, embedder, faiss_manager, threshold: float = 0.5):
        """
        Initialize the semantic retriever.
        
        Args:
            embedder: Text embedding model
            faiss_manager: FAISS index manager
            threshold: Minimum similarity threshold for retrieval (0-1)
        """
        self.embedder = embedder
        self.faiss_manager = faiss_manager
        self.threshold = max(0.0, min(1.0, threshold))  # Ensure threshold is between 0 and 1

    def retrieve_chunks(
        self, 
        query: str, 
        k: int = 5, 
        file_ids: Optional[List[str]] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks with filtering and scoring.
        
        Args:
            query: The search query
            k: Maximum number of results to return
            file_ids: Optional list of file IDs to filter by
            min_score: Minimum similarity score (0-1) for results
            
        Returns:
            List of dictionaries containing chunk data and metadata
        """
        min_score = min_score or self.threshold
        
        try:
            # Embed query
            query_embedding = self.embedder.embed_text(query)
            
            # Search FAISS with more results for better filtering
            max_results = min(k * 3, 50)  # Get more results for better filtering
            distances, indices = self.faiss_manager.search(query_embedding, k=max_results)
            
            # Process and filter results
            retrieved_chunks = []
            seen_chunks = set()  # To avoid duplicate chunks
            
            for distance, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.faiss_manager.metadata):
                    continue
                    
                metadata = self.faiss_manager.metadata[idx]
                
                # Filter by file_ids if specified
                if file_ids and metadata.get("file_id") not in file_ids:
                    continue
                
                # Calculate similarity score (convert distance to similarity)
                similarity = float(1.0 / (1.0 + distance))
                
                # Filter by minimum score
                if similarity < min_score:
                    continue
                
                # Create chunk data
                chunk_id = metadata.get("chunk_id") or str(idx)
                
                # Skip duplicates
                if chunk_id in seen_chunks:
                    continue
                seen_chunks.add(chunk_id)
                
                # Add to results
                retrieved_chunks.append({
                    "content": metadata.get("content", ""),
                    "metadata": metadata,
                    "similarity": similarity,
                    "file_id": metadata.get("file_id"),
                    "filename": metadata.get("filename", "Unknown"),
                    "chunk_id": chunk_id,
                    "distance": float(distance)
                })
            
            # Sort by similarity (highest first)
            retrieved_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Return top-k results
            return retrieved_chunks[:k]
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to retrieve chunks: {str(e)}")