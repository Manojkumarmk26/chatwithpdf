"""
Content Preprocessor
Preprocesses and structures document content for better analysis
"""

import logging
import re
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class ContentPreprocessor:
    """Preprocesses document content for comprehensive analysis."""
    
    @staticmethod
    def extract_sections(content: str) -> Dict[str, str]:
        """Extract major sections from content."""
        sections = {}
        
        # Common section patterns
        section_patterns = [
            (r'(?:^|\n)(?:INSTRUCTIONS?|PROCEDURE|PROCESS)(?:\s|:|$)', 'instructions'),
            (r'(?:^|\n)(?:REQUIREMENTS?|SPECIFICATIONS?)(?:\s|:|$)', 'requirements'),
            (r'(?:^|\n)(?:TECHNICAL|ARCHITECTURE|SYSTEM)(?:\s|:|$)', 'technical'),
            (r'(?:^|\n)(?:TIMELINE|SCHEDULE|MILESTONES?)(?:\s|:|$)', 'timeline'),
            (r'(?:^|\n)(?:BUDGET|FINANCIAL|COST|PRICING)(?:\s|:|$)', 'financial'),
            (r'(?:^|\n)(?:TERMS?|CONDITIONS?|CLAUSES?)(?:\s|:|$)', 'terms'),
            (r'(?:^|\n)(?:COMPLIANCE|STANDARDS?|CERTIFICATIONS?)(?:\s|:|$)', 'compliance'),
            (r'(?:^|\n)(?:CONTACT|STAKEHOLDERS?|PARTIES?)(?:\s|:|$)', 'contacts'),
        ]
        
        for pattern, section_name in section_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                start = match.start()
                # Find next section or end of content
                end = len(content)
                for next_pattern, _ in section_patterns:
                    next_match = re.search(next_pattern, content[start+1:], re.IGNORECASE | re.MULTILINE)
                    if next_match:
                        end = min(end, start + 1 + next_match.start())
                
                section_content = content[start:end].strip()
                if section_content:
                    sections[section_name] = section_content
        
        return sections
    
    @staticmethod
    def extract_tables(content: str) -> List[Dict[str, Any]]:
        """Extract table-like structures from content."""
        tables = []
        
        # Pattern for pipe-separated tables
        pipe_table_pattern = r'\|.*?\|.*?\n(?:\|[-\s|]*\|)?\n(?:\|.*?\|.*?\n)+'
        
        for match in re.finditer(pipe_table_pattern, content, re.MULTILINE):
            table_text = match.group(0)
            rows = [row.strip() for row in table_text.split('\n') if row.strip() and '|' in row]
            
            if len(rows) > 1:
                # Parse rows
                parsed_rows = []
                for row in rows:
                    cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                    if cells:
                        parsed_rows.append(cells)
                
                if parsed_rows:
                    tables.append({
                        'type': 'pipe_table',
                        'rows': parsed_rows,
                        'row_count': len(parsed_rows),
                        'column_count': len(parsed_rows[0]) if parsed_rows else 0
                    })
        
        return tables
    
    @staticmethod
    def extract_key_information(content: str) -> Dict[str, List[str]]:
        """Extract key information items."""
        info = {
            'dates': [],
            'amounts': [],
            'requirements': [],
            'instructions': [],
            'contacts': [],
            'references': []
        }
        
        # Extract dates (various formats)
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
        ]
        for pattern in date_patterns:
            info['dates'].extend(re.findall(pattern, content, re.IGNORECASE))
        
        # Extract monetary amounts
        amount_patterns = [
            r'(?:Rs\.?|₹|INR|USD|\$|€)\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:Rs\.?|₹|INR|USD|\$|€)',
            r'(?:Crore|Lakh|Million|Billion|Thousand)\s*(?:Rs\.?|₹|INR|USD|\$|€)?'
        ]
        for pattern in amount_patterns:
            info['amounts'].extend(re.findall(pattern, content, re.IGNORECASE))
        
        # Extract requirements (lines with "must", "should", "required")
        requirement_patterns = [
            r'(?:must|should|required|shall|mandatory).*?(?:\.|$)',
        ]
        for pattern in requirement_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            info['requirements'].extend(matches[:10])  # Limit to 10
        
        # Extract instructions (lines with "step", "procedure", "process")
        instruction_patterns = [
            r'(?:step|procedure|process|instruction|guideline).*?(?:\.|$)',
        ]
        for pattern in instruction_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            info['instructions'].extend(matches[:10])  # Limit to 10
        
        # Extract emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        info['contacts'].extend(re.findall(email_pattern, content))
        
        # Extract phone numbers
        phone_pattern = r'(?:\+91|0)?[\s-]?(?:\d{3}[\s-]?\d{3}[\s-]?\d{4}|\d{10})'
        info['contacts'].extend(re.findall(phone_pattern, content))
        
        # Extract document references
        ref_pattern = r'(?:Ref|Reference|Doc|Document|ID|Code)[\s:]*([A-Z0-9\-/]+)'
        info['references'].extend(re.findall(ref_pattern, content, re.IGNORECASE))
        
        # Remove duplicates
        for key in info:
            info[key] = list(set(info[key]))
        
        return info
    
    @staticmethod
    def structure_content(
        text: str,
        tables: List[Dict[str, Any]] = None,
        extracted_data: Dict[str, Any] = None
    ) -> str:
        """Structure content for better LLM analysis."""
        
        structured = []
        
        # Add main content
        structured.append("=" * 80)
        structured.append("DOCUMENT CONTENT")
        structured.append("=" * 80)
        structured.append(text)
        
        # Add extracted tables
        if tables:
            structured.append("\n" + "=" * 80)
            structured.append("EXTRACTED TABLES")
            structured.append("=" * 80)
            for idx, table in enumerate(tables, 1):
                structured.append(f"\nTable {idx}:")
                if 'rows' in table:
                    for row in table['rows']:
                        structured.append(" | ".join(str(cell) for cell in row))
        
        # Add key information
        if extracted_data:
            structured.append("\n" + "=" * 80)
            structured.append("KEY INFORMATION EXTRACTED")
            structured.append("=" * 80)
            
            if extracted_data.get('dates'):
                structured.append("\nDates Found:")
                for date in extracted_data['dates'][:10]:
                    structured.append(f"  - {date}")
            
            if extracted_data.get('amounts'):
                structured.append("\nFinancial Amounts Found:")
                for amount in extracted_data['amounts'][:10]:
                    structured.append(f"  - {amount}")
            
            if extracted_data.get('requirements'):
                structured.append("\nRequirements Found:")
                for req in extracted_data['requirements'][:10]:
                    structured.append(f"  - {req}")
            
            if extracted_data.get('instructions'):
                structured.append("\nInstructions Found:")
                for instr in extracted_data['instructions'][:10]:
                    structured.append(f"  - {instr}")
            
            if extracted_data.get('contacts'):
                structured.append("\nContact Information Found:")
                for contact in extracted_data['contacts'][:10]:
                    structured.append(f"  - {contact}")
            
            if extracted_data.get('references'):
                structured.append("\nDocument References Found:")
                for ref in extracted_data['references'][:10]:
                    structured.append(f"  - {ref}")
        
        structured.append("\n" + "=" * 80)
        
        return "\n".join(structured)
