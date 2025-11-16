import faiss
import numpy as np
import pickle
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FAISSManager:
    """Centralized FAISS index management for vector storage and retrieval."""
    
    def __init__(self, dimension: int = 768, index_type: str = "flat_ip"):
        """
        Initialize FAISS manager.
        
        Args:
            dimension: Embedding dimension (default: 768 for BGE-small)
            index_type: Type of FAISS index ("flat_ip" for inner product, "flat_l2" for L2)
        """
        self.dimension = dimension
        self.index_type = index_type
        
        # Create appropriate index type
        if index_type == "flat_ip":
            self.index = faiss.IndexFlatIP(dimension)
        else:
            self.index = faiss.IndexFlatL2(dimension)
            
        self.metadata: List[Dict[str, Any]] = []
        logger.info(f"✅ FAISSManager initialized (type: {index_type}, dim: {dimension})")

    def add_embeddings(self, embeddings: np.ndarray, metadata: List[Dict[str, Any]]) -> int:
        """
        Add embeddings to FAISS index.
        
        Args:
            embeddings: numpy array of embeddings (N x dimension)
            metadata: List of metadata dicts for each embedding
            
        Returns:
            Number of embeddings added
        """
        try:
            if len(embeddings) != len(metadata):
                raise ValueError(f"Embeddings count ({len(embeddings)}) != metadata count ({len(metadata)})")
            
            # Normalize for cosine similarity (inner product)
            embeddings_normalized = embeddings.copy().astype(np.float32)
            faiss.normalize_L2(embeddings_normalized)
            
            # Add to index
            self.index.add(embeddings_normalized)
            self.metadata.extend(metadata)
            
            logger.info(f"✅ Added {len(embeddings)} embeddings to index (total: {self.index.ntotal})")
            return len(embeddings)
        except Exception as e:
            logger.error(f"❌ Error adding embeddings: {e}")
            raise

    def search(self, query_embedding: np.ndarray, k: int = 5) -> Tuple[List[float], List[int]]:
        """
        Search for top-k similar chunks.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            Tuple of (distances, indices)
        """
        try:
            if self.index.ntotal == 0:
                logger.warning("⚠️ Index is empty, no results to return")
                return [], []
            
            # Ensure k doesn't exceed index size
            k = min(k, self.index.ntotal)
            
            # Normalize query
            query_normalized = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_normalized)
            
            # Search
            distances, indices = self.index.search(query_normalized, k)
            
            logger.debug(f"✓ Search completed: found {len(indices[0])} results")
            return distances[0].tolist(), indices[0].tolist()
        except Exception as e:
            logger.error(f"❌ Error searching: {e}")
            raise

    def get_metadata(self, indices: List[int]) -> List[Dict[str, Any]]:
        """
        Get metadata for given indices.
        
        Args:
            indices: List of indices
            
        Returns:
            List of metadata dicts
        """
        try:
            results = []
            for idx in indices:
                if 0 <= idx < len(self.metadata):
                    results.append(self.metadata[idx])
            return results
        except Exception as e:
            logger.error(f"❌ Error getting metadata: {e}")
            raise

    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """Get all metadata from index."""
        return self.metadata.copy()

    def save_index(self, path: Path) -> None:
        """
        Save FAISS index to disk.
        
        Args:
            path: Directory path to save index
        """
        try:
            path = Path(path)
            path.mkdir(parents=True, exist_ok=True)
            
            index_file = path / "index.faiss"
            metadata_file = path / "metadata.pkl"
            
            # Write index
            faiss.write_index(self.index, str(index_file))
            logger.debug(f"  ✓ Index saved to {index_file}")
            
            # Write metadata
            with open(metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.debug(f"  ✓ Metadata saved to {metadata_file}")
            
            logger.info(f"✅ Index saved to {path} ({self.index.ntotal} vectors)")
        except Exception as e:
            logger.error(f"❌ Error saving index: {e}")
            raise

    def load_index(self, path: Path) -> None:
        """
        Load FAISS index from disk.
        
        Args:
            path: Directory path to load index from
        """
        try:
            path = Path(path)
            index_file = path / "index.faiss"
            metadata_file = path / "metadata.pkl"
            
            if not index_file.exists() or not metadata_file.exists():
                raise FileNotFoundError(f"Index files not found in {path}")
            
            # Load index
            self.index = faiss.read_index(str(index_file))
            logger.debug(f"  ✓ Index loaded from {index_file}")
            
            # Load metadata
            with open(metadata_file, 'rb') as f:
                self.metadata = pickle.load(f)
            logger.debug(f"  ✓ Metadata loaded from {metadata_file}")
            
            logger.info(f"✅ Index loaded from {path} ({self.index.ntotal} vectors)")
        except Exception as e:
            logger.error(f"❌ Error loading index: {e}")
            raise

    def merge_indices(self, other_manager: 'FAISSManager') -> None:
        """
        Merge another FAISS index with current.
        
        Args:
            other_manager: Another FAISSManager instance to merge
        """
        try:
            if other_manager.index.ntotal == 0:
                logger.warning("⚠️ Other index is empty, nothing to merge")
                return
            
            # Get all vectors from other index
            other_vectors = other_manager.index.reconstruct_n(0, other_manager.index.ntotal)
            
            # Add to current index
            self.index.add(other_vectors)
            self.metadata.extend(other_manager.metadata)
            
            logger.info(f"✅ Indices merged successfully (total: {self.index.ntotal} vectors)")
        except Exception as e:
            logger.error(f"❌ Error merging indices: {e}")
            raise

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "metadata_count": len(self.metadata)
        }

    def clear_index(self) -> None:
        """Clear all data from index."""
        try:
            # Recreate empty index
            if self.index_type == "flat_ip":
                self.index = faiss.IndexFlatIP(self.dimension)
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
            
            self.metadata = []
            logger.info("✅ Index cleared")
        except Exception as e:
            logger.error(f"❌ Error clearing index: {e}")
            raise