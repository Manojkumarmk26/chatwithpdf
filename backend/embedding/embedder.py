from sentence_transformers import SentenceTransformer
import numpy as np
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, model_name="BAAI/bge-base-en-v1.5"):
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for single text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def embed_batch(self, texts: list) -> np.ndarray:
        """Generate embeddings for batch of texts"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()
