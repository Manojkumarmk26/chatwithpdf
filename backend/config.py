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

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
    ".md",
    ".csv",
    ".tsv",
    ".xlsx",
    ".pptx",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp"
}
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
MAX_RETRIEVAL_RESULTS = 150

# Query / Cache Config
QUERY_CACHE_MAX_SIZE = int(os.getenv("QUERY_CACHE_MAX_SIZE", "100"))
QUERY_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "600"))
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "5"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "25"))

# Batch Processing Config
MAX_CONCURRENT_FILE_TASKS = int(os.getenv("MAX_CONCURRENT_FILE_TASKS", "3"))

# API Config
API_TIMEOUT = 300
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000"
]