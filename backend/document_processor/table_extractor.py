"""
Enhanced Table and Structured Data Extraction Module
Handles OCR, table detection, and structured data extraction from PDFs
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
import re

logger = logging.getLogger(__name__)


class TableExtractor:
    """Extracts tables and structured data from documents"""
    
    def __init__(self):
        logger.info("✅ TableExtractor initialized")
    
    def extract_tables_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract table-like structures from OCR text
        
        Args:
            text: Extracted text from document
        
        Returns:
            List of detected tables with structure
        """
        logger.info("🔍 Detecting table structures in text...")
        
        tables = []
        lines = text.split('\n')
        
        # Detect table patterns
        table_regions = self._detect_table_regions(lines)
        
        for region_start, region_end in table_regions:
            table_text = '\n'.join(lines[region_start:region_end])
            table = self._parse_table_region(table_text, region_start)
            if table:
                tables.append(table)
        
        logger.info(f"✅ Detected {len(tables)} table structures")
        return tables
    
    def _detect_table_regions(self, lines: List[str]) -> List[Tuple[int, int]]:
        """Detect regions that contain table-like structures"""
        regions = []
        in_table = False
        table_start = 0
        
        for i, line in enumerate(lines):
            # Check if line looks like a table row (has multiple columns/separators)
            is_table_line = self._is_table_line(line)
            
            if is_table_line and not in_table:
                # Start of table
                table_start = i
                in_table = True
            elif not is_table_line and in_table:
                # End of table
                regions.append((table_start, i))
                in_table = False
        
        # Handle table at end of document
        if in_table:
            regions.append((table_start, len(lines)))
        
        return regions
    
    def _is_table_line(self, line: str) -> bool:
        """Check if a line appears to be part of a table"""
        # Check for multiple separators or aligned columns
        separators = line.count('|') + line.count('\t')
        spaces = line.count('  ')  # Multiple spaces indicate columns
        
        # Check for common table patterns
        has_numbers = any(char.isdigit() for char in line)
        
        return (separators >= 2 or spaces >= 2) and len(line.strip()) > 10
    
    def _parse_table_region(self, table_text: str, start_line: int) -> Optional[Dict[str, Any]]:
        """Parse a detected table region into structured format"""
        
        lines = [l.strip() for l in table_text.split('\n') if l.strip()]
        
        if len(lines) < 2:
            return None
        
        # Try to parse as pipe-separated table
        if '|' in lines[0]:
            return self._parse_pipe_table(lines, start_line)
        
        # Try to parse as tab-separated or space-aligned table
        return self._parse_aligned_table(lines, start_line)
    
    def _parse_pipe_table(self, lines: List[str], start_line: int) -> Dict[str, Any]:
        """Parse pipe-separated table format"""
        
        rows = []
        headers = None
        
        for i, line in enumerate(lines):
            cells = [cell.strip() for cell in line.split('|')]
            cells = [c for c in cells if c]  # Remove empty cells
            
            if i == 0:
                headers = cells
            else:
                if len(cells) == len(headers):
                    rows.append(dict(zip(headers, cells)))
        
        return {
            "type": "pipe_table",
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(headers) if headers else 0,
            "start_line": start_line,
            "content": "\n".join(lines)
        }
    
    def _parse_aligned_table(self, lines: List[str], start_line: int) -> Dict[str, Any]:
        """Parse space or tab-aligned table format"""
        
        # Detect column positions based on alignment
        column_positions = self._detect_column_positions(lines)
        
        rows = []
        headers = None
        
        for i, line in enumerate(lines):
            cells = self._extract_cells_by_position(line, column_positions)
            
            if i == 0:
                headers = cells
            else:
                if len(cells) == len(headers):
                    rows.append(dict(zip(headers, cells)))
        
        return {
            "type": "aligned_table",
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(headers) if headers else 0,
            "start_line": start_line,
            "content": "\n".join(lines)
        }
    
    def _detect_column_positions(self, lines: List[str]) -> List[int]:
        """Detect column positions in aligned table"""
        
        # Find positions where multiple lines have spaces
        positions = set()
        
        for line in lines:
            for i, char in enumerate(line):
                if char == ' ' and i > 0 and line[i-1] != ' ':
                    positions.add(i)
        
        return sorted(list(positions))
    
    def _extract_cells_by_position(self, line: str, positions: List[int]) -> List[str]:
        """Extract cells based on column positions"""
        
        cells = []
        start = 0
        
        for pos in positions:
            if pos > start:
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
    
    def format_table_as_markdown(self, table: Dict[str, Any]) -> str:
        """Convert extracted table to Markdown format"""
        
        if not table.get('headers'):
            return ""
        
        lines = []
        
        # Header row
        lines.append("| " + " | ".join(table['headers']) + " |")
        
        # Separator row
        lines.append("|" + "|".join(["-" * 10 for _ in table['headers']]) + "|")
        
        # Data rows
        for row in table.get('rows', []):
            cells = [str(row.get(header, '')) for header in table['headers']]
            lines.append("| " + " | ".join(cells) + " |")
        
        return "\n".join(lines)
    
    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data patterns from text
        (emails, phone numbers, dates, amounts, etc.)
        """
        
        logger.info("🔍 Extracting structured data patterns...")
        
        structured_data = {
            "emails": self._extract_emails(text),
            "phone_numbers": self._extract_phone_numbers(text),
            "dates": self._extract_dates(text),
            "amounts": self._extract_amounts(text),
            "urls": self._extract_urls(text),
            "references": self._extract_references(text)
        }
        
        logger.info(f"✅ Extracted structured data: {len(structured_data)} categories")
        return structured_data
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(pattern, text)))
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers"""
        patterns = [
            r'\+?1?\d{9,15}',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            r'\d{3}-\d{3}-\d{4}'
        ]
        numbers = []
        for pattern in patterns:
            numbers.extend(re.findall(pattern, text))
        return list(set(numbers))
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates"""
        patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
            r'\d{4}-\d{1,2}-\d{1,2}'
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(dates))
    
    def _extract_amounts(self, text: str) -> List[str]:
        """Extract monetary amounts"""
        pattern = r'[$€£¥]?\s*\d+(?:,\d{3})*(?:\.\d{2})?'
        return list(set(re.findall(pattern, text)))
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs"""
        pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        return list(set(re.findall(pattern, text)))
    
    def _extract_references(self, text: str) -> List[str]:
        """Extract document references (IDs, codes, etc.)"""
        patterns = [
            r'(?:ID|Code|Ref|Reference):\s*([A-Z0-9\-]+)',
            r'(?:Invoice|PO|Order)\s*#?:?\s*([A-Z0-9\-]+)',
            r'(?:Contract|Agreement)\s*#?:?\s*([A-Z0-9\-]+)'
        ]
        references = []
        for pattern in patterns:
            references.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(references))


