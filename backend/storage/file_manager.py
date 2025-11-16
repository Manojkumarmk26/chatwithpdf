import shutil
from pathlib import Path
import uuid
import logging

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, upload_dir: Path):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(exist_ok=True)

    def save_file(self, file_content, filename: str) -> str:
        """Save uploaded file and return file_id"""
        try:
            file_id = str(uuid.uuid4())
            file_path = self.upload_dir / file_id / filename
            file_path.parent.mkdir(exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"File saved: {file_id}/{filename}")
            return file_id
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise

    def get_file_path(self, file_id: str, filename: str) -> Path:
        """Get path to saved file"""
        return self.upload_dir / file_id / filename

    def delete_file(self, file_id: str):
        """Delete uploaded file"""
        try:
            file_dir = self.upload_dir / file_id
            if file_dir.exists():
                shutil.rmtree(file_dir)
                logger.info(f"File deleted: {file_id}")
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            raise