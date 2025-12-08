"""
RAG Pipeline with support for both OpenAI and free local LLMs.
"""
import os
from langchain_core.documents import Document  # avoid deprecated langchain.schema
from .vectorstore import load_collection
from .embeddings import get_embeddings
from .config import OPENAI_API_KEY

# Check if using local LLM
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
LOCAL_LLM_TYPE = os.getenv("LOCAL_LLM_TYPE", "ollama").lower()  # "ollama" or "huggingface"
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama3.2")  # For Ollama: llama3.2, mistral, etc.


def get_llm():
    """
    Get LLM model. Uses local LLM if USE_LOCAL_LLM=true, otherwise uses OpenAI.
    """
    if USE_LOCAL_LLM:
        if LOCAL_LLM_TYPE == "ollama":
            try:
                # Try ChatOllama first (newer API)
                try:
                    from langchain_community.chat_models import ChatOllama
                    # Ollama is fast and free - runs locally
                    # Make sure Ollama is installed and running: https://ollama.ai
                    return ChatOllama(
                        model=LOCAL_LLM_MODEL,  # llama3.2, mistral, llama2, etc.
                        temperature=0.7,
                        num_predict=512  # Limit response length for speed
                    )
                except ImportError:
                    # Fallback to older Ollama API
                    from langchain_community.llms import Ollama
                    return Ollama(
                        model=LOCAL_LLM_MODEL,
                        temperature=0.7,
                        num_predict=512
                    )
            except ImportError:
                raise ImportError(
                    "Ollama not available. Install Ollama from https://ollama.ai\n"
                    "Then run: ollama pull llama3.2"
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to connect to Ollama. Make sure Ollama is running.\n"
                    f"Install from: https://ollama.ai\n"
                    f"Then run: ollama pull {LOCAL_LLM_MODEL}\n"
                    f"Error: {str(e)}"
                )
        elif LOCAL_LLM_TYPE == "huggingface":
            try:
                from langchain_community.llms import HuggingFacePipeline
                from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
                import torch
                
                model_name = LOCAL_LLM_MODEL or "microsoft/DialoGPT-medium"
                
                # Load model (will download on first use)
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None
                )
                
                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=256,
                    temperature=0.7,
                    do_sample=True
                )
                
                return HuggingFacePipeline(pipeline=pipe)
            except ImportError:
                raise ImportError(
                    "HuggingFace transformers not installed. "
                    "Install with: pip install transformers accelerate"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load HuggingFace model: {str(e)}")
        else:
            raise ValueError(f"Unknown LOCAL_LLM_TYPE: {LOCAL_LLM_TYPE}. Use 'ollama' or 'huggingface'")
    else:
        # Use OpenAI LLM (requires API key and has quota)
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not found. Either set it in .env file "
                "or set USE_LOCAL_LLM=true to use free local LLM."
            )
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=OPENAI_API_KEY,
            temperature=0.7
        )


def ask_rag(university: str, query: str):
    """
    Ask a question using RAG pipeline with vector search and LLM.
    """
    collection = load_collection(university)
    embedding = get_embeddings()

    # Get query embedding
    query_vec = embedding.embed_query(query)

    # Search for relevant documents
    results = collection.query(
        query_embeddings=[query_vec],
        n_results=5
    )

    docs = [Document(page_content=txt) for txt in results["documents"][0]]

    # Get LLM
    llm = get_llm()

    # Prepare context
    joined = "\n\n".join([d.page_content for d in docs])

    # Create prompt
    prompt = f"""You are a concise University AI Assistant.
Use ONLY the context below. If the answer is not in the context, reply exactly: "I don't have enough information to answer this question based on the provided context."

CRITICAL RULES:
- Do NOT invent, guess, or make up any URLs, links, or website addresses.
- Only use URLs/links that are EXACTLY written in the context below.
- If no URL is mentioned in the context, do NOT provide any URL in your answer.
- Do NOT modify or correct URLs - use them exactly as they appear in context.

Language:
- Reply ONLY in the language of the user question. If mixed, use the last/dominant language.
- Do NOT add any other language.
- Keep names exactly as in context (no translation/transliteration).

Output format:
- Return ONLY the answer sentence; no preamble or bullet points.
- If mentioning URLs, copy them EXACTLY from the context.

Context:
{joined}

Question: {query}

Answer:"""

    # Get response with better error messaging for local LLMs (e.g., Ollama)
    try:
        response = llm.invoke(prompt)
    except Exception as e:
        msg = str(e)
        if USE_LOCAL_LLM and "ollama" in msg.lower():
            raise RuntimeError(
                "Ollama failed to generate a response. "
                "Common fixes:\n"
                "1) Ensure Ollama service is running.\n"
                "2) Pull the model you set in LOCAL_LLM_MODEL (default: llama3.2):\n"
                "   ollama pull llama3.2\n"
                "3) If it still fails, try a lighter model:\n"
                "   LOCAL_LLM_MODEL=mistral   (then: ollama pull mistral)\n"
                "4) Restart Ollama service after pulling the model."
            )
        raise

    # Handle different response types
    if hasattr(response, 'content'):
        # ChatOllama, ChatOpenAI return objects with content
        return response.content
    elif isinstance(response, str):
        # Direct string response
        return response
    else:
        # Fallback
        return str(response)
