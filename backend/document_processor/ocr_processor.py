import paddleocr
import numpy as np
from PIL import Image
import logging
import os
import tempfile
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple

logger = logging.getLogger('document_processor.ocr_processor')

class EnhancedOCRProcessor:
    """
    Enhanced OCR processor with:
    - Full document processing (no page limits)
    - Better text extraction quality
    - Table structure preservation
    - Image preprocessing
    """
    
    def __init__(self):
        logger.info("🔧 Initializing Enhanced OCR Processor...")
        
        # Initialize PaddleOCR with optimized settings
        self.ocr = paddleocr.PaddleOCR(
            lang='en',
            use_angle_cls=True,  # Enable angle classification for rotated text
            use_gpu=False,
            show_log=False
        )
        
        logger.info("✅ Enhanced OCR Processor initialized")
    
    def _preprocess_image(self, image_path: str) -> str:
        """
        Preprocess image for better OCR quality.
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (max 4000px on longest side)
                max_size = 4000
                width, height = img.size
                
                if width > max_size or height > max_size:
                    ratio = min(max_size/width, max_size/height)
                    new_size = (int(width * ratio), int(height * ratio))
                    logger.info(f"  📐 Resizing from {width}x{height} to {new_size[0]}x{new_size[1]}")
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Enhance contrast and sharpness
                from PIL import ImageEnhance
                
                # Increase contrast
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                
                # Increase sharpness
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.3)
                
                # Save preprocessed image
                base, ext = os.path.splitext(image_path)
                processed_path = f"{base}_processed{ext}"
                img.save(processed_path, 'PNG', quality=95)
                
                return processed_path
        
        except Exception as e:
            logger.warning(f"  ⚠️ Image preprocessing failed: {e}")
            return image_path
    
    def extract_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from image with enhanced quality.
        """
        start_time = datetime.now()
        logger.info(f"📷 Processing image: {os.path.basename(image_path)}")
        
        try:
            # Preprocess image
            processed_path = self._preprocess_image(str(image_path))
            
            # Run OCR
            result = self.ocr.ocr(processed_path)
            
            # Clean up processed image
            if processed_path != str(image_path) and os.path.exists(processed_path):
                try:
                    os.remove(processed_path)
                except:
                    pass
            
            # Extract text with structure preservation
            text_lines = []
            table_regions = []
            
            if result and isinstance(result, list):
                for page_idx, page in enumerate(result):
                    if page and isinstance(page, list):
                        # Sort by vertical position to maintain reading order
                        sorted_lines = sorted(
                            page,
                            key=lambda x: (x[0][0][1], x[0][0][0])  # Sort by Y then X
                        )
                        
                        # Group lines that might be part of tables
                        current_y = None
                        line_group = []
                        
                        for line in sorted_lines:
                            try:
                                box = line[0]
                                text_info = line[1]
                                text_part = str(text_info[0]) if text_info[0] else ""
                                confidence = float(text_info[1]) if text_info[1] else 0.0
                                
                                if confidence > 0.5 and text_part.strip():
                                    y_pos = box[0][1]
                                    
                                    # Check if this line is aligned with previous (potential table row)
                                    if current_y and abs(y_pos - current_y) < 10:
                                        line_group.append(text_part)
                                    else:
                                        # Save previous group
                                        if len(line_group) > 2:  # Potential table row
                                            table_regions.append(" | ".join(line_group))
                                        elif line_group:
                                            text_lines.extend(line_group)
                                        
                                        line_group = [text_part]
                                        current_y = y_pos
                            
                            except Exception as e:
                                logger.debug(f"Error processing line: {e}")
                                continue
                        
                        # Add remaining lines
                        if line_group:
                            if len(line_group) > 2:
                                table_regions.append(" | ".join(line_group))
                            else:
                                text_lines.extend(line_group)
            
            # Combine text
            text = "\n".join(text_lines)
            
            # Add table regions
            if table_regions:
                text += "\n\n=== TABLE DATA ===\n"
                text += "\n".join(table_regions)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ OCR completed in {duration:.2f}s - Extracted {len(text)} chars")
            
            return {
                "text": text,
                "tables": table_regions,
                "line_count": len(text_lines),
                "table_count": len(table_regions)
            }
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ OCR failed after {duration:.2f}s: {e}")
            return {"text": "", "tables": [], "error": str(e)}
    
    def extract_from_pdf_images(
        self,
        pdf_path: str,
        max_pages: int = None  # Process ALL pages by default
    ) -> Dict[str, Any]:
        """
        Extract from image-based PDF - process ALL pages unless limited.
        """
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # Process all pages unless limited
            pages_to_process = max_pages if max_pages else total_pages
            pages_to_process = min(pages_to_process, total_pages)
            
            logger.info(f"📄 Processing {pages_to_process} pages from {total_pages} total")
            
            all_text = ""
            all_tables = []
            page_results = []
            
            for page_num in range(pages_to_process):
                try:
                    logger.info(f"  📄 Processing page {page_num + 1}/{pages_to_process}...")
                    page = doc[page_num]
                    page_header = f"\n\n{'='*60}\n=== Page {page_num + 1} ===\n{'='*60}\n\n"
                    
                    # Try direct text extraction first
                    direct_text = page.get_text("text")
                    if direct_text.strip() and len(direct_text.strip()) > 50:
                        all_text += page_header + direct_text
                        page_results.append({
                            'page': page_num + 1,
                            'method': 'direct',
                            'char_count': len(direct_text)
                        })
                        continue
                    
                    # Use OCR for scanned pages
                    zoom = 2.0  # Higher resolution
                    mat = fitz.Matrix(zoom, zoom)
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        img_path = os.path.join(temp_dir, f"page_{page_num}.png")
                        
                        # Render page
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                        pix.save(img_path)
                        
                        # OCR processing
                        ocr_result = self.extract_from_image(img_path)
                        
                        if ocr_result.get("text", "").strip():
                            all_text += page_header + ocr_result["text"]
                            page_results.append({
                                'page': page_num + 1,
                                'method': 'ocr',
                                'char_count': len(ocr_result["text"])
                            })
                        
                        if ocr_result.get("tables"):
                            all_tables.extend(ocr_result["tables"])
                
                except Exception as page_err:
                    logger.error(f"  ❌ Error on page {page_num + 1}: {page_err}")
                    page_results.append({
                        'page': page_num + 1,
                        'method': 'failed',
                        'error': str(page_err)
                    })
            
            # Summary
            successful_pages = sum(1 for r in page_results if r['method'] != 'failed')
            logger.info(f"✅ Processed {successful_pages}/{pages_to_process} pages successfully")
            
            return {
                "text": all_text.strip(),
                "tables": all_tables,
                "page_results": page_results,
                "total_pages": total_pages,
                "processed_pages": pages_to_process
            }
        
        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {e}")
            return {
                "text": "",
                "tables": [],
                "error": str(e)
            }


class EnhancedTableExtractor:
    """
    Enhanced table extraction with better structure detection.
    """
    
    def __init__(self):
        logger.info("✅ Enhanced TableExtractor initialized")
    
    def extract_tables_with_context(
        self,
        text: str,
        embedder=None
    ) -> List[Dict[str, Any]]:
        """
        Extract tables with surrounding context for better understanding.
        """
        logger.info("📊 Extracting tables with context...")
        
        lines = text.split('\n')
        tables = []
        
        # Detect table regions with context
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for table indicators
            if self._is_table_line(line):
                # Found potential table
                table_start = max(0, i - 2)  # Include 2 lines before (context)
                table_end = i
                
                # Find end of table
                while table_end < len(lines) and self._is_table_line(lines[table_end]):
                    table_end += 1
                
                # Include 2 lines after (context)
                table_end = min(len(lines), table_end + 2)
                
                # Extract table with context
                table_text = '\n'.join(lines[table_start:table_end])
                
                # Parse table structure
                parsed = self._parse_table_structure(
                    '\n'.join(lines[i:table_end-2])  # Actual table without context
                )
                
                if parsed:
                    tables.append({
                        'table': parsed,
                        'context_before': '\n'.join(lines[table_start:i]),
                        'context_after': '\n'.join(lines[table_end-2:table_end]),
                        'full_text': table_text,
                        'start_line': table_start,
                        'end_line': table_end
                    })
                
                i = table_end
            else:
                i += 1
        
        logger.info(f"✅ Extracted {len(tables)} tables with context")
        return tables
    
    def _is_table_line(self, line: str) -> bool:
        """Enhanced table line detection"""
        if not line or len(line.strip()) < 10:
            return False
        
        # Count structural elements
        pipes = line.count('|')
        tabs = line.count('\t')
        double_spaces = len([m for m in re.finditer(r'\s{2,}', line)])
        
        # Check for numeric content (common in tables)
        has_numbers = bool(re.search(r'\d', line))
        
        # Check for common table separators
        has_separators = bool(re.search(r'[-_]{3,}', line))
        
        # Scoring system
        score = 0
        score += min(pipes, 3)  # Up to 3 points for pipes
        score += min(tabs, 2)  # Up to 2 points for tabs
        score += min(double_spaces, 2)  # Up to 2 points for aligned spaces
        score += 1 if has_numbers else 0
        score += 1 if has_separators else 0
        
        return score >= 3
    
    def _parse_table_structure(self, table_text: str) -> Dict[str, Any]:
        """Parse table into structured format"""
        lines = [l.strip() for l in table_text.split('\n') if l.strip()]
        
        if len(lines) < 2:
            return None
        
        # Detect delimiter
        first_line = lines[0]
        delimiter = None
        
        if '|' in first_line:
            delimiter = '|'
        elif '\t' in first_line:
            delimiter = '\t'
        else:
            # Try to detect column positions from spacing
            return self._parse_aligned_table(lines)
        
        # Parse delimited table
        rows = []
        headers = None
        
        for i, line in enumerate(lines):
            # Skip separator lines
            if re.match(r'^[\s\-|_+=]+$', line):
                continue
            
            cells = [cell.strip() for cell in line.split(delimiter)]
            cells = [c for c in cells if c]  # Remove empty
            
            if i == 0:
                headers = cells
            else:
                if len(cells) == len(headers):
                    rows.append(dict(zip(headers, cells)))
                elif cells:  # Handle partial rows
                    row = {}
                    for j, cell in enumerate(cells):
                        if j < len(headers):
                            row[headers[j]] = cell
                    rows.append(row)
        
        return {
            'headers': headers,
            'rows': rows,
            'row_count': len(rows),
            'column_count': len(headers) if headers else 0
        }
    
    def _parse_aligned_table(self, lines: List[str]) -> Dict[str, Any]:
        """Parse space-aligned table"""
        # Detect column positions
        positions = self._detect_column_positions(lines)
        
        if not positions:
            return None
        
        rows = []
        headers = None
        
        for i, line in enumerate(lines):
            cells = self._extract_cells_by_position(line, positions)
            
            if i == 0:
                headers = cells
            else:
                if len(cells) == len(headers):
                    rows.append(dict(zip(headers, cells)))
        
        return {
            'headers': headers,
            'rows': rows,
            'row_count': len(rows),
            'column_count': len(headers) if headers else 0
        }
    
    def _detect_column_positions(self, lines: List[str]) -> List[int]:
        """Detect column boundaries in aligned text"""
        # Find consistent spacing patterns
        space_positions = {}
        
        for line in lines[:min(10, len(lines))]:  # Check first 10 lines
            for i, char in enumerate(line):
                if char == ' ' and i > 0:
                    space_positions[i] = space_positions.get(i, 0) + 1
        
        # Find positions that appear in most lines
        threshold = len(lines) * 0.5
        positions = [pos for pos, count in space_positions.items() if count >= threshold]
        
        return sorted(positions)
    
    def _extract_cells_by_position(self, line: str, positions: List[int]) -> List[str]:
        """Extract cells based on column positions"""
        cells = []
        start = 0
        
        for pos in positions:
            if pos > start and pos < len(line):
                cell = line[start:pos].strip()
                if cell:
                    cells.append(cell)
                start = pos
        
        # Add last cell
        if start < len(line):
            cell = line[start:].strip()
            if cell:
                cells.append(cell)
        
        return cells


# ============= Integration Function =============

def extract_with_enhanced_ocr(pdf_path: str) -> Dict[str, Any]:
    """
    Main function to extract content with enhanced OCR and table detection.
    """
    logger.info(f"🚀 Starting enhanced extraction: {os.path.basename(pdf_path)}")
    
    # Initialize processors
    ocr_processor = EnhancedOCRProcessor()
    table_extractor = EnhancedTableExtractor()
    
    # Extract text with OCR
    ocr_result = ocr_processor.extract_from_pdf_images(pdf_path)
    
    if not ocr_result.get('text'):
        logger.warning("⚠️ No text extracted from PDF")
        return {
            'text': '',
            'tables': [],
            'error': 'No text could be extracted'
        }
    
    # Extract tables with context
    tables = table_extractor.extract_tables_with_context(ocr_result['text'])
    
    logger.info(f"✅ Extraction complete:")
    logger.info(f"  - Text: {len(ocr_result['text'])} characters")
    logger.info(f"  - Tables: {len(tables)}")
    logger.info(f"  - Pages: {ocr_result.get('processed_pages', 0)}")
    
    return {
        'text': ocr_result['text'],
        'tables': tables,
        'ocr_result': ocr_result,
        'page_results': ocr_result.get('page_results', [])
    }