# University RAG Assistant

Streamlit app to scrape a university website (HTML + PDFs), build a Chroma vector database, and answer questions with a RAG pipeline using OpenAI or local models.

## Features
- One-click crawl + indexing per university short name.
- RAG Q&A with language-aware prompting (answers in the user’s question language).
- Works with OpenAI or free local embeddings/LLMs (Ollama/HF).
- Adjustable crawl scope (pages, PDFs, size limits, same-domain toggle).

## Quickstart
```bash
python -m venv .venv
source .venv/Scripts/activate  # on Windows use .venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:
```
OPENAI_API_KEY=sk-...
# Optional free embeddings
USE_FREE_EMBEDDINGS=true
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
# Optional local LLM via Ollama
USE_LOCAL_LLM=true
LOCAL_LLM_TYPE=ollama
LOCAL_LLM_MODEL=llama3.2
```

Run the app:
```bash
streamlit run app.py
```

## Using the app
1. Enter a university short name (e.g., `duet`) and the root URL (e.g., `https://www.duet.ac.bd/`).
2. (Optional) Expand “Advanced crawl options” to adjust max pages/PDFs or domain restriction.
3. Click **Build / Update Database** to scrape, chunk, embed, and store in `data/<shortname>`.
4. Ask questions with **Get Answer**. Answers are constrained to retrieved context; if missing, it will say it lacks information.

## Notes
- Rebuilding recreates the vector DB with the latest site content and current crawl settings.
- For Bangla/English content, keep the multilingual embedding model (default above).
- If using local models, install the extras noted in `requirements.txt` comments (sentence-transformers/torch for embeddings; Ollama or transformers/accelerate for LLMs).
