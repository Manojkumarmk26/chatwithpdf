from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

class QAChain:
    def __init__(self, llm, reranker):
        self.llm = llm
        self.reranker = reranker

    def create_qa_chain(self, retriever):
        """Create QA chain with retriever and LLM"""
        try:
            prompt_template = """Use the following pieces of context to answer the question. 
            If you don't know the answer, say so.

Context:
{context}

Question: {question}

Answer:"""
            
            PROMPT = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )
            
            return qa_chain
        except Exception as e:
            logger.error(f"Error creating QA chain: {e}")
            raise

    def answer_query(self, qa_chain, query: str) -> dict:
        """Answer query using QA chain"""
        try:
            result = qa_chain({"query": query})
            return {
                "answer": result.get("result"),
                "sources": result.get("source_documents", [])
            }
        except Exception as e:
            logger.error(f"Error answering query: {e}")
            raise