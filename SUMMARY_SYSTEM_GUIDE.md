# Summary System Integration Guide

## Overview
The summary system provides automatic saving, retrieval, combining, and condensing of document summaries. All summaries are stored locally and can be reused without regenerating from scratch.

## Architecture

### Components
1. **summary_routes.py** - FastAPI router with all summary endpoints
2. **Storage** - `/summaries/` directory with `.txt` and `.json` files
3. **Integration** - Registered in `main.py` at startup

### Storage Structure
```
summaries/
├── document1_summary.txt      # Summary text
├── document1_summary.json     # Metadata
├── document2_summary.txt
├── document2_summary.json
└── ...
```

## API Endpoints

### 1. Generate Summary
**POST** `/api/summary/generate`

Generate a comprehensive summary for a document and save it.

**Request:**
```json
{
  "filename": "GeM-Bidding-8255755.pdf",
  "session_id": "session-123",
  "user_id": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "summary": "## Overview\n...",
  "metadata": {
    "filename": "GeM-Bidding-8255755.pdf",
    "session_id": "session-123",
    "user_id": "user@example.com",
    "model": "mistral",
    "length": 2500,
    "table_count": 3,
    "is_scanned": false,
    "document_type": "Tender",
    "saved_at": "2025-11-04T15:30:00"
  }
}
```

### 2. Combine Summaries
**POST** `/api/summary/combine`

Combine multiple saved summaries into one comprehensive report.

**Request:**
```json
{
  "filenames": ["doc1.pdf", "doc2.pdf", "doc3.pdf"],
  "session_id": "session-123",
  "user_id": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "summary": "## Executive Summary\n...",
  "combined_count": 3,
  "metadata": {
    "combined_files": ["doc1.pdf", "doc2.pdf", "doc3.pdf"],
    "file_count": 3,
    "combined_length": 5000
  }
}
```

### 3. Condense Summary
**POST** `/api/summary/condense`

Create a brief executive summary from a longer summary.

**Request:**
```json
{
  "summary_text": "## Overview\n... (long summary) ..."
}
```

**Response:**
```json
{
  "success": true,
  "condensed_summary": "## Executive Overview\n... (3 paragraphs) ..."
}
```

### 4. Retrieve Saved Summary
**GET** `/api/summary/retrieve/{filename}`

Retrieve a previously saved summary.

**Response:**
```json
{
  "success": true,
  "filename": "GeM-Bidding-8255755.pdf",
  "summary": "## Overview\n...",
  "metadata": {
    "filename": "GeM-Bidding-8255755.pdf",
    "saved_at": "2025-11-04T15:30:00",
    "length": 2500
  }
}
```

### 5. List All Summaries
**GET** `/api/summary/list`

List all saved summaries with metadata.

**Response:**
```json
{
  "success": true,
  "count": 5,
  "summaries": [
    {
      "filename": "GeM-Bidding-8255755.pdf",
      "saved_at": "2025-11-04T15:30:00",
      "user_id": "user@example.com",
      "length": 2500,
      "document_type": "Tender"
    }
  ]
}
```

## Workflow Examples

### Example 1: Generate and Save Summary
```bash
curl -X POST http://localhost:8000/api/summary/generate \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "document.pdf",
    "session_id": "sess-123",
    "user_id": "user@example.com"
  }'
```

### Example 2: Combine Multiple Summaries
```bash
curl -X POST http://localhost:8000/api/summary/combine \
  -H "Content-Type: application/json" \
  -d '{
    "filenames": ["doc1.pdf", "doc2.pdf"],
    "session_id": "sess-123",
    "user_id": "user@example.com"
  }'
```

### Example 3: Retrieve Saved Summary
```bash
curl http://localhost:8000/api/summary/retrieve/document.pdf
```

## Features

### ✅ Automatic Saving
- All generated summaries are automatically saved to `/summaries/`
- Metadata is stored as JSON for tracking

### ✅ Reusability
- Load saved summaries without regenerating
- Combine multiple summaries efficiently
- Avoid unnecessary model re-runs

### ✅ Metadata Tracking
- Filename, user, session, timestamp
- Model used, document type, table count
- Scanned vs. native PDF detection

### ✅ Graceful Degradation
- If Ollama is unavailable, endpoints return 503 error
- System continues to work for retrieval operations

### ✅ Deep Analysis
- OCR + structure analysis for scanned PDFs
- Table extraction and formatting
- Document type detection

## Requirements

### Python Dependencies
- FastAPI
- Pydantic
- PyPDF2
- Ollama (running on localhost:11434)

### System Requirements
- Ollama service running: `ollama serve`
- Model available: `ollama pull mistral`
- Write access to `/summaries/` directory

## Configuration

### Ollama Model
Default: `mistral`

To use a different model, modify `summary_routes.py`:
```python
ollama_client = OllamaModel(model_name="neural-chat")  # or "orca-mini"
```

### Storage Directory
Default: `./summaries/`

To change, modify `summary_routes.py`:
```python
SUMMARY_DIR = Path("/custom/path/summaries")
```

### Max Tokens
- Summary generation: 700 tokens
- Combining: 1000 tokens
- Condensing: 300 tokens

## Error Handling

### Ollama Not Available
```json
{
  "detail": "Ollama service not available. Please ensure Ollama is running."
}
```

**Solution:** Start Ollama with `ollama serve`

### File Not Found
```json
{
  "detail": "File not found: document.pdf"
}
```

**Solution:** Ensure file exists in `/uploads/` directory

### No Saved Summary
```json
{
  "detail": "No saved summary found for document.pdf"
}
```

**Solution:** Generate summary first with `/api/summary/generate`

## Performance Notes

- **First generation**: ~30-60 seconds (depends on document size)
- **Combining**: ~20-40 seconds (for 2-3 documents)
- **Retrieval**: <100ms (from disk)
- **Condensing**: ~10-20 seconds

## Security Considerations

- User IDs are tracked for audit purposes
- Session IDs link summaries to user sessions
- All files stored locally (no external API calls except Ollama)
- Metadata includes generation timestamp for tracking

## Troubleshooting

### Summaries not saving
- Check `/summaries/` directory exists and is writable
- Check logs for permission errors

### Empty summaries generated
- Verify PDF has extractable text
- Check Ollama is responding correctly
- Try with a different document

### Combine endpoint fails
- Ensure all files have been summarized first
- Check individual summaries exist in `/summaries/`

## Future Enhancements

- [ ] Database storage instead of file-based
- [ ] Summary versioning
- [ ] Batch processing
- [ ] Summary templates
- [ ] Multi-language support
