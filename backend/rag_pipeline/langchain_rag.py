from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
import logging

logger = logging.getLogger(__name__)

class LangChainRAG:
    def __init__(self, embedder_model="BAAI/bge-base-en-v1.5"):
        self.embeddings = HuggingFaceEmbeddings(model_name=embedder_model)
        self.vector_stores = {}  # file_id -> vectorstore

    def create_vectorstore(self, file_id: str, chunks: list):
        """Create vector store for document chunks"""
        try:
            from langchain_core.documents import Document
            
            # Convert chunks to LangChain documents
            documents = [
                Document(
                    page_content=chunk["content"],
                    metadata={
                        "chunk_id": chunk.get("chunk_id"),
                        "file_id": file_id,
                        "index": chunk.get("index")
                    }
                )
                for chunk in chunks
            ]
            
            # Create FAISS vectorstore
            vectorstore = FAISS.from_documents(documents, self.embeddings)
            self.vector_stores[file_id] = vectorstore
            logger.info(f"Vector store created for {file_id}")
            return vectorstore
        except Exception as e:
            logger.error(f"Error creating vectorstore: {e}")
            raise

    def merge_vectorstores(self, file_ids: list):
        """Merge multiple vector stores"""
        try:
            if not file_ids:
                return None
            
            merged_store = self.vector_stores[file_ids[0]]
            for file_id in file_ids[1:]:
                if file_id in self.vector_stores:
                    merged_store.merge_from(self.vector_stores[file_id])
            
            return merged_store
        except Exception as e:
            logger.error(f"Error merging vectorstores: {e}")
            raise

    def get_retriever(self, file_ids: list, search_kwargs: dict = None):
        """Get retriever for specified files"""
        try:
            if search_kwargs is None:
                search_kwargs = {"k": 5}
            
            merged_store = self.merge_vectorstores(file_ids)
            return merged_store.as_retriever(search_kwargs=search_kwargs)
        except Exception as e:
            logger.error(f"Error getting retriever: {e}")
            raise