# Quick Start Guide - Enhanced Multi-Document Analysis

## 🚀 Getting Started in 5 Minutes

### Step 1: Start the Backend Server
```bash
cd /home/dell/Desktop/manoj/nampdf/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

### Step 2: Start the Frontend Server
```bash
cd /home/dell/Desktop/manoj/nampdf/frontend
npm start
```

**Expected Output**:
```
Compiled successfully!
Local:            http://localhost:3001
```

### Step 3: Open the Application
- Navigate to: `http://localhost:3001`
- You should see the Document Analysis Chat interface

---

## 📄 Using the Enhanced Analysis

### Basic Workflow

1. **Upload Documents**
   - Click "Upload Documents" or drag & drop
   - Select multiple PDFs
   - Wait for processing to complete

2. **Select Files**
   - Check the files you want to analyze
   - Click "Select All" or choose specific files

3. **Perform Analysis**
   - Click the "Analysis" button (if available)
   - Or ask a question in the chat
   - System will automatically analyze selected documents

4. **View Results**
   - Results appear in expandable sections
   - Click section headers to expand/collapse
   - Review source mapping for verification

---

## 🎯 Common Tasks

### Task 1: Analyze Multiple Contracts
```
1. Upload 2-3 contract PDFs
2. Select all contracts
3. Ask: "What are the key differences between these contracts?"
4. Review the comparative analysis
```

### Task 2: Extract Payment Information
```
1. Upload invoice or contract PDFs
2. Select documents
3. Ask: "What are the payment terms and due dates?"
4. Check the "Structured Data" section for extracted dates and amounts
```

### Task 3: Find Common Clauses
```
1. Upload multiple agreement PDFs
2. Select all documents
3. Ask: "What clauses appear in all documents?"
4. Review "Cross-Document Insights" section
```

### Task 4: Get Document Summary
```
1. Upload PDF
2. Select document
3. Click "Summary" button
4. View comprehensive analysis
```

---

## 📊 Understanding the Results

### Overview Section
- **Document Count**: Number of documents analyzed
- **Total Chunks**: Number of content segments extracted
- **Summary**: Brief overview of all documents

### Key Insights
- Critical information extracted from documents
- Color-coded by type
- Clickable for more details

### Cross-Document Insights
- **Common Themes**: Terms appearing in multiple documents
- **Document Relationships**: How documents relate to each other
- **Relationship Strength**: 0-100% similarity

### Extracted Tables
- **Table Type**: Format detected (pipe_table or aligned_table)
- **Dimensions**: Rows × Columns
- **Preview**: First 5 rows shown (expandable)

### Structured Data
- **Emails**: All email addresses found
- **Phone Numbers**: Contact numbers
- **Dates**: Important dates in various formats
- **Amounts**: Monetary values
- **URLs**: Web links
- **References**: Document IDs and codes

### Source Mapping
- **File Names**: Which document each insight comes from
- **Chunk ID**: Specific content segment
- **Relevance Score**: 0-100% match to query
- **Preview**: First 100 characters of content

### Comprehensive Analysis
- LLM-generated detailed analysis
- Structured sections
- Evidence-backed statements
- Markdown formatted

---

## 🔍 Tips & Tricks

### Tip 1: Be Specific with Queries
- ❌ Bad: "Tell me about the document"
- ✅ Good: "What are the payment terms and penalties?"

### Tip 2: Use Multiple Documents
- Analyzing 2-3 related documents together provides better insights
- System identifies relationships and patterns

### Tip 3: Check Source Mapping
- Always verify insights by checking the source
- Click on source items to see the original content

### Tip 4: Review Extracted Data
- Structured data section shows all extracted information
- Useful for verification and cross-reference

### Tip 5: Expand All Sections
- Start with overview
- Then check key insights
- Review cross-document relationships
- Examine extracted tables
- Verify with source mapping

---

## ⚠️ Common Issues & Solutions

### Issue: "Upload failed"
**Solution**:
1. Check file size (max 50MB)
2. Ensure file is a valid PDF
3. Check browser console for errors
4. Refresh page and try again

### Issue: "No files selected"
**Solution**:
1. Click "Select All" to select all uploaded files
2. Or manually check individual files
3. Ensure at least one file is selected

### Issue: "Analysis not available"
**Solution**:
1. Ensure backend is running on port 8001
2. Check browser console for error messages
3. Verify files are uploaded and selected
4. Try refreshing the page

### Issue: "Tables not extracted"
**Solution**:
1. This is normal if documents don't have tables
2. Check "Structured Data" section instead
3. Some tables may be in image format (not extractable)

### Issue: "Slow analysis"
**Solution**:
1. Reduce number of documents (analyze 2-3 at a time)
2. Use more specific queries
3. Check backend logs for processing status
4. Ensure Ollama is running: `ollama serve`

---

## 🔧 System Requirements

### Backend
- Python 3.8+
- FastAPI
- FAISS
- Ollama (for LLM)
- PaddleOCR (for scanned PDFs)

### Frontend
- Node.js 14+
- React 17+
- Modern browser (Chrome, Firefox, Safari, Edge)

### Ports
- Backend: 8001
- Frontend: 3001
- Ollama: 11434

---

## 📚 File Structure

```
nampdf/
├── backend/
│   ├── main.py (main API)
│   ├── document_processor/
│   │   ├── enhanced_analyzer.py (NEW)
│   │   ├── table_extractor.py (NEW)
│   │   ├── ocr_processor.py
│   │   ├── chunker.py
│   │   └── extractor.py
│   └── uploads/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AnalysisResults.js (NEW)
│   │   │   ├── AnalysisResults.css (NEW)
│   │   │   ├── Chat.js
│   │   │   ├── ChatMessage.js
│   │   │   └── FileUpload.js
│   │   ├── services/
│   │   │   └── api.js (UPDATED)
│   │   └── App.js
│   └── package.json
├── ENHANCED_ANALYSIS_GUIDE.md (NEW)
└── QUICK_START.md (THIS FILE)
```

---

## 🎓 Learning Path

### Beginner
1. Upload a single PDF
2. Ask a simple question
3. Review the answer
4. Check source mapping

### Intermediate
1. Upload 2-3 related documents
2. Ask a specific question
3. Review cross-document insights
4. Verify with extracted data

### Advanced
1. Upload 5+ documents
2. Ask comparative questions
3. Analyze relationships
4. Extract and verify structured data
5. Review comprehensive analysis

---

## 📞 Need Help?

1. **Check the logs**:
   - Backend: Terminal where you ran `uvicorn`
   - Frontend: Browser console (F12)

2. **Review documentation**:
   - `ENHANCED_ANALYSIS_GUIDE.md` - Detailed guide
   - This file - Quick reference

3. **Verify setup**:
   - Backend running on 8001? ✓
   - Frontend running on 3001? ✓
   - Ollama running? ✓
   - Files uploaded? ✓

4. **Common fixes**:
   - Refresh browser (Ctrl+R or Cmd+R)
   - Restart backend server
   - Clear browser cache
   - Check file permissions

---

## ✨ Features Highlight

✅ **Multi-Document Analysis** - Analyze 2+ documents together
✅ **OCR Support** - Extract text from scanned PDFs
✅ **Table Extraction** - Automatically detect and parse tables
✅ **Structured Data** - Extract emails, dates, amounts, etc.
✅ **Query-Aware** - Get answers tailored to your questions
✅ **Source Mapping** - Trace every insight to its source
✅ **Cross-Document Insights** - Find relationships between documents
✅ **LLM Analysis** - Comprehensive AI-powered analysis
✅ **Responsive UI** - Works on desktop and mobile
✅ **Vector Search** - Semantic similarity matching

---

## 🎉 You're Ready!

Start analyzing your documents now:
1. Open http://localhost:3001
2. Upload your PDFs
3. Ask your questions
4. Get comprehensive analysis

Happy analyzing! 📊
