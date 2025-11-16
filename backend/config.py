import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
CACHE_DIR = BASE_DIR / "cache"
INDEX_DIR = BASE_DIR / "faiss_indices"

UPLOAD_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png", ".bmp"}
MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_FILES_UPLOAD = 10
CHUNK_SIZE = 256
CHUNK_OVERLAP = 50

# Embedding Config
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIMENSION = 768

# ========== OLLAMA CONFIG (NEW - REPLACE HuggingFace Config) ==========
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "true").lower() == "true"
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "mistral")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MAX_TOKENS = 256
OLLAMA_TEMPERATURE = 0.7
OLLAMA_TIMEOUT = 300
# ========== END OLLAMA CONFIG ==========

# FAISS Config
SIMILARITY_THRESHOLD = 0.5
TOP_K_RETRIEVAL = 3

# API Config
API_TIMEOUT = 300
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000"
]