from sentence_transformers import CrossEncoder
import logging
from typing import List, Union, Dict, Any, Optional

logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"):
        """Initialize the reranker with a cross-encoder model.
        
        Args:
            model_name: Name or path of the cross-encoder model to use.
        """
        try:
            self.model = CrossEncoder(model_name, max_length=512)
            logger.info(f"Loaded reranker model: {model_name}")
        except Exception as e:
            logger.warning(f"Could not load cross-encoder '{model_name}': {e}")
            self.model = None

    def rerank_passages(
        self, 
        query: str, 
        passages: List[Union[Dict[str, Any], str, object]], 
        top_k: int = 3
    ) -> List[Any]:
        """Rerank passages using cross-encoder with graceful fallback.
        
        Args:
            query: The search query string.
            passages: List of passages to rerank. Can be:
                - Document objects (with page_content and metadata)
                - Dictionaries with 'content' or 'page_content' keys
                - Raw strings
            top_k: Maximum number of results to return.
            
        Returns:
            List of reranked passages in the same format as input.
        """
        if not passages or self.model is None:
            return passages[:top_k]
        
        try:
            # Extract passage texts while preserving original format
            passage_data = []
            for i, passage in enumerate(passages):
                if hasattr(passage, 'page_content'):  # Document object
                    passage_data.append({
                        'original': passage,
                        'text': passage.page_content,
                        'type': 'document',
                        'metadata': getattr(passage, 'metadata', {})
                    })
                elif isinstance(passage, dict):  # Dictionary
                    passage_data.append({
                        'original': passage,
                        'text': passage.get('page_content', passage.get('content', str(passage))),
                        'type': 'dict',
                        'metadata': passage.get('metadata', {})
                    })
                else:  # String or other
                    passage_data.append({
                        'original': passage,
                        'text': str(passage),
                        'type': 'string',
                        'metadata': {}
                    })
            
            # Skip reranking if no valid passages
            if not passage_data:
                return passages[:top_k]
            
            # Create query-passage pairs for reranking
            pairs = [[query, item['text']] for item in passage_data]
            
            # Get scores from cross-encoder
            scores = self.model.predict(pairs)
            
            # Sort passages by score (highest first)
            scored_passages = list(zip(passage_data, scores))
            scored_passages.sort(key=lambda x: x[1], reverse=True)
            
            # Convert back to original format
            results = []
            for item, _ in scored_passages[:top_k]:
                if item['type'] == 'document':
                    # Return document object
                    from langchain_core.documents import Document
                    results.append(Document(
                        page_content=item['original'].page_content,
                        metadata=item['original'].metadata
                    ))
                else:
                    # Return original object
                    results.append(item['original'])
            
            return results
            
        except Exception as e:
            logger.warning(f"Error during reranking: {e}. Using original order.")
            return passages[:top_k]
