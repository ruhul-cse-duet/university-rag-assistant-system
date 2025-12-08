import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DB_DIR = "data"

# Get OpenAI API key from environment variable (optional if using free embeddings)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Check if using free embeddings
USE_FREE_EMBEDDINGS = os.getenv("USE_FREE_EMBEDDINGS", "false").lower() == "true"

# Check if using local LLM
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

# Only require API key if not using free alternatives
if not USE_FREE_EMBEDDINGS and not USE_LOCAL_LLM and not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found. Please set it as an environment variable "
        "or create a .env file with OPENAI_API_KEY=your_key_here\n"
        "Alternatively, set USE_FREE_EMBEDDINGS=true and USE_LOCAL_LLM=true "
        "to use completely free local models (no API key needed)."
    )
