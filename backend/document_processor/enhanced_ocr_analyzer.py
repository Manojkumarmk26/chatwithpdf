"""
Enhanced OCR Analyzer for Deep Document Analysis
Provides comprehensive analysis of scanned, normal, and mixed PDFs
"""

import logging
import re
from typing import Dict, List, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class EnhancedOCRAnalyzer:
    """
    Analyzes OCR-extracted content with deep contextual understanding.
    Handles scanned PDFs, normal PDFs, and mixed content.
    """
    
    @staticmethod
    def analyze_document_structure(content: str) -> Dict[str, Any]:
        """
        Analyze document structure and extract all sections comprehensively.
        """
        logger.info("🔍 Analyzing document structure...")
        
        analysis = {
            'sections': {},
            'key_information': {},
            'document_type': 'Unknown',
            'confidence': 0,
            'content_quality': 'Unknown',
            'is_scanned': False,
            'structure_detected': []
        }
        
        # Detect if document is scanned (OCR quality indicators)
        analysis['is_scanned'] = EnhancedOCRAnalyzer._detect_scanned_pdf(content)
        analysis['content_quality'] = EnhancedOCRAnalyzer._assess_content_quality(content)
        
        # Extract all sections comprehensively
        analysis['sections'] = EnhancedOCRAnalyzer._extract_all_sections(content)
        
        # Extract key information
        analysis['key_information'] = EnhancedOCRAnalyzer._extract_comprehensive_info(content)
        
        # Detect document type
        analysis['document_type'] = EnhancedOCRAnalyzer._detect_document_type(content)
        
        # Detect structure
        analysis['structure_detected'] = EnhancedOCRAnalyzer._detect_structure_elements(content)
        
        logger.info(f"✅ Document analysis complete: {analysis['document_type']}")
        return analysis
    
    @staticmethod
    def _detect_scanned_pdf(content: str) -> bool:
        """Detect if document is scanned (OCR-processed)."""
        # Scanned PDFs often have OCR artifacts
        ocr_indicators = [
            r'\b[a-z]{1,2}\s+[a-z]{1,2}\b',  # Single letter words (OCR errors)
            r'[0-9]{1,2}\s+[a-z]{1,2}\s+[0-9]',  # Mixed patterns
            r'(?:OCR|scanned|image|extracted)',  # Explicit indicators
        ]
        
        indicator_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in ocr_indicators)
        return indicator_count > 5
    
    @staticmethod
    def _assess_content_quality(content: str) -> str:
        """Assess quality of extracted content."""
        if not content or len(content) < 100:
            return 'Poor'
        
        # Check for coherent sentences
        sentences = re.split(r'[.!?]+', content)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        if avg_sentence_length < 3:
            return 'Poor'
        elif avg_sentence_length < 8:
            return 'Fair'
        else:
            return 'Good'
    
    @staticmethod
    def _extract_all_sections(content: str) -> Dict[str, str]:
        """Extract ALL sections from document comprehensively."""
        sections = {}
        
        # Comprehensive section patterns
        section_patterns = {
            'overview': [
                r'(?:DOCUMENT\s+)?OVERVIEW|INTRODUCTION|EXECUTIVE\s+SUMMARY|SUMMARY',
                r'(?:^|\n)(?:1\.|I\.)\s+(?:OVERVIEW|INTRODUCTION|EXECUTIVE\s+SUMMARY)',
            ],
            'instructions': [
                r'INSTRUCTIONS?|PROCEDURE|PROCESS|STEPS?|HOW\s+TO|GUIDELINES?',
                r'(?:^|\n)(?:2\.|II\.)\s+(?:INSTRUCTIONS?|PROCEDURE)',
            ],
            'requirements': [
                r'REQUIREMENTS?|SPECIFICATIONS?|SPECS|MUST\s+HAVE|SHOULD\s+HAVE',
                r'(?:^|\n)(?:3\.|III\.)\s+(?:REQUIREMENTS?|SPECIFICATIONS?)',
            ],
            'technical': [
                r'TECHNICAL|ARCHITECTURE|SYSTEM|DESIGN|TECHNOLOGY|TECHNICAL\s+DETAILS',
                r'(?:^|\n)(?:4\.|IV\.)\s+(?:TECHNICAL|ARCHITECTURE)',
            ],
            'timeline': [
                r'TIMELINE|SCHEDULE|MILESTONES?|DATES?|DEADLINES?|PHASES?',
                r'(?:^|\n)(?:5\.|V\.)\s+(?:TIMELINE|SCHEDULE)',
            ],
            'budget': [
                r'BUDGET|FINANCIAL|COST|PRICING|PAYMENT|EXPENSES?|FEES?',
                r'(?:^|\n)(?:6\.|VI\.)\s+(?:BUDGET|FINANCIAL)',
            ],
            'terms': [
                r'TERMS?|CONDITIONS?|CLAUSES?|AGREEMENT|LEGAL|LIABILITY',
                r'(?:^|\n)(?:7\.|VII\.)\s+(?:TERMS?|CONDITIONS?)',
            ],
            'compliance': [
                r'COMPLIANCE|STANDARDS?|CERTIFICATIONS?|REQUIREMENTS?|REGULATIONS?',
                r'(?:^|\n)(?:8\.|VIII\.)\s+(?:COMPLIANCE|STANDARDS?)',
            ],
            'contacts': [
                r'CONTACT|STAKEHOLDERS?|PARTIES?|AUTHOR|RESPONSIBLE|TEAM',
                r'(?:^|\n)(?:9\.|IX\.)\s+(?:CONTACT|STAKEHOLDERS?)',
            ],
            'data': [
                r'DATA|TABLES?|FIGURES?|CHARTS?|APPENDIX|ATTACHMENT',
                r'(?:^|\n)(?:10\.|X\.)\s+(?:DATA|TABLES?)',
            ],
            'findings': [
                r'FINDINGS?|RESULTS?|CONCLUSIONS?|OUTCOMES?|KEY\s+POINTS?',
                r'(?:^|\n)(?:11\.|XI\.)\s+(?:FINDINGS?|RESULTS?)',
            ],
            'recommendations': [
                r'RECOMMENDATIONS?|NEXT\s+STEPS?|ACTIONS?|SUGGESTIONS?',
                r'(?:^|\n)(?:12\.|XII\.)\s+(?:RECOMMENDATIONS?|NEXT\s+STEPS?)',
            ],
        }
        
        # Extract each section
        for section_name, patterns in section_patterns.items():
            section_content = EnhancedOCRAnalyzer._extract_section_content(content, patterns)
            if section_content:
                sections[section_name] = section_content
                logger.info(f"  ✓ Extracted {section_name}: {len(section_content)} chars")
        
        return sections
    
    @staticmethod
    def _extract_section_content(content: str, patterns: List[str]) -> str:
        """Extract content for a specific section."""
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                start = match.start()
                
                # Find next section header or end
                next_section_pattern = r'\n(?:^|\n)(?:[A-Z][A-Z\s]+:|[0-9]+\.|[A-Z]{1,3}\.)\s'
                next_match = re.search(next_section_pattern, content[start+1:], re.MULTILINE)
                
                if next_match:
                    end = start + 1 + next_match.start()
                else:
                    end = len(content)
                
                section_text = content[start:end].strip()
                if len(section_text) > 50:  # Only return if substantial
                    return section_text
        
        return ""
    
    @staticmethod
    def _extract_comprehensive_info(content: str) -> Dict[str, List[str]]:
        """Extract comprehensive key information."""
        info = {
            'dates': [],
            'amounts': [],
            'requirements': [],
            'instructions': [],
            'contacts': [],
            'references': [],
            'acronyms': [],
            'key_terms': [],
            'email_addresses': [],
            'phone_numbers': [],
            'urls': [],
            'document_ids': [],
            'certifications': [],
            'standards': [],
        }
        
        # Extract dates
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',
        ]
        for pattern in date_patterns:
            info['dates'].extend(re.findall(pattern, content, re.IGNORECASE))
        
        # Extract monetary amounts
        amount_patterns = [
            r'(?:USD|INR|EUR|\$|₹|€)\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:USD|INR|EUR|dollars?|rupees?|euros?)',
            r'(?:budget|cost|price|amount|fee):\s*[\d,]+(?:\.\d{2})?',
        ]
        for pattern in amount_patterns:
            info['amounts'].extend(re.findall(pattern, content, re.IGNORECASE))
        
        # Extract requirements (lines with "must", "should", "required")
        requirement_lines = re.findall(r'.*(?:must|should|required|shall|need|must\s+have).*', content, re.IGNORECASE)
        info['requirements'] = [line.strip() for line in requirement_lines if len(line.strip()) > 20][:20]
        
        # Extract instructions (lines with action verbs)
        instruction_patterns = [
            r'(?:^|\n)\s*(?:1\.|•|-|→)\s+.*(?:do|perform|execute|run|follow|complete|submit)',
            r'(?:^|\n)\s*(?:Step|Procedure|Process).*?:\s+.*',
        ]
        for pattern in instruction_patterns:
            info['instructions'].extend(re.findall(pattern, content, re.IGNORECASE))
        
        # Extract email addresses
        info['email_addresses'] = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
        
        # Extract phone numbers
        info['phone_numbers'] = re.findall(r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', content)
        
        # Extract URLs
        info['urls'] = re.findall(r'https?://[^\s]+', content)
        
        # Extract acronyms
        acronyms = re.findall(r'\b[A-Z]{2,}\b', content)
        info['acronyms'] = list(set(acronyms))[:20]
        
        # Extract certifications
        cert_patterns = [
            r'(?:CMMI|ISO|ITIL|PRINCE2|PMP|AGILE|SCRUM|SIX\s+SIGMA)',
            r'(?:CERTIFIED|ACCREDITED|CERTIFIED\s+BY)',
        ]
        for pattern in cert_patterns:
            info['certifications'].extend(re.findall(pattern, content, re.IGNORECASE))
        
        # Extract standards
        standards = re.findall(r'(?:ISO\s+\d+|NIST|IEEE|RFC|W3C|OWASP)', content, re.IGNORECASE)
        info['standards'] = list(set(standards))
        
        # Remove duplicates and limit
        for key in info:
            if isinstance(info[key], list):
                info[key] = list(set(info[key]))[:15]
        
        return info
    
    @staticmethod
    def _detect_document_type(content: str) -> str:
        """Detect document type."""
        type_indicators = {
            'Specification': [r'specification|spec|technical\s+spec', r'requirements\s+specification'],
            'Proposal': [r'proposal|bid|tender', r'proposed\s+solution'],
            'Contract': [r'contract|agreement|terms\s+and\s+conditions', r'legal\s+agreement'],
            'Manual': [r'manual|guide|handbook|instructions?', r'user\s+guide'],
            'Report': [r'report|analysis|findings?', r'executive\s+summary'],
            'Policy': [r'policy|procedure|guidelines?', r'standard\s+operating\s+procedure'],
            'Invoice': [r'invoice|bill|receipt', r'payment\s+request'],
            'Form': [r'form|application|questionnaire', r'data\s+collection'],
        }
        
        content_lower = content.lower()
        scores = {}
        
        for doc_type, patterns in type_indicators.items():
            score = sum(len(re.findall(pattern, content_lower)) for pattern in patterns)
            scores[doc_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'Document'
    
    @staticmethod
    def _detect_structure_elements(content: str) -> List[str]:
        """Detect structural elements in document."""
        elements = []
        
        if re.search(r'\n\d+\.\s+', content):
            elements.append('numbered_sections')
        if re.search(r'\n[A-Z]\.\s+', content):
            elements.append('lettered_sections')
        if re.search(r'\n•\s+', content):
            elements.append('bullet_points')
        if re.search(r'\n-\s+', content):
            elements.append('dashed_lists')
        if re.search(r'\|.*\|.*\n', content):
            elements.append('tables')
        if re.search(r'\[.*\]', content):
            elements.append('references')
        if re.search(r'Table\s+\d+', content, re.IGNORECASE):
            elements.append('numbered_tables')
        if re.search(r'Figure\s+\d+', content, re.IGNORECASE):
            elements.append('numbered_figures')
        
        return elements
    
    @staticmethod
    def prepare_context_for_analysis(content: str, analysis: Dict[str, Any]) -> str:
        """
        Prepare comprehensive context for LLM analysis.
        Includes all extracted information and structure.
        """
        logger.info("📋 Preparing comprehensive context for analysis...")
        
        context_parts = []
        
        # Add document metadata
        context_parts.append(f"DOCUMENT TYPE: {analysis['document_type']}")
        context_parts.append(f"CONTENT QUALITY: {analysis['content_quality']}")
        context_parts.append(f"IS SCANNED: {analysis['is_scanned']}")
        context_parts.append(f"DETECTED STRUCTURE: {', '.join(analysis['structure_detected']) or 'None'}")
        context_parts.append("")
        
        # Add key information summary
        key_info = analysis['key_information']
        if key_info['dates']:
            context_parts.append(f"DATES FOUND: {', '.join(key_info['dates'][:10])}")
        if key_info['amounts']:
            context_parts.append(f"AMOUNTS FOUND: {', '.join(key_info['amounts'][:10])}")
        if key_info['email_addresses']:
            context_parts.append(f"CONTACTS: {', '.join(key_info['email_addresses'][:5])}")
        if key_info['acronyms']:
            context_parts.append(f"KEY ACRONYMS: {', '.join(key_info['acronyms'][:10])}")
        if key_info['certifications']:
            context_parts.append(f"CERTIFICATIONS: {', '.join(set(key_info['certifications']))}")
        if key_info['standards']:
            context_parts.append(f"STANDARDS: {', '.join(set(key_info['standards']))}")
        context_parts.append("")
        
        # Add full content
        context_parts.append("FULL DOCUMENT CONTENT:")
        context_parts.append("=" * 80)
        context_parts.append(content)
        context_parts.append("=" * 80)
        context_parts.append("")
        
        # Add extracted sections
        if analysis['sections']:
            context_parts.append("EXTRACTED SECTIONS:")
            for section_name, section_content in analysis['sections'].items():
                context_parts.append(f"\n--- {section_name.upper()} ---")
                context_parts.append(section_content[:500])  # First 500 chars of each section
        
        return "\n".join(context_parts)
