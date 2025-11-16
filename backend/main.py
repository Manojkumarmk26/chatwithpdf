# ============= backend/main.py (OPTIMIZED - MEMORY EFFICIENT) =============

import os
import logging
import asyncio
import pickle
import json
import uuid
import time
import math
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, List, Optional, Any
from contextlib import asynccontextmanager
from collections import defaultdict, OrderedDict

import faiss
import numpy as np
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator, Field
import PyPDF2
from document_processor.ocr_processor import EnhancedOCRProcessor as OCRProcessor
from document_processor.table_extractor import TableExtractor
from document_processor.loader import DocumentLoader

from config import (
    ALLOWED_EXTENSIONS as CONFIG_ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE as CONFIG_MAX_FILE_SIZE,
    CHUNK_SIZE as CONFIG_CHUNK_SIZE,
    CHUNK_OVERLAP as CONFIG_CHUNK_OVERLAP,
    QUERY_CACHE_MAX_SIZE,
    QUERY_CACHE_TTL_SECONDS,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_RETRIEVAL_RESULTS,
    MAX_CONCURRENT_FILE_TASKS
)
# Removed summary-related imports
# ============= LOGGING SETUP =============

def setup_logging():
    """Configure centralized logging with enhanced verbosity."""
    log_format = '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
    logging.basicConfig(
        level=logging.DEBUG,  # Changed from INFO to DEBUG for more detailed logs
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )
    logging.getLogger('filelock').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('document_processor').setLevel(logging.DEBUG)
    logging.getLogger('__main__').setLevel(logging.DEBUG)
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    return logging.getLogger(__name__)

logger = setup_logging()

# ============= CONSTANTS & CONFIG =============

UPLOAD_DIR = Path("./uploads")
INDEX_DIR = Path("./faiss_indices")
VECTOR_STORE_DIR = INDEX_DIR / "vector_store"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = CONFIG_ALLOWED_EXTENSIONS
MAX_FILE_SIZE = CONFIG_MAX_FILE_SIZE
CHUNK_SIZE = CONFIG_CHUNK_SIZE
CHUNK_OVERLAP = CONFIG_CHUNK_OVERLAP
EMBEDDING_DIM = None

logger.info("="*80)
logger.info("🚀 INITIALIZATION STARTED")
logger.info(f"📁 Upload directory: {UPLOAD_DIR}")
logger.info(f"📁 Index directory: {INDEX_DIR}")
logger.info("="*80)

# ============= SHARED RESOURCES =============

class QueryCache:
    """In-memory TTL cache for frequent query responses."""

    def __init__(self, max_size: int, ttl_seconds: int):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._lock = asyncio.Lock()

    def _make_key(
        self,
        chat_id: str,
        query: str,
        selected_file_ids: Optional[List[str]]
    ) -> str:
        normalized_query = query.strip().lower()
        files_key = tuple(sorted(selected_file_ids or []))
        return json.dumps({
            "chat_id": chat_id,
            "query": normalized_query,
            "files": files_key
        }, sort_keys=True)

    async def get(
        self,
        chat_id: str,
        query: str,
        selected_file_ids: Optional[List[str]]
    ) -> Optional[Dict[str, Any]]:
        key = self._make_key(chat_id, query, selected_file_ids)
        async with self._lock:
            cache_entry = self._cache.get(key)
            if not cache_entry:
                return None

            timestamp, value = cache_entry
            if time.time() - timestamp > self.ttl_seconds:
                self._cache.pop(key, None)
                return None

            # Move to end to denote recent use
            self._cache.move_to_end(key)
            return value

    async def set(
        self,
        chat_id: str,
        query: str,
        selected_file_ids: Optional[List[str]],
        value: Dict[str, Any]
    ) -> None:
        key = self._make_key(chat_id, query, selected_file_ids)
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (time.time(), value)

            # Evict oldest entries beyond max size
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()

    async def invalidate_session(self, chat_id: str) -> None:
        async with self._lock:
            keys_to_remove = [key for key in self._cache.keys() if json.loads(key).get("chat_id") == chat_id]
            for key in keys_to_remove:
                self._cache.pop(key, None)


class SharedResources:
    """Memory-efficient resource management."""
    
    def __init__(self):
        self.faiss_indices: Dict[str, faiss.IndexFlatIP] = {}
        self.metadata_dict: Dict[str, List[Dict]] = {}
        self.chat_document_mapping: Dict[str, List[str]] = {}
        self.lock = asyncio.Lock()
        self.embedder = None
        self.query_cache = QueryCache(
            max_size=QUERY_CACHE_MAX_SIZE,
            ttl_seconds=QUERY_CACHE_TTL_SECONDS
        )
        
        logger.info("✅ SharedResources initialized")
    
    async def acquire_lock(self):
        """Acquire resource lock."""
        await self.lock.acquire()
    
    def release_lock(self):
        """Release resource lock."""
        if self.lock.locked():
            self.lock.release()

shared_resources = SharedResources()

# ============= EMBEDDER INITIALIZATION =============

def get_embedder():
    """Get singleton embedder - LIGHTWEIGHT VERSION."""
    if shared_resources.embedder is None:
        logger.info("📚 Initializing lightweight embedder...")
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use lightweight model to save memory
            shared_resources.embedder = SentenceTransformer(
                'BAAI/bge-small-en-v1.5',  # Smaller model (~100MB vs 500MB)
                device='cpu'
            )
            
            global EMBEDDING_DIM
            EMBEDDING_DIM = shared_resources.embedder.get_sentence_embedding_dimension()
            logger.info(f"✅ Embedder initialized. Dimension: {EMBEDDING_DIM}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embedder: {e}")
            raise
    return shared_resources.embedder

# ============= TEXT EXTRACTION (PyPDF2 + OCR) =============

def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, List[str]]:
    """Extract text from PDF using PyPDF2 first, then OCR for scanned pages.
    
    Returns:
        Tuple[text: str, errors: List[str]]
    """
    logger.info(f"📄 Starting text extraction from PDF: {pdf_path.name}")
    errors = []
    text = ""
    page_count = 0
    
    try:
        # First, try PyPDF2 extraction
        logger.info("  [1/2] Attempting PyPDF2 text extraction...")
        
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            page_count = len(pdf_reader.pages)
            logger.info(f"  📋 PDF has {page_count} pages")
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                        logger.debug(f"  ✓ Page {page_num + 1}: {len(page_text)} chars")
                except Exception as e:
                    logger.warning(f"  ⚠️ Page {page_num + 1} extraction failed: {e}")
                    errors.append(f"Page {page_num + 1} failed")
        
        # If no text extracted, use OCR
        if not text.strip():
            logger.info("  [2/2] No text found, attempting OCR extraction...")
            try:
                ocr_processor = OCRProcessor()
                ocr_result = ocr_processor.extract_from_pdf_images(str(pdf_path))
                text = ocr_result.get("text", "")
                logger.info(f"  ✓ OCR extraction complete: {len(text)} chars")
                if text.strip():
                    logger.info("  ✅ Successfully extracted text using OCR")
                else:
                    logger.warning("  ⚠️ OCR extraction returned empty text")
                    errors.append("OCR extraction failed")
            except Exception as ocr_error:
                logger.error(f"  ❌ OCR extraction failed: {ocr_error}")
                errors.append(f"OCR failed: {str(ocr_error)}")
        else:
            logger.info(f"  ✅ PyPDF2 extraction successful: {len(text)} chars")
        
        logger.info(f"✅ Extraction complete: {len(text)} chars")
        return text, errors
    
    except Exception as e:
        logger.error(f"❌ Critical error in PDF extraction: {e}")
        errors.append(f"Critical error: {str(e)}")
        return "", errors

# ============= TEXT CHUNKING (OPTIMIZED) =============

def improved_semantic_text_chunking(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """Split text into semantic chunks efficiently.
    
    Args:
        text: Input text
        chunk_size: Tokens per chunk
        chunk_overlap: Token overlap
    
    Returns:
        List of chunks
    """
    logger.info(f"🔪 Starting semantic chunking (size={chunk_size}, overlap={chunk_overlap})...")
    
    if not text or not text.strip():
        logger.warning("  ⚠️ Empty text provided")
        return []
    
    # Split by sentences for better semantic boundaries
    sentences = text.split('. ')
    logger.info(f"  📝 Text split into {len(sentences)} sentences")
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Approximate: 1 token ≈ 4 characters
        current_size = len(current_chunk) // 4
        sentence_size = len(sentence) // 4
        
        if current_size + sentence_size > chunk_size:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                logger.debug(f"  ✓ Chunk: {len(current_chunk)//4} tokens")
            current_chunk = sentence
        else:
            current_chunk += ". " + sentence if current_chunk else sentence
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        logger.debug(f"  ✓ Final chunk: {len(current_chunk)//4} tokens")
    
    logger.info(f"✅ Chunking complete: {len(chunks)} chunks created")
    return chunks

# ============= FAISS INDEX MANAGEMENT =============

def load_faiss_index(chat_id: str) -> Tuple[Optional[faiss.IndexFlatIP], Optional[List[Dict]]]:
    """Load FAISS index and metadata."""
    logger.info(f"📂 Loading FAISS index for chat_id: {chat_id}")
    
    index_path = VECTOR_STORE_DIR / f"faiss_index_{chat_id}.bin"
    metadata_path = VECTOR_STORE_DIR / f"metadata_{chat_id}.pickle"
    
    if not index_path.exists() or not metadata_path.exists():
        logger.warning(f"  ⚠️ Index or metadata files not found")
        return None, None
    
    try:
        logger.debug(f"  Loading index from {index_path.name}...")
        index = faiss.read_index(str(index_path))
        logger.debug(f"  ✓ Index loaded: {index.ntotal} vectors")
        
        logger.debug(f"  Loading metadata from {metadata_path.name}...")
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        logger.debug(f"  ✓ Metadata loaded: {len(metadata)} entries")
        
        logger.info(f"✅ FAISS index loaded successfully")
        return index, metadata
    
    except Exception as e:
        logger.error(f"❌ Failed to load FAISS index: {e}")
        return None, None

def add_to_faiss_index(
    filename: str,
    text_chunks: List[str],
    chat_id: str
) -> bool:
    """Add text chunks to FAISS index atomically."""
    logger.info(f"➕ Adding {len(text_chunks)} chunks to FAISS index...")
    logger.info(f"   Filename: {filename}")
    
    if not text_chunks:
        logger.warning("  ⚠️ No chunks provided")
        return False
    
    try:
        # Get embedder
        embedder = get_embedder()
        logger.info(f"  🔢 Encoding {len(text_chunks)} chunks...")
        
        # Encode in batches to save memory
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(text_chunks), batch_size):
            batch = text_chunks[i:i+batch_size]
            batch_embeddings = embedder.encode(batch, convert_to_numpy=True)
            all_embeddings.extend(batch_embeddings)
            logger.debug(f"  ✓ Encoded batch {i//batch_size + 1}/{(len(text_chunks)-1)//batch_size + 1}")
        
        embeddings = np.array(all_embeddings, dtype=np.float32)
        logger.debug(f"  ✓ Embeddings created: shape {embeddings.shape}")
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        logger.debug(f"  ✓ Embeddings normalized")
        
        # Create or load index
        index_path = VECTOR_STORE_DIR / f"faiss_index_{chat_id}.bin"
        metadata_path = VECTOR_STORE_DIR / f"metadata_{chat_id}.pickle"
        
        if index_path.exists():
            logger.info(f"  📂 Loading existing index...")
            index, metadata = load_faiss_index(chat_id)
            if index is None:
                logger.warning("  ⚠️ Creating new index")
                index = faiss.IndexFlatIP(EMBEDDING_DIM)
                metadata = []
        else:
            logger.info(f"  ✨ Creating new FAISS index...")
            index = faiss.IndexFlatIP(EMBEDDING_DIM)
            metadata = []
        
        # Add embeddings
        logger.info(f"  ➕ Adding {len(embeddings)} embeddings...")
        index.add(embeddings)
        logger.debug(f"  ✓ Index now contains {index.ntotal} vectors")
        
        # Create metadata
        chunk_metadata = []
        for idx, chunk in enumerate(text_chunks):
            chunk_metadata.append({
                'chunk_id': f"{chat_id}_chunk_{len(metadata) + idx}",
                'filename': filename,
                'chat_id': chat_id,
                'content': chunk[:500],  # Store only first 500 chars to save memory
                'timestamp': datetime.now().isoformat(),
                'chunk_index': len(metadata) + idx
            })
        
        metadata.extend(chunk_metadata)
        logger.debug(f"  ✓ Metadata updated: {len(metadata)} entries")
        
        # ATOMIC PERSISTENCE
        logger.info(f"  💾 Atomically persisting index and metadata...")
        temp_index_path = index_path.with_suffix('.tmp.bin')
        temp_metadata_path = metadata_path.with_suffix('.tmp.pickle')
        
        try:
            faiss.write_index(index, str(temp_index_path))
            logger.debug(f"  ✓ Temp index written")
            
            with open(temp_metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            logger.debug(f"  ✓ Temp metadata written")
            
            # Atomic replace
            temp_index_path.replace(index_path)
            temp_metadata_path.replace(metadata_path)
            logger.info(f"  ✓ Files atomically replaced")
            
        except Exception as e:
            logger.error(f"  ❌ Failed to persist: {e}")
            temp_index_path.unlink(missing_ok=True)
            temp_metadata_path.unlink(missing_ok=True)
            raise
        
        # Update in-memory cache
        shared_resources.faiss_indices[chat_id] = index
        shared_resources.metadata_dict[chat_id] = metadata
        
        logger.info(f"✅ Successfully added chunks to FAISS")
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to add chunks: {e}")
        return False

# ============= RETRIEVAL =============

def get_filenames_from_file_ids(session_id: str, file_ids: List[str]) -> List[str]:
    """Map file_ids to filenames from session data."""
    if session_id not in sessions:
        return []
    
    filenames = []
    for file_record in sessions[session_id].files:
        if file_record.get("file_id") in file_ids:
            filenames.append(file_record.get("filename"))
    
    return filenames

def retrieve_all_chunks_for_files(
    chat_id: str,
    selected_files: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Retrieve ALL chunks from selected files for comprehensive analysis."""
    logger.info(f"📚 Retrieving ALL chunks for comprehensive analysis...")
    
    try:
        logger.info(f"  📂 Loading FAISS index for session {chat_id}...")
        index, metadata = load_faiss_index(chat_id)
        
        if index is None or metadata is None:
            logger.warning(f"  ⚠️ No index found for session {chat_id}")
            return []
        
        # Collect all chunks from selected files
        all_chunks = []
        for idx, meta in enumerate(metadata):
            if selected_files and meta['filename'] not in selected_files:
                continue
            
            chunk_info = {
                'content': meta['content'],
                'filename': meta['filename'],
                'chunk_id': meta['chunk_id'],
                'page': meta.get('page', 'unknown'),
                'chunk_index': idx
            }
            
            all_chunks.append(chunk_info)
        
        logger.info(f"✅ Retrieved {len(all_chunks)} total chunks from {len(set(c['filename'] for c in all_chunks))} files")
        return all_chunks
    
    except Exception as e:
        logger.error(f"❌ Failed to retrieve all chunks: {e}")
        return []

def retrieve_relevant_chunks(
    query: str,
    chat_id: str,
    selected_files: Optional[List[str]] = None,
    top_k: int = 5  # Increased for better context
) -> List[Dict[str, Any]]:
    """Retrieve relevant chunks from FAISS with detailed semantic search."""
    logger.info(f"🔍 Detailed Vector Search for query: '{query[:50]}...'")
    
    try:
        embedder = get_embedder()
        
        logger.info("  📊 Encoding query with sentence transformer...")
        query_embedding = embedder.encode([query], convert_to_numpy=True)[0]
        query_embedding = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_embedding)
        logger.debug(f"  ✓ Query encoded - Dimension: {query_embedding.shape}")
        
        logger.info(f"  📂 Loading FAISS index for session {chat_id}...")
        index, metadata = load_faiss_index(chat_id)
        
        if index is None or metadata is None:
            logger.warning(f"  ⚠️ No index found for session {chat_id}")
            return []
        
        logger.info(f"  🔎 Semantic search across {index.ntotal} vectors...")
        # Search for more candidates to filter and rank
        search_k = min(top_k * 3, index.ntotal)
        distances, indices = index.search(query_embedding, search_k)
        logger.debug(f"  ✓ Search complete - Found {len(indices[0])} candidates")
        
        # Collect and score chunks
        chunks = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= len(metadata):
                logger.debug(f"    ⚠️ Index {idx} out of bounds")
                continue
            
            meta = metadata[idx]
            
            if selected_files and meta['filename'] not in selected_files:
                logger.debug(f"    ⏭️ Skipping {meta['filename']} (not selected)")
                continue
            
            # Calculate relevance score (0-100)
            relevance_score = float(dist) * 100
            
            chunk_info = {
                'content': meta['content'],
                'filename': meta['filename'],
                'chunk_id': meta['chunk_id'],
                'similarity': float(dist),
                'relevance_score': relevance_score,
                'rank': rank + 1,
                'content_preview': meta['content'][:100] + '...' if len(meta['content']) > 100 else meta['content']
            }
            
            chunks.append(chunk_info)
            logger.debug(f"    [{rank+1}] File: {meta['filename'][:30]}... | Score: {relevance_score:.1f}%")
        
        # Sort by similarity and limit to top_k
        chunks.sort(key=lambda x: x['similarity'], reverse=True)
        chunks = chunks[:top_k]
        
        logger.info(f"✅ Retrieved {len(chunks)} most relevant chunks")
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"   [{i}] {chunk['filename']} (Relevance: {chunk['relevance_score']:.1f}%)")
        
        return chunks
    
    except Exception as e:
        logger.error(f"❌ Failed to retrieve: {e}")
        return []

# ============= MODELS & SCHEMAS =============

class UploadResponse(BaseModel):
    status: str
    message: str
    file_id: str
    chunks: int
    text_length: int

class QueryRequest(BaseModel):
    query: str
    chat_id: str
    selected_files: Optional[List[str]] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    query: str

# ============= APP INITIALIZATION =============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup and shutdown."""
    logger.info("\n" + "="*80)
    logger.info("🚀 APP STARTUP")
    logger.info("="*80)
    
    try:
        logger.info("📚 Initializing embedder...")
        get_embedder()
        logger.info("✅ Embedder ready")
        logger.info("="*80)
        logger.info("✅ APP STARTUP COMPLETE")
        logger.info("="*80 + "\n")
    
    except Exception as e:
        logger.error(f"❌ STARTUP FAILED: {e}")
        raise
    
    yield
    
    logger.info("\n" + "="*80)
    logger.info("🛑 APP SHUTDOWN")
    logger.info("="*80)

app = FastAPI(title="Document Analysis Chat", lifespan=lifespan)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3002",  # Frontend development server
        "http://192.168.5.195:3002",  # Local network access
        "http://192.168.5.195:3000"   # In case frontend runs on 3000
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

logger.info("✅ CORS middleware configured")

# ============= SUMMARY ROUTES INTEGRATION =============
try:
    from summary_routes import router as summary_router
    app.include_router(summary_router)
    logger.info("✅ Summary routes integrated")
except Exception as e:
    logger.warning(f"⚠️ Failed to integrate summary routes: {e}")

# ============= ROUTES =============

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    logger.info("❤️  Health check")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "embedding_dim": EMBEDDING_DIM
    }

@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(..., description="List of files to upload"),
    session_id: str = Query(..., description="Chat session ID")
):
    """
    Upload and process documents.
    
    Args:
        files: List of files to upload (PDF only)
        session_id: The chat session ID to associate with these files
    """
    uploaded_files = []
    
    # Process each file
    for file in files:
        logger.info("\n" + "="*80)
        logger.info(f"📤 UPLOAD REQUEST: {file.filename}")
        logger.info("="*80)
        
        try:
            logger.info(f"  ✓ File: {file.filename}")
            logger.info(f"  ✓ Size: {file.size / 1024 / 1024:.2f} MB")
            logger.info(f"  ✓ Session: {session_id}")
            
            # Validate file extension
            ext = Path(file.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=400, detail=f"File type {ext} not allowed. Only PDFs are supported.")
            
            # Validate file size
            if file.size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"File {file.filename} is too large. Max size is {MAX_FILE_SIZE/1024/1024:.1f}MB")
            
            # Save file
            file_path = UPLOAD_DIR / file.filename
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"  ✓ Saved to {file_path}")
            
            # Process the file (extract text, chunk, add to FAISS, etc.)
            text, errors = extract_text_from_pdf(file_path)
            if errors:
                logger.warning(f"  ⚠️ Extraction warnings: {errors}")
            
            if not text or len(text.strip()) < 50:
                raise HTTPException(status_code=400, detail=f"Could not extract sufficient text from {file.filename}")
            
            # Chunk text and add to FAISS
            chunks = improved_semantic_text_chunking(text)
            if not chunks:
                raise HTTPException(status_code=400, detail=f"Could not create text chunks from {file.filename}")
            
            success = add_to_faiss_index(file.filename, chunks, session_id)
            if not success:
                raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}")
            
            # Generate a unique file_id based on filename
            file_id = str(uuid.uuid4())
            
            uploaded_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "size": file.size,
                "chunks": len(chunks),
                "status": "success"
            })
            
            logger.info(f"✅ Successfully processed {file.filename}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to process {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process {file.filename}")
    
    logger.info("="*80)
    logger.info(f"✅ UPLOAD COMPLETE - Processed {len(uploaded_files)} files")
    logger.info("="*80 + "\n")
    
    # Also update the session with the uploaded files
    if session_id in sessions:
        for uploaded_file in uploaded_files:
            sessions[session_id].files.append({
                "file_id": uploaded_file["file_id"],
                "filename": uploaded_file["filename"],
                "selected": True
            })
    
    return {
        "status": "success",
        "session_id": session_id,
        "uploaded_files": uploaded_files,
        "total_files": len(uploaded_files)
    }

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents using RAG."""
    logger.info("\n" + "="*80)
    logger.info(f"❓ QUERY: {request.query}")
    logger.info("="*80)
    
    try:
        logger.info(f"  Chat: {request.chat_id}")
        
        # Retrieve with enhanced vector search (increased top_k for better context)
        logger.info("🔍 Performing detailed vector search...")
        chunks = retrieve_relevant_chunks(
            request.query,
            request.chat_id,
            request.selected_files,
            top_k=15  # Increased from 5 to 15 for more comprehensive context
        )
        
        if not chunks:
            logger.warning("  ⚠️ No chunks found")
            return QueryResponse(
                answer="No relevant information found.",
                sources=[],
                query=request.query
            )
        
        logger.info(f"  ✓ Retrieved {len(chunks)} chunks")
        
        # Build detailed context with source information
        logger.info("📝 Building detailed context with sources...")
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source_info = f"[Source {i}: {chunk['filename']} - Relevance: {chunk['relevance_score']:.1f}%]"
            context_parts.append(f"{source_info}\n{chunk['content']}")
        
        context = "\n\n".join(context_parts)
        logger.debug(f"  Context: {len(context)} chars from {len(chunks)} sources")
        
        # Query Ollama with enhanced prompt
        logger.info("🤖 Querying Ollama with semantic understanding...")
        
        prompt = f"""You are an intelligent document analysis assistant. Based on the provided document context, answer the user's question in detail.

IMPORTANT INSTRUCTIONS:
1. Provide a detailed and comprehensive answer
2. Reference specific information from the documents
3. If information is not in the documents, clearly state that
4. Use the relevance scores to prioritize information from more relevant sources
5. Structure your answer clearly with key points

DOCUMENT CONTEXT:
{context}

USER QUESTION: {request.query}

DETAILED ANSWER:"""
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=None  # No timeout at all
            )
            
            if response.status_code == 200:
                answer = response.json()['response'].strip()
                logger.info(f"  ✓ Answer: {len(answer)} chars")
            else:
                logger.error(f"  ❌ Ollama error: {response.status_code}")
                answer = "Error generating response"
        
        except Exception as e:
            logger.error(f"  ❌ Ollama failed: {e}")
            answer = "Error connecting to model"
        
        logger.info("="*80)
        logger.info(f"✅ QUERY COMPLETE")
        logger.info("="*80 + "\n")
        
        return QueryResponse(
            answer=answer,
            sources=[
                {
                    'filename': chunk['filename'],
                    'similarity': chunk['similarity'],
                    'relevance_score': chunk['relevance_score'],
                    'chunk_id': chunk['chunk_id'],
                    'preview': chunk['content_preview']
                }
                for chunk in chunks
            ],
            query=request.query
        )
    
    except Exception as e:
        logger.error(f"❌ Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= CHAT SESSION MANAGEMENT =============

class ChatSession(BaseModel):
    session_id: str
    created_at: datetime
    messages: List[Dict] = []
    files: List[Dict] = []

sessions: Dict[str, ChatSession] = {}

@app.post("/api/chat/new")
async def create_chat_session():
    """Create a new chat session."""
    try:
        session_id = str(uuid.uuid4())
        new_session = ChatSession(
            session_id=session_id,
            created_at=datetime.now(),
            messages=[],
            files=[]
        )
        sessions[session_id] = new_session
        
        logger.info(f"\n" + "="*80)
        logger.info(f"🆕 New chat session created: {session_id}")
        logger.info(f"Total active sessions: {len(sessions)}")
        logger.info("="*80)
        
        return {
            "status": "success",
            "session_id": session_id,
            "created_at": new_session.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to create chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/chat/{session_id}/select-files")
async def select_files(session_id: str, request: Request):
    """Update selected files for a chat session."""
    try:
        logger.info("\n" + "="*80)
        logger.info("📥 SELECT FILES REQUEST")
        logger.info("="*80)
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Available sessions: {list(sessions.keys())}")
        logger.info(f"Total active sessions: {len(sessions)}")
        
        if session_id not in sessions:
            logger.error(f"❌ Session not found: {session_id}")
            logger.error(f"Available sessions: {list(sessions.keys())}")
            logger.error(f"Total active sessions: {len(sessions)}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Parse the request body
        try:
            body = await request.json()
            logger.info(f"Request body type: {type(body)}")
            logger.info(f"Request body content: {body}")
        except Exception as e:
            logger.error(f"❌ Failed to parse request body: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")
        
        # Handle both formats: direct array or object with selected_files key
        if isinstance(body, list):
            selected_files = [fid for fid in body if fid is not None]  # Filter out None values
            logger.info(f"Processed as direct list: {selected_files}")
        elif isinstance(body, dict) and "selected_files" in body:
            selected_files = [fid for fid in body["selected_files"] if fid is not None]  # Filter out None values
            logger.info(f"Processed from selected_files key: {selected_files}")
        else:
            error_msg = f"Invalid request format. Expected list or dict with 'selected_files' key, got {type(body)}"
            logger.error(f"❌ {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Log if we filtered out any None values
        if len(selected_files) != len(body if isinstance(body, list) else body.get("selected_files", [])):
            logger.warning(f"⚠️ Filtered out None values from selected files")
        
        # Update the session's selected files - mark which files are selected
        for file_record in sessions[session_id].files:
            file_record["selected"] = file_record.get("file_id") in selected_files
        
        logger.info(f"📁 Updated selected files for session {session_id}: {selected_files}")
        logger.info("="*80 + "\n")
        
        return {
            "status": "success",
            "session_id": session_id,
            "selected_files": selected_files
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update selected files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ChatQueryRequest(BaseModel):
    query: str
    session_id: str
    selected_files: Optional[List[str]] = None

# Simple query detection for instant responses
SIMPLE_QUERIES = {
    "hi": "Hello! How can I assist you with your documents today?",
    "hello": "Hi there! Ready to analyze your documents. What would you like to know?",
    "hey": "Hey! I'm here to help with your document queries. What can I do for you?",
    "thanks": "You're welcome! Let me know if you need anything else.",
    "thank you": "You're welcome! Let me know if you need anything else.",
    "ok": "Got it! What would you like to do next?",
    "okay": "Got it! What would you like to do next?"
}

def get_simple_response(query: str) -> Optional[Dict]:
    """Check if the query matches any simple patterns and return a response if found."""
    query_lower = query.lower().strip()
    
    # Check for exact matches
    if query_lower in SIMPLE_QUERIES:
        return {
            "answer": SIMPLE_QUERIES[query_lower],
            "sources": [],
            "query": query
        }
    
    # Check for queries that start with simple greetings
    for prefix in ["hi ", "hello ", "hey ", "thanks ", "thank you "]:
        if query_lower.startswith(prefix):
            return {
                "answer": SIMPLE_QUERIES[prefix.strip()],
                "sources": [],
                "query": query
            }
    
    return None

@app.post("/api/chat/query")
async def chat_query(request: ChatQueryRequest):
    """
    Handle chat query with optimized response flow.
    
    For simple queries (greetings, thanks), returns instant response (50-100ms).
    For complex queries, uses RAG with document context.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"💬 Chat query: {request.query}")
        logger.info(f"   Session: {request.session_id}")
        logger.info(f"   Selected files: {request.selected_files}")
        
        # Check for simple queries first (instant response)
        simple_response = get_simple_response(request.query)
        if simple_response:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"⚡ Simple query handled in {response_time:.0f}ms")
            
            # Log the interaction in session
            if request.session_id in sessions:
                sessions[request.session_id].messages.extend([
                    {
                        "role": "user",
                        "content": request.query,
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "role": "assistant",
                        "content": simple_response["answer"],
                        "sources": [],
                        "timestamp": datetime.now().isoformat()
                    }
                ])
            
            return simple_response
        
        # For non-simple queries, use RAG
        logger.info("🔍 Processing with RAG...")
        
        # Use the existing query_documents function
        response = await query_documents(QueryRequest(
            query=request.query,
            chat_id=request.session_id,
            selected_files=request.selected_files
        ))
        
        # Log the interaction in session
        if request.session_id in sessions:
            sessions[request.session_id].messages.extend([
                {
                    "role": "user",
                    "content": request.query,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "role": "assistant",
                    "content": response.answer,
                    "sources": response.sources,
                    "timestamp": datetime.now().isoformat()
                }
            ])
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"✅ Query processed in {response_time:.0f}ms")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Chat query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= ENHANCED MULTI-DOCUMENT ANALYSIS =============

class EnhancedAnalysisRequest(BaseModel):
    session_id: str
    selected_file_ids: List[str]
    query: Optional[str] = None
    analysis_type: str = "comprehensive"
    
    @validator('selected_file_ids', pre=True)
    def filter_none_values(cls, v):
        if isinstance(v, list):
            filtered = [fid for fid in v if fid is not None]
            if not filtered:
                raise ValueError('selected_file_ids cannot be empty')
            return filtered
        return v

@app.post("/api/analysis/enhanced")
async def enhanced_multi_document_analysis(request: EnhancedAnalysisRequest):
    """
    Perform enhanced multi-document analysis with:
    - Combined document analysis
    - Cross-document insights
    - Query-aware responses
    - Table extraction
    - Source mapping
    """
    try:
        logger.info("\n" + "="*80)
        logger.info("🔬 ENHANCED MULTI-DOCUMENT ANALYSIS")
        logger.info("="*80)
        logger.info(f"Session: {request.session_id}")
        logger.info(f"Files: {request.selected_file_ids}")
        logger.info(f"Query: {request.query}")
        logger.info(f"Analysis Type: {request.analysis_type}")
        
        # Convert file_ids to filenames
        filenames = get_filenames_from_file_ids(request.session_id, request.selected_file_ids)
        if not filenames:
            raise HTTPException(status_code=400, detail="No valid files found")
        
        # Retrieve chunks from all selected documents
        logger.info("🔍 Retrieving document chunks...")
        chunks = retrieve_relevant_chunks(
            request.query or "Comprehensive analysis of all documents",
            request.session_id,
            filenames,
            top_k=10
        )
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No content found in documents")
        
        # Initialize enhanced analyzer
        analyzer = EnhancedDocumentAnalyzer(embedder=get_embedder())
        
        # Perform multi-document analysis
        logger.info("📊 Performing multi-document analysis...")
        analysis = analyzer.analyze_multiple_documents(
            chunks,
            query=request.query,
            analysis_type=request.analysis_type
        )
        
        # Extract tables from combined content
        logger.info("📋 Extracting tables...")
        table_extractor = TableExtractor()
        combined_content = "\n\n".join([chunk['content'] for chunk in chunks])
        tables = table_extractor.extract_tables_from_text(combined_content)
        structured_data = table_extractor.extract_structured_data(combined_content)
        
        # Create enhanced analysis prompt for LLM
        logger.info("🤖 Generating comprehensive analysis with LLM...")
        analysis_prompt = create_enhanced_analysis_prompt(analysis, request.query)
        
        # Add table information to prompt
        if tables:
            table_summary = f"Found {len(tables)} tables in the document."
            analysis_prompt += f"\n\n## EXTRACTED TABLES:\n{table_summary}"
        
        # Add structured data to prompt
        if any(structured_data.values()):
            analysis_prompt += "\n\n## STRUCTURED DATA FOUND:\n"
            for data_type, values in structured_data.items():
                if values:
                    analysis_prompt += f"- {data_type.replace('_', ' ').title()}: {', '.join(values[:5])}\n"
        
        # Query LLM for comprehensive analysis
        try:
            llm_response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral",
                    "prompt": analysis_prompt,
                    "stream": False,
                },
                timeout=None
            )
            
            if llm_response.status_code == 200:
                comprehensive_analysis = llm_response.json()['response'].strip()
            else:
                comprehensive_analysis = "Error generating analysis"
        except Exception as e:
            logger.error(f"LLM error: {e}")
            comprehensive_analysis = "Error connecting to analysis model"
        
        logger.info("="*80)
        logger.info("✅ ENHANCED ANALYSIS COMPLETE")
        logger.info("="*80 + "\n")
        
        return {
            "status": "success",
            "session_id": request.session_id,
            "analysis": {
                "overview": analysis['overview'],
                "document_count": analysis['document_count'],
                "total_chunks": analysis['total_chunks'],
                "key_insights": analysis['key_insights'],
                "cross_document_insights": analysis['cross_document_insights'],
                "source_mapping": analysis['source_mapping'],
                "query_response": analysis.get('query_response'),
                "tables_found": len(tables),
                "structured_data": structured_data
            },
            "comprehensive_analysis": comprehensive_analysis,
            "tables": tables,
            "query": request.query
        }
    
    except Exception as e:
        logger.error(f"❌ Enhanced analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= RUN =============

if __name__ == "__main__":
    import uvicorn
    
    logger.info("\n" + "="*80)
    logger.info("🎯 STARTING UVICORN SERVER")
    logger.info("="*80 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False  # Disable reload in production
    )