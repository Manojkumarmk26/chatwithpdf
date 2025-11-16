from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileValidator:
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png", ".bmp"}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    @staticmethod
    def validate_file(file_path: Path) -> tuple:
        """Validate file before processing"""
        # Check existence
        if not file_path.exists():
            return False, "File does not exist"
        
        # Check extension
        if file_path.suffix.lower() not in FileValidator.ALLOWED_EXTENSIONS:
            return False, f"File type not supported. Allowed: {FileValidator.ALLOWED_EXTENSIONS}"
        
        # Check size
        if file_path.stat().st_size > FileValidator.MAX_FILE_SIZE:
            return False, "File size exceeds maximum limit"
        
        return True, "File is valid"