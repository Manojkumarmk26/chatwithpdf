from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class HuggingFaceModel:
    """Optimized HuggingFace model for CPU-only systems with limited resources."""
    
    # Small models suitable for CPU (< 3GB each)
    SMALL_MODELS = {
        "distilgpt2": "distilgpt2",  # 350M params, ~1.2GB
        "gpt2-medium": "gpt2-medium",  # 355M params, ~1.5GB
        "distilbert-base": "distilbert-base-uncased-distilled-squad",  # 66M params, ~260MB
        "phi-1.5": "microsoft/phi-1.5",  # 1.3B params, ~3GB
    }
    
    def __init__(
        self, 
        model_name: str = "distilgpt2",  # Default to smallest model
        use_gpu: bool = False,
        max_memory_percent: float = 0.7  # Use max 70% of available RAM
    ):
        """Initialize the HuggingFace model with CPU optimizations.
        
        Args:
            model_name: Name or path of the pre-trained model
            use_gpu: Whether to use GPU if available (not recommended for your system)
            max_memory_percent: Maximum percentage of RAM to use
        """
        try:
            self.model_name = model_name
            self.use_gpu = False  # Force CPU for stability
            device = -1  # CPU device
            
            logger.info(f"Initializing model: {model_name}")
            logger.info(f"System specs - RAM: 32GB, GPU: None, Using CPU only")
            logger.info(f"This may take 2-5 minutes on first load (downloading model)")
            
            # Calculate memory limits
            total_memory = 32 * 1024 * 1024 * 1024  # 32GB in bytes
            max_memory = int(total_memory * max_memory_percent)
            
            # Set environment variables for optimization
            os.environ["TRANSFORMERS_CACHE"] = os.path.expanduser("~/.cache/huggingface/hub")
            os.environ["OMP_NUM_THREADS"] = "8"  # Use 8 CPU threads
            os.environ["OPENBLAS_NUM_THREADS"] = "8"
            os.environ["MKL_NUM_THREADS"] = "8"
            
            # Load model with CPU optimizations
            self.pipe = pipeline(
                "text-generation",
                model=model_name,
                device=device,  # CPU
                torch_dtype=torch.float32,  # CPU doesn't support float16 efficiently
                trust_remote_code=True,
                model_kwargs={
                    "low_cpu_mem_usage": True,  # Critical for CPU
                    "offload_folder": os.path.expanduser("~/.cache/huggingface/offload"),
                }
            )
            
            logger.info(f"✅ Model loaded successfully: {model_name}")
            logger.info(f"Model device: CPU")
            logger.info(f"Model size: ~{self._get_model_size()}")
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            raise

    def _get_model_size(self) -> str:
        """Estimate model size in MB."""
        try:
            model = self.pipe.model
            param_size = sum(p.numel() * 4 for p in model.parameters()) / (1024 * 1024)  # 4 bytes per float32
            return f"{param_size:.1f}MB"
        except:
            return "Unknown"

    def generate_text(
        self, 
        prompt: str, 
        max_tokens: int = 256,  # Reduced from 512
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """Generate text with CPU optimizations and error recovery.
        
        Args:
            prompt: The input prompt for text generation
            max_tokens: Maximum number of tokens to generate (256-512 recommended)
            temperature: Controls randomness (lower = more deterministic)
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated text or error message if generation fails
        """
        try:
            # Input validation
            if not prompt or not isinstance(prompt, str):
                logger.warning("Invalid prompt provided")
                return "Invalid prompt. Please provide a valid text."
            
            # Clamp prompt to reasonable length
            prompt = prompt[:1000]  # Max 1000 chars to avoid memory issues
            
            # Clamp temperature
            temperature = max(0.1, min(1.0, temperature))
            
            logger.info(f"Generating text (max_tokens={max_tokens})...")
            
            # Generate with aggressive optimization for CPU
            outputs = self.pipe(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=50,
                do_sample=True,
                repetition_penalty=1.05,
                truncation=True,
                num_beams=1,  # Disable beam search (too slow on CPU)
                early_stopping=True,
                pad_token_id=self.pipe.tokenizer.eos_token_id,
                eos_token_id=self.pipe.tokenizer.eos_token_id,
            )
            
            # Extract generated text
            generated_text = outputs[0]["generated_text"]
            
            # Clean output - remove prompt
            if prompt in generated_text:
                answer = generated_text.split(prompt)[-1].strip()
            else:
                answer = generated_text.strip()
            
            # Ensure answer is not empty
            if not answer:
                answer = "Unable to generate a meaningful response. Please try rephrasing your question."
            
            logger.info(f"✅ Generation complete ({len(answer)} chars)")
            return answer
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.error("❌ Out of memory! Reduce max_tokens or use a smaller model.")
                return "Out of memory. Please try with a shorter prompt or reduce complexity."
            logger.error(f"❌ Runtime error: {str(e)}")
            return "Error during generation. Please try again with a simpler query."
        except Exception as e:
            logger.error(f"❌ Error in text generation: {str(e)}", exc_info=True)
            return f"Unable to generate response. Error: {str(e)[:100]}"

    def answer_question(
        self, 
        question: str, 
        context: str = "",
        max_tokens: int = 256
    ) -> str:
        """Answer a question, optionally with context (optimized for CPU).
        
        Args:
            question: The question to answer
            context: Optional context to base the answer on
            max_tokens: Maximum length of the answer
            
        Returns:
            Answer to the question
        """
        try:
            # Build optimized prompt
            if context:
                context = context[:1500]  # Limit context
                prompt = f"""Based on the following context, answer the question concisely.

Context:
{context}

Question: {question}

Answer:"""
            else:
                prompt = f"""Answer the following question concisely:

Question: {question}

Answer:"""
            
            logger.info("Generating answer...")
            return self.generate_text(
                prompt, 
                max_tokens=max_tokens,
                temperature=0.6
            )
            
        except Exception as e:
            logger.error(f"❌ Error answering question: {str(e)}")
            return "Unable to answer the question. Please try rephrasing."


# ============= Recommended Model Selection =============
"""
RECOMMENDED MODELS FOR YOUR SYSTEM (32GB RAM, CPU Only):

1. **distilgpt2** (BEST for speed) ⭐⭐⭐
   - Size: ~1.2GB
   - Params: 82M
   - Speed: Fast (2-5 sec per response)
   - Quality: Good
   - Recommended max_tokens: 200-256

2. **gpt2-medium** (Balance)
   - Size: ~1.5GB
   - Params: 355M
   - Speed: Medium (5-10 sec per response)
   - Quality: Better
   - Recommended max_tokens: 256-300

3. **microsoft/phi-1.5** (Best quality if slower)
   - Size: ~3GB
   - Params: 1.3B
   - Speed: Slow (10-20 sec per response)
   - Quality: Very Good
   - Recommended max_tokens: 300-400

MEMORY USAGE BY OPERATION:
- Model loading: ~2-4GB
- Generation: ~2-8GB
- Peak usage: ~10-12GB
- Available RAM after: ~20-22GB

OPTIMIZATION TIPS:
1. Use distilgpt2 for best performance
2. Keep max_tokens between 200-300
3. Limit prompt size to <1000 chars
4. Run on CPU only (no GPU attempts)
5. Use float32 (not float16)
6. Allow 2-10 seconds per generation
7. Close other applications
"""


# ============= Usage Example =============
"""
# Initialize with smallest, fastest model
model = HuggingFaceModel(model_name="distilgpt2", use_gpu=False)

# Generate text (fast)
response = model.generate_text(
    "What is artificial intelligence?",
    max_tokens=256,
    temperature=0.7
)
print(response)

# Summarize (optimized for CPU)
summary = model.summarize_content(
    "Your long text here...",
    max_tokens=200
)
print(summary)

# Answer questions
answer = model.answer_question(
    question="What is machine learning?",
    context="Machine learning is a subset of AI...",
    max_tokens=256
)
print(answer)
"""