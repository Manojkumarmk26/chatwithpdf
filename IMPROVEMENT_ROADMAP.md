# 🚀 System Improvement Roadmap

## Phase 1: Centralize FAISS Operations (Priority: HIGH)

### Current State
- `faiss_manager.py` exists but is **not used** in `main.py`
- FAISS operations are duplicated throughout `main.py`
- No unified interface for FAISS operations

### Goal
- Replace all FAISS logic in `main.py` with calls to `FAISSManager`
- Reduce code duplication
- Improve maintainability

### Tasks
1. ✅ Review `faiss_manager.py` (already done)
2. ⏳ Create wrapper functions in `main.py` that use `FAISSManager`
3. ⏳ Replace all inline FAISS operations with manager calls
4. ⏳ Test all FAISS operations work correctly

### Files to Modify
- `/backend/main.py` - Replace FAISS logic
- `/backend/embedding/faiss_manager.py` - Enhance if needed

---

## Phase 2: Integrate Table Extraction into Summaries (Priority: HIGH)

### Current State
- `table_extractor.py` exists with full table parsing capability
- Tables are **NOT** included in summary generation
- Summary only uses text chunks, ignoring structured data

### Goal
- Extract tables from documents during upload
- Include table content in summary context
- Format tables as Markdown in final summary

### Tasks
1. ✅ Review `table_extractor.py` (already done)
2. ⏳ Modify upload endpoint to extract and store tables
3. ⏳ Update summary generation to include table content
4. ⏳ Format tables in Markdown for better presentation
5. ⏳ Test table extraction and inclusion in summaries

### Files to Modify
- `/backend/main.py` - Add table extraction to upload, include in summary
- `/backend/document_processor/table_extractor.py` - Enhance if needed

---

## Phase 3: Add Session Persistence (Priority: MEDIUM)

### Current State
- All sessions exist only in memory
- Sessions are lost after backend restart
- No database or file-based persistence

### Goal
- Save session metadata to disk
- Persist FAISS indices with session info
- Allow session recovery after restart

### Tasks
1. ⏳ Create session manager class
2. ⏳ Save session metadata to JSON/SQLite
3. ⏳ Load sessions on backend startup
4. ⏳ Implement session cleanup (old sessions)
5. ⏳ Test session persistence and recovery

### Files to Create/Modify
- `/backend/session_manager.py` (NEW)
- `/backend/main.py` - Integrate session manager

---

## Phase 4: Add Async Background Tasks (Priority: MEDIUM)

### Current State
- Large PDF processing blocks requests
- OCR and embedding operations are synchronous
- No background task queue

### Goal
- Move OCR/embedding to background tasks
- Return immediately to user
- Notify user when processing completes

### Tasks
1. ⏳ Implement background task queue (Celery or FastAPI BackgroundTasks)
2. ⏳ Move OCR processing to background
3. ⏳ Move embedding generation to background
4. ⏳ Add progress tracking
5. ⏳ Add WebSocket notifications for completion

### Files to Modify
- `/backend/main.py` - Add background task handling
- `/backend/document_processor/ocr_processor.py` - Make async-compatible

---

## Phase 5: Enhance Error Handling & Retry Logic (Priority: MEDIUM)

### Current State
- Minimal error handling
- No retry logic for failed operations
- No timeout handling for Ollama requests

### Goal
- Add comprehensive error handling
- Implement retry logic with exponential backoff
- Add timeouts for LLM requests
- Better error messages to frontend

### Tasks
1. ⏳ Add retry decorator for network operations
2. ⏳ Add timeout handling for Ollama
3. ⏳ Add fallback extraction methods
4. ⏳ Improve error logging
5. ⏳ Return meaningful error messages to frontend

### Files to Modify
- `/backend/main.py` - Add error handling
- `/backend/models_local/ollama_model.py` - Add timeout/retry

---

## Phase 6: Add Search Result Formatting (Priority: LOW)

### Current State
- Chat responses don't show source information
- No clear indication of which file/page result came from

### Goal
- Add source attribution to chat responses
- Show filename and page number
- Add relevance scores

### Tasks
1. ⏳ Enhance chunk metadata with source info
2. ⏳ Format chat responses with source prefixes
3. ⏳ Add relevance scores to results
4. ⏳ Update frontend to display sources

### Files to Modify
- `/backend/main.py` - Add source formatting
- `/frontend/src/components/ChatWindow.js` - Display sources

---

## Phase 7: Add Embedding Cache (Priority: LOW)

### Current State
- Embeddings are generated fresh for every query
- No caching of embeddings
- Repeated queries are inefficient

### Goal
- Cache embeddings for reuse
- Reduce API calls to embedding model
- Improve query performance

### Tasks
1. ⏳ Create embedding cache (Redis or file-based)
2. ⏳ Check cache before generating embeddings
3. ⏳ Store new embeddings in cache
4. ⏳ Implement cache invalidation

### Files to Create/Modify
- `/backend/embedding/cache.py` (NEW)
- `/backend/embedding/embedder.py` - Use cache

---

## Phase 8: Add Search Reranking (Priority: LOW)

### Current State
- Search results use only semantic similarity
- No reranking of results
- Less relevant results might appear first

### Goal
- Add cross-encoder reranker
- Improve search result quality
- Better ranking of results

### Tasks
1. ⏳ Integrate cross-encoder model
2. ⏳ Rerank top-k results
3. ⏳ Compare quality before/after
4. ⏳ Optimize for performance

### Files to Create/Modify
- `/backend/embedding/reranker.py` (NEW)
- `/backend/main.py` - Use reranker in queries

---

## Implementation Priority

### Immediate (This Session)
1. **Phase 1**: Centralize FAISS Operations
2. **Phase 2**: Integrate Table Extraction

### Short-term (Next Session)
3. **Phase 3**: Session Persistence
4. **Phase 4**: Async Background Tasks

### Medium-term
5. **Phase 5**: Error Handling & Retry
6. **Phase 6**: Search Result Formatting

### Long-term
7. **Phase 7**: Embedding Cache
8. **Phase 8**: Search Reranking

---

## Quick Reference: Key Improvements

| Phase | Feature | Impact | Effort | Status |
|-------|---------|--------|--------|--------|
| 1 | Centralize FAISS | Code quality ⬆️ | Medium | ⏳ |
| 2 | Table Integration | Accuracy ⬆️ | Medium | ⏳ |
| 3 | Session Persistence | UX ⬆️ | Medium | ⏳ |
| 4 | Async Tasks | Performance ⬆️ | High | ⏳ |
| 5 | Error Handling | Reliability ⬆️ | Medium | ⏳ |
| 6 | Source Formatting | UX ⬆️ | Low | ⏳ |
| 7 | Embedding Cache | Performance ⬆️ | Low | ⏳ |
| 8 | Search Reranking | Accuracy ⬆️ | Medium | ⏳ |

---

## Success Criteria

✅ All FAISS operations use centralized manager
✅ Tables extracted and included in summaries
✅ Sessions persist across restarts
✅ Large PDFs don't block requests
✅ Errors handled gracefully
✅ Search results show sources
✅ Embedding cache reduces API calls
✅ Search results properly ranked

---

## Notes

- Each phase builds on previous phases
- Can be implemented independently if needed
- Testing required after each phase
- Frontend updates may be needed for some phases
