import re
from typing import List
import logging

logger = logging.getLogger(__name__)

class ContentExtractor:
    @staticmethod
    def extract_tables_as_text(tables):
        """Convert table data to structured text"""
        text_output = ""
        for idx, table in enumerate(tables):
            text_output += f"\n[TABLE {idx + 1}]\n"
            if isinstance(table, list):
                for row in table:
                    text_output += " | ".join([str(cell) for cell in row]) + "\n"
            text_output += "[END TABLE]\n"
        return text_output

    @staticmethod
    def clean_text(text):
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        return text.strip()

    @staticmethod
    def extract_structured_content(raw_content):
        """Extract and structure content from loaded document"""
        text = raw_content.get("text", "")
        tables = raw_content.get("tables", [])
        
        # Clean text
        text = ContentExtractor.clean_text(text)
        
        # Add tables as structured text
        tables_text = ContentExtractor.extract_tables_as_text(tables)
        
        structured_content = text + "\n" + tables_text
        return structured_content
