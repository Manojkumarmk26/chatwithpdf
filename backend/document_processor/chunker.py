import re
from typing import List
import logging

logger = logging.getLogger(__name__)

class SemanticChunker:
    def __init__(self, chunk_size=512, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """Split text into semantic chunks maintaining context"""
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # Skip very short paragraphs
            if len(para.strip()) < 10:
                continue
            
            # If adding para would exceed chunk_size, save current chunk
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Handle overlap
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                # Add overlap from previous chunk
                overlap_text = " ".join(chunks[i-1].split()[-5:])
                chunk = overlap_text + " " + chunk
            overlapped_chunks.append(chunk)
        
        return overlapped_chunks

    def get_chunks(self, content: str) -> List[dict]:
        """Get chunks with metadata"""
        chunks = self.chunk_text(content)
        return [
            {
                "chunk_id": f"chunk_{i}",
                "content": chunk,
                "index": i,
                "length": len(chunk)
            }
            for i, chunk in enumerate(chunks)
        ]