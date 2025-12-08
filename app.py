import streamlit as st
# Load environment variables and validate API key
import pkg_resources
from app_utils import config
from app_utils.scraper import scrape_website
from app_utils.vectorstore import save_to_vector_db
from app_utils.rag_pipeline import ask_rag

st.title("📚 University RAG Assistant")

univ = st.text_input("University short name (example: du, cu, buet):")
url = st.text_input("University website URL:")

# Advanced crawl controls so you can index full sites (notices, news, events, academics, etc.)
with st.expander("Advanced crawl options (optional)"):
    max_pages = st.number_input("Max HTML pages to crawl", min_value=10, max_value=2000, value=400, step=50)
    max_pdfs = st.number_input("Max PDFs to fetch", min_value=0, max_value=500, value=120, step=10)
    pdf_max_mb = st.number_input("Max PDF size (MB)", min_value=1, max_value=50, value=15, step=1)
    same_domain = st.checkbox("Stay within same domain", value=True)

if st.button("Build / Update Database"):
    if not univ:
        st.error("Please enter a university short name.")
    elif not url:
        st.error("Please enter a university website URL.")
    else:
        try:
            with st.spinner("Scraping website..."):
                text = scrape_website(
                    url,
                    max_pages=int(max_pages),
                    max_pdfs=int(max_pdfs),
                    same_domain=bool(same_domain),
                    pdf_max_mb=int(pdf_max_mb),
                )
            
            if not text or len(text.strip()) == 0:
                st.error("No text content found on the website. Please check the URL.")
            else:
                with st.spinner(f"Building vector database for {univ}..."):
                    save_to_vector_db(univ, text)
                st.success(f"✅ Vector DB created successfully for {univ}!")
        except Exception as e:
            error_msg = str(e)
            
            # Check for OpenAI API quota errors
            if "429" in error_msg or "insufficient_quota" in error_msg.lower() or "exceeded your current quota" in error_msg.lower():
                st.error("❌ **OpenAI API Quota Exceeded**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.warning("""
                    **Option 1: Fix OpenAI Quota**
                    
                    To resolve this issue:
                    1. Check your OpenAI account billing and usage at: https://platform.openai.com/usage
                    2. Add payment method or increase your quota at: https://platform.openai.com/account/billing
                    3. Wait for your quota to reset (if you have a rate limit)
                    4. Consider upgrading your OpenAI plan if you need higher limits
                    
                    For more information: https://platform.openai.com/docs/guides/error-codes/api-errors
                    """)
                
                with col2:
                    st.info("""
                    **Option 2: Use FREE Local Models (No Quota!)**
                    
                    Switch to completely free local models:
                    
                    **For Embeddings:**
                    1. `pip install sentence-transformers torch`
                    2. Add to `.env`: `USE_FREE_EMBEDDINGS=true`
                    
                    **For LLM (ChatGPT replacement):**
                    1. Install Ollama: https://ollama.ai
                    2. Run: `ollama pull llama3.2`
                    3. Add to `.env`:
                       ```
                       USE_LOCAL_LLM=true
                       LOCAL_LLM_TYPE=ollama
                       LOCAL_LLM_MODEL=llama3.2
                       ```
                    
                    4. Restart the app
                    
                    **Now everything is FREE and FAST!** 🚀
                    """)
            elif "401" in error_msg or "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                st.error("❌ **OpenAI API Authentication Error**")
                st.warning("""
                **Invalid or missing OpenAI API key.**
                
                Please check:
                1. Your `.env` file contains a valid `OPENAI_API_KEY`
                2. The API key is correct and active
                3. You have access to the OpenAI API
                
                Get your API key from: https://platform.openai.com/api-keys
                """)
            else:
                st.error(f"❌ Error building database: {error_msg}")
                if "null bytes" in error_msg.lower():
                    st.info("💡 Tip: If you see a 'null bytes' error, the old data directory may need manual deletion.")

question = st.text_input("Ask a question:")

if st.button("Get Answer"):
    if not univ:
        st.error("Please enter a university short name first.")
    elif not question:
        st.error("Please enter a question.")
    else:
        try:
            with st.spinner("Searching and generating answer..."):
                ans = ask_rag(univ, question)
            st.write("### 🧠 Answer:")
            st.write(ans)
        except Exception as e:
            error_msg = str(e)
            
            # Check for OpenAI API quota errors
            if "429" in error_msg or "insufficient_quota" in error_msg.lower() or "exceeded your current quota" in error_msg.lower():
                st.error("❌ **OpenAI API Quota Exceeded**")
                st.warning("""
                **Your OpenAI API quota has been exceeded.**
                
                To resolve this issue:
                1. Check your OpenAI account billing and usage at: https://platform.openai.com/usage
                2. Add payment method or increase your quota at: https://platform.openai.com/account/billing
                3. Wait for your quota to reset (if you have a rate limit)
                4. Consider upgrading your OpenAI plan if you need higher limits
                """)
            elif "401" in error_msg or "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                st.error("❌ **OpenAI API Authentication Error**")
                st.warning("Please check your OpenAI API key in the `.env` file.")
            else:
                st.error(f"❌ Error getting answer: {error_msg}")
                if "not found" in error_msg.lower() or "build the database" in error_msg.lower():
                    st.info("💡 Please build the database first using 'Build / Update Database'.")


#  streamlit run app.py