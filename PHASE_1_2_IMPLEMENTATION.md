# Phase 1 & 2 Implementation Guide

## Phase 1: Centralize FAISS Operations ✅ STARTED

### Status: Enhanced FAISSManager Created

The `FAISSManager` class has been completely rewritten with:

#### New Features:
1. **Flexible Index Types**: Support for both `flat_ip` (inner product) and `flat_l2` (L2 distance)
2. **Better Error Handling**: Comprehensive try-catch blocks with detailed logging
3. **Metadata Management**: Dedicated methods for metadata retrieval
4. **Index Statistics**: `get_index_stats()` for monitoring
5. **Index Clearing**: `clear_index()` for cleanup
6. **Type Hints**: Full type annotations for better IDE support

#### Key Methods:
```python
# Add embeddings with metadata
manager.add_embeddings(embeddings, metadata)

# Search for similar chunks
distances, indices = manager.search(query_embedding, k=15)

# Get metadata for results
results = manager.get_metadata(indices)

# Save/Load index
manager.save_index(path)
manager.load_index(path)

# Merge indices
manager.merge_indices(other_manager)

# Get statistics
stats = manager.get_index_stats()
```

### Next Steps for Phase 1:
1. ⏳ Update `main.py` to use `FAISSManager` instead of inline FAISS operations
2. ⏳ Replace all `load_faiss_index()` calls with manager methods
3. ⏳ Replace all `faiss.write_index()` calls with manager methods
4. ⏳ Test all FAISS operations work correctly

---

## Phase 2: Integrate Table Extraction into Summaries ⏳ PENDING

### Current State:
- `table_extractor.py` has full table parsing capability
- Tables are NOT extracted during upload
- Tables are NOT included in summaries

### Implementation Plan:

#### Step 1: Extract Tables During Upload
**File**: `/backend/main.py` - `upload_file()` endpoint

```python
# After text extraction, add:
from document_processor.table_extractor import TableExtractor

table_extractor = TableExtractor()
tables = table_extractor.extract_tables_from_text(extracted_text)

# Store table metadata with chunks
for table in tables:
    table_metadata = {
        'filename': filename,
        'type': 'table',
        'table_type': table.get('type'),
        'headers': table.get('headers'),
        'row_count': table.get('row_count'),
        'content': table.get('content')
    }
    # Include in chunks
```

#### Step 2: Format Tables for Summary
**File**: `/backend/main.py` - `generate_summary()` endpoint

```python
# After retrieving chunks, add:
# Separate tables from text chunks
tables = [c for c in chunks if c.get('type') == 'table']
text_chunks = [c for c in chunks if c.get('type') != 'table']

# Format tables as Markdown
table_markdown = ""
for table in tables:
    table_markdown += table_extractor.format_table_as_markdown(table)
    table_markdown += "\n\n"

# Include in context
context = table_markdown + "\n\n" + "\n\n".join([c['content'] for c in text_chunks])
```

#### Step 3: Update Summary Prompt
**File**: `/backend/main.py` - `generate_summary()` endpoint

```python
# Update prompt to mention tables:
summary_prompt = f"""...
IMPORTANT: Include any tables or structured data found in the document.
Format tables as Markdown tables in your analysis.
...
{context}
"""
```

### Files to Modify:
1. `/backend/main.py` - Upload and summary endpoints
2. `/backend/document_processor/table_extractor.py` - Enhance if needed

---

## Implementation Order

### Phase 1 Tasks (FAISS Centralization):

1. **Create wrapper functions in main.py**
   - `create_faiss_manager(chat_id)` - Create new manager
   - `load_faiss_manager(chat_id)` - Load existing manager
   - `save_faiss_manager(chat_id, manager)` - Save manager

2. **Replace FAISS operations in upload endpoint**
   - Replace inline index creation with manager
   - Replace index.add() with manager.add_embeddings()
   - Replace faiss.write_index() with manager.save_index()

3. **Replace FAISS operations in query endpoints**
   - Replace load_faiss_index() with manager.load_index()
   - Replace faiss.normalize_L2() with manager.search()
   - Replace index.search() with manager.search()

4. **Test all operations**
   - Upload PDF
   - Generate summary
   - Chat queries
   - Verify results are identical

### Phase 2 Tasks (Table Integration):

1. **Extract tables during upload**
   - Initialize TableExtractor
   - Extract tables from text
   - Store table metadata

2. **Include tables in summary**
   - Retrieve table chunks
   - Format as Markdown
   - Include in context

3. **Update summary prompt**
   - Mention tables in instructions
   - Request Markdown formatting

4. **Test table extraction**
   - Upload PDF with tables
   - Verify tables are extracted
   - Verify tables appear in summary

---

## Code Snippets for Integration

### Wrapper Functions (to add to main.py):

```python
from embedding.faiss_manager import FAISSManager

def create_faiss_manager(chat_id: str) -> FAISSManager:
    """Create a new FAISS manager for a session."""
    manager = FAISSManager(dimension=EMBEDDING_DIM, index_type="flat_ip")
    return manager

def load_faiss_manager(chat_id: str) -> Optional[FAISSManager]:
    """Load FAISS manager from disk."""
    index_path = VECTOR_STORE_DIR / chat_id
    if not index_path.exists():
        return None
    
    manager = FAISSManager(dimension=EMBEDDING_DIM, index_type="flat_ip")
    try:
        manager.load_index(index_path)
        return manager
    except Exception as e:
        logger.error(f"Failed to load FAISS manager: {e}")
        return None

def save_faiss_manager(chat_id: str, manager: FAISSManager) -> bool:
    """Save FAISS manager to disk."""
    index_path = VECTOR_STORE_DIR / chat_id
    try:
        manager.save_index(index_path)
        return True
    except Exception as e:
        logger.error(f"Failed to save FAISS manager: {e}")
        return False
```

### Table Integration (to add to generate_summary):

```python
# Extract tables
table_extractor = TableExtractor()
all_tables = []

for chunk in chunks:
    if 'table' in chunk.get('content', '').lower():
        tables = table_extractor.extract_tables_from_text(chunk['content'])
        all_tables.extend(tables)

# Format tables
table_content = ""
for table in all_tables:
    table_content += table_extractor.format_table_as_markdown(table)
    table_content += "\n\n"

# Include in context
if table_content:
    context = f"## Extracted Tables\n\n{table_content}\n\n## Document Content\n\n{context}"
```

---

## Testing Checklist

### Phase 1 Testing:
- [ ] Backend starts without errors
- [ ] Upload PDF works
- [ ] FAISS manager creates index
- [ ] FAISS manager saves index
- [ ] FAISS manager loads index
- [ ] Search returns correct results
- [ ] Summary generation works
- [ ] Chat queries work
- [ ] Results are identical to before

### Phase 2 Testing:
- [ ] Tables are extracted during upload
- [ ] Table metadata is stored
- [ ] Tables appear in summary
- [ ] Tables are formatted as Markdown
- [ ] Summary includes table content
- [ ] Chat can reference tables

---

## Success Criteria

### Phase 1:
✅ All FAISS operations use FAISSManager
✅ No inline FAISS code in main.py
✅ All tests pass
✅ Performance is same or better

### Phase 2:
✅ Tables extracted from documents
✅ Tables included in summaries
✅ Tables formatted as Markdown
✅ Summary quality improved

---

## Notes

- Phase 1 is a refactoring - functionality should remain the same
- Phase 2 adds new functionality - summaries will be more complete
- Both phases improve code maintainability
- Testing is critical to ensure no regressions
