"""
Embedding provider with support for both OpenAI and free local embeddings.
"""
import os
from .config import OPENAI_API_KEY

# Check if user wants to use free embeddings
USE_FREE_EMBEDDINGS = os.getenv("USE_FREE_EMBEDDINGS", "false").lower() == "true"
# Allow overriding the local embedding model (default is multilingual for better Bangla support)
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

def get_embeddings():
    """
    Get embeddings model. Uses free local embeddings if USE_FREE_EMBEDDINGS=true,
    otherwise uses OpenAI embeddings.
    """
    if USE_FREE_EMBEDDINGS:
        # Use the langchain_community implementation (works with our pinned LangChain)
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(
                # Multilingual model to handle Bangla + English notices
                model_name=EMBEDDING_MODEL_NAME,
                model_kwargs={'device': 'cpu'},  # Use 'cuda' if you have GPU
                encode_kwargs={'normalize_embeddings': True}
            )
        except ImportError as e:
            raise ImportError(
                "HuggingFace embeddings not installed. "
                "Install with: pip install sentence-transformers torch\n"
                f"Original error: {str(e)}"
            )
    else:
        # Use OpenAI embeddings (requires API key and has quota)
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not found. Either set it in .env file "
                "or set USE_FREE_EMBEDDINGS=true to use free local embeddings."
            )
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=OPENAI_API_KEY
        )
