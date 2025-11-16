# ============= summary_routes.py =============
"""
Summary Generation and Management Routes
Handles automatic saving, retrieval, combining, and condensing of summaries
"""

import os
import json
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Import local modules
from models_local.ollama_model import OllamaModel
from document_processor.enhanced_ocr_analyzer import EnhancedOCRAnalyzer
from document_processor.table_extractor import TableExtractor
from document_processor.chunker import SemanticChunker
from document_processor.extractor import ContentExtractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/summary", tags=["Summary"])

# ============= INITIALIZATION =============

# Initialize tools
try:
    ollama_client = OllamaModel(model_name="mistral")
except Exception as e:
    logger.warning(f"⚠️ Ollama not available: {e}. Summary generation will be limited.")
    ollama_client = None

ocr_analyzer = EnhancedOCRAnalyzer()
table_extractor = TableExtractor()
chunker = SemanticChunker()
extractor = ContentExtractor()

# Create storage directory
SUMMARY_DIR = Path("./summaries")
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"📁 Summary storage directory: {SUMMARY_DIR}")


# ============= REQUEST MODELS =============

class SummaryGenerationRequest(BaseModel):
    filename: str
    session_id: str
    user_id: str = "default_user"


class CombineSummariesRequest(BaseModel):
    filenames: List[str]
    session_id: str
    user_id: str = "default_user"


class CondenseRequest(BaseModel):
    summary_text: str


# ============= UTILITY FUNCTIONS =============

def save_summary(filename: str, summary: str, metadata: Dict[str, Any]) -> None:
    """Save generated summary and metadata to disk.
    
    Args:
        filename: Original filename
        summary: Generated summary text
        metadata: Metadata dict with generation info
    """
    try:
        base_name = Path(filename).stem
        summary_path = SUMMARY_DIR / f"{base_name}_summary.txt"
        meta_path = SUMMARY_DIR / f"{base_name}_summary.json"

        # Save summary text
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)

        # Save metadata
        metadata["saved_at"] = datetime.now().isoformat()
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        logger.info(f"💾 Summary saved: {summary_path}")
        logger.info(f"📋 Metadata saved: {meta_path}")
    except Exception as e:
        logger.error(f"❌ Failed to save summary: {e}")
        raise


def load_saved_summary(filename: str) -> str:
    """Load previously saved summary if it exists.
    
    Args:
        filename: Original filename
        
    Returns:
        Summary text or empty string if not found
    """
    try:
        base_name = Path(filename).stem
        summary_path = SUMMARY_DIR / f"{base_name}_summary.txt"
        
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""
    except Exception as e:
        logger.error(f"❌ Failed to load summary: {e}")
        return ""


def load_saved_metadata(filename: str) -> Dict[str, Any]:
    """Load metadata for a saved summary.
    
    Args:
        filename: Original filename
        
    Returns:
        Metadata dict or empty dict if not found
    """
    try:
        base_name = Path(filename).stem
        meta_path = SUMMARY_DIR / f"{base_name}_summary.json"
        
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"❌ Failed to load metadata: {e}")
        return {}


def extract_text_from_pdf_for_summary(file_path: Path) -> str:
    """Extract text from PDF for summary generation.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text
    """
    try:
        import PyPDF2
        
        text = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text.append(page_text)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract page {page_num}: {e}")
        
        return "\n".join(text)
    except Exception as e:
        logger.error(f"❌ Error extracting text: {e}")
        return ""


# ============= SUMMARY GENERATION =============

@router.post("/generate")
async def generate_summary(req: SummaryGenerationRequest):
    """Generate a deep contextual summary for a document.
    
    Process:
    1. Extract text and tables from PDF
    2. Analyze document structure
    3. Generate comprehensive summary with Ollama
    4. Save summary and metadata
    
    Args:
        req: SummaryGenerationRequest with filename, session_id, user_id
        
    Returns:
        JSON with success status, summary text, and metadata
    """
    try:
        if not ollama_client:
            raise HTTPException(
                status_code=503,
                detail="Ollama service not available. Please ensure Ollama is running."
            )
        
        file_path = Path(f"./uploads/{req.filename}")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {req.filename}")

        logger.info(f"📘 Generating summary for {req.filename}")

        # Extract text from PDF
        text = extract_text_from_pdf_for_summary(file_path)
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found in document")

        logger.info(f"✅ Extracted {len(text)} characters from PDF")

        # Extract tables
        try:
            tables = table_extractor.extract_tables_from_text(text)
            tables_md = "\n\n".join([
                table_extractor.format_table_as_markdown(t) for t in tables
            ])
            if tables_md.strip():
                text += f"\n\n## Extracted Tables\n\n{tables_md}"
            logger.info(f"✅ Extracted {len(tables)} tables")
        except Exception as e:
            logger.warning(f"⚠️ Table extraction failed: {e}")

        # Analyze document structure
        try:
            analysis = ocr_analyzer.analyze_document_structure(text)
            context = ocr_analyzer.prepare_context_for_analysis(text, analysis)
            logger.info(f"✅ Document analysis complete: {analysis.get('document_type', 'Unknown')}")
        except Exception as e:
            logger.warning(f"⚠️ Structure analysis failed: {e}")
            context = text[:2000]  # Fallback to first 2000 chars

        # Build summary prompt
        prompt = f"""You are an expert summarizer specializing in technical, legal, and tender documents.
Generate a **detailed, factual summary** from the document content below.

Guidelines:
1. Include all key sections (Overview, Requirements, Technical Details, Timeline, Budget, Terms, Contacts, etc.)
2. Summarize important data, numbers, and findings accurately.
3. Use markdown headings (##) and bullet points for clarity.
4. Be comprehensive but concise (~25–35% of the full text).
5. Include extracted structured data if relevant.

Document Context:
{context}
"""

        # Generate summary with Ollama
        logger.info("🤖 Generating summary with Ollama...")
        summary = ollama_client.generate_text(prompt, max_tokens=700)
        
        if not summary.strip() or "Error" in summary:
            raise HTTPException(status_code=500, detail="Empty or error summary returned by LLM")

        logger.info(f"✅ Summary generated: {len(summary)} characters")

        # Save summary and metadata
        metadata = {
            "filename": req.filename,
            "session_id": req.session_id,
            "user_id": req.user_id,
            "model": ollama_client.model_name,
            "length": len(summary),
            "table_count": len(tables) if 'tables' in locals() else 0,
            "is_scanned": analysis.get("is_scanned", False) if 'analysis' in locals() else False,
            "document_type": analysis.get("document_type", "Unknown") if 'analysis' in locals() else "Unknown",
        }
        save_summary(req.filename, summary, metadata)

        return {
            "success": True,
            "summary": summary,
            "metadata": metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in generate_summary")
        raise HTTPException(status_code=500, detail=str(e))


# ============= COMBINE SUMMARIES =============

@router.post("/combine")
async def combine_summaries(req: CombineSummariesRequest):
    """Combine multiple summaries intelligently into one comprehensive report.
    
    Process:
    1. Load saved summaries for each file
    2. If not found, regenerate on-the-fly
    3. Combine all summaries into one coherent report
    4. Save combined summary
    
    Args:
        req: CombineSummariesRequest with filenames, session_id, user_id
        
    Returns:
        JSON with combined summary and count of merged documents
    """
    try:
        if not ollama_client:
            raise HTTPException(
                status_code=503,
                detail="Ollama service not available. Please ensure Ollama is running."
            )
        
        logger.info(f"🧩 Combining summaries for: {req.filenames}")

        summaries = []
        for fname in req.filenames:
            # Try to load saved summary
            summary_text = load_saved_summary(fname)
            
            if not summary_text.strip():
                logger.warning(f"⚠️ No saved summary for {fname}, regenerating...")
                try:
                    gen_resp = await generate_summary(SummaryGenerationRequest(
                        filename=fname, 
                        session_id=req.session_id, 
                        user_id=req.user_id
                    ))
                    summary_text = gen_resp["summary"]
                except Exception as e:
                    logger.error(f"❌ Failed to generate summary for {fname}: {e}")
                    continue
            
            summaries.append(f"=== {fname} ===\n{summary_text}")

        if not summaries:
            raise HTTPException(
                status_code=400,
                detail="No summaries available to combine"
            )

        combined_input = "\n\n".join(summaries)

        # Build combine prompt
        combine_prompt = f"""Combine the following document summaries into a single detailed report.

Instructions:
- Retain all important details, remove repetition.
- Start with a 3–4 paragraph executive summary.
- Then list each section clearly (Overview, Requirements, Technical Details, etc.)
- Maintain markdown formatting.
- Highlight key metrics and dates.

{combined_input}
"""

        logger.info("🤖 Combining summaries with Ollama...")
        combined_summary = ollama_client.generate_text(combine_prompt, max_tokens=1000)

        if not combined_summary.strip() or "Error" in combined_summary:
            raise HTTPException(status_code=500, detail="Failed to combine summaries")

        logger.info(f"✅ Combined summary generated: {len(combined_summary)} characters")

        # Save the combined summary
        combo_filename = "_".join([Path(f).stem for f in req.filenames])[:80]
        metadata = {
            "combined_files": req.filenames,
            "user_id": req.user_id,
            "session_id": req.session_id,
            "file_count": len(summaries),
            "combined_length": len(combined_summary)
        }
        save_summary(combo_filename, combined_summary, metadata)

        return {
            "success": True,
            "summary": combined_summary,
            "combined_count": len(summaries),
            "metadata": metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error combining summaries")
        raise HTTPException(status_code=500, detail=str(e))


# ============= CONDENSE SUMMARY =============

@router.post("/condense")
async def condense_summary(req: CondenseRequest):
    """Condense a long summary into a brief executive summary.
    
    Args:
        req: CondenseRequest with summary_text
        
    Returns:
        JSON with condensed summary
    """
    try:
        if not ollama_client:
            raise HTTPException(
                status_code=503,
                detail="Ollama service not available. Please ensure Ollama is running."
            )
        
        logger.info("📝 Condensing summary...")
        
        prompt = f"""Condense the following summary into a clear, 3-paragraph executive overview.
Focus on the most critical information, key metrics, and action items.

{req.summary_text}
"""
        
        condensed = ollama_client.generate_text(prompt, max_tokens=300)
        
        if not condensed.strip() or "Error" in condensed:
            raise HTTPException(status_code=500, detail="Failed to condense summary")

        logger.info(f"✅ Summary condensed: {len(condensed)} characters")
        
        return {
            "success": True,
            "condensed_summary": condensed
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error condensing summary")
        raise HTTPException(status_code=500, detail=str(e))


# ============= RETRIEVE SAVED SUMMARY =============

@router.get("/retrieve/{filename}")
async def retrieve_summary(filename: str):
    """Retrieve a previously saved summary.
    
    Args:
        filename: Original filename
        
    Returns:
        JSON with summary text and metadata
    """
    try:
        summary_text = load_saved_summary(filename)
        metadata = load_saved_metadata(filename)
        
        if not summary_text:
            raise HTTPException(
                status_code=404,
                detail=f"No saved summary found for {filename}"
            )
        
        logger.info(f"📂 Retrieved summary for {filename}")
        
        return {
            "success": True,
            "filename": filename,
            "summary": summary_text,
            "metadata": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving summary")
        raise HTTPException(status_code=500, detail=str(e))


# ============= LIST SAVED SUMMARIES =============

@router.get("/list")
async def list_summaries():
    """List all saved summaries.
    
    Returns:
        JSON with list of saved summaries and their metadata
    """
    try:
        summaries = []
        
        for meta_file in SUMMARY_DIR.glob("*_summary.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    summaries.append({
                        "filename": metadata.get("filename", meta_file.stem),
                        "saved_at": metadata.get("saved_at"),
                        "user_id": metadata.get("user_id"),
                        "length": metadata.get("length", 0),
                        "document_type": metadata.get("document_type", "Unknown")
                    })
            except Exception as e:
                logger.warning(f"⚠️ Failed to read {meta_file}: {e}")
        
        logger.info(f"📋 Listed {len(summaries)} saved summaries")
        
        return {
            "success": True,
            "count": len(summaries),
            "summaries": summaries
        }
    except Exception as e:
        logger.exception("Error listing summaries")
        raise HTTPException(status_code=500, detail=str(e))
