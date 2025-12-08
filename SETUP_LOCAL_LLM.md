# Free Local LLM Setup Guide (বাংলা)

## 🚀 দ্রুত সেটআপ (Ollama - Recommended)

### Step 1: Ollama ইনস্টল করুন
1. https://ollama.ai থেকে Ollama ডাউনলোড করুন
2. Windows/Mac/Linux এর জন্য installer চালান
3. Terminal/Command Prompt খুলুন

### Step 2: Model ডাউনলোড করুন
```bash
# Fast এবং ভাল quality এর জন্য (Recommended)
ollama pull llama3.2

# অথবা আরো ছোট model (দ্রুত কিন্তু কম quality)
ollama pull mistral

# অথবা আরো ভাল quality (ধীর কিন্তু ভাল)
ollama pull llama3
```

### Step 3: .env ফাইলে যোগ করুন
`.env` ফাইলে এই লাইনগুলো যোগ করুন:
```
USE_LOCAL_LLM=true
LOCAL_LLM_TYPE=ollama
LOCAL_LLM_MODEL=llama3.2
USE_FREE_EMBEDDINGS=true
```

### Step 4: App Restart করুন
Streamlit app restart করুন এবং test করুন!

## 📊 Model Comparison

| Model | Size | Speed | Quality | Command |
|-------|------|-------|---------|---------|
| llama3.2 | ~2GB | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | `ollama pull llama3.2` |
| mistral | ~4GB | ⚡⚡ Fast | ⭐⭐⭐⭐ Very Good | `ollama pull mistral` |
| llama3 | ~4.7GB | ⚡ Medium | ⭐⭐⭐⭐⭐ Excellent | `ollama pull llama3` |

## 🔧 Alternative: HuggingFace Models

যদি Ollama কাজ না করে, HuggingFace ব্যবহার করতে পারেন:

### .env ফাইলে:
```
USE_LOCAL_LLM=true
LOCAL_LLM_TYPE=huggingface
LOCAL_LLM_MODEL=microsoft/DialoGPT-medium
USE_FREE_EMBEDDINGS=true
```

### Install dependencies:
```bash
pip install transformers accelerate
```

## ✅ Benefits

- ✅ **100% FREE** - কোনো API key লাগবে না
- ✅ **Fast** - Local এ run করে তাই দ্রুত
- ✅ **Private** - আপনার data কখনো internet এ যাবে না
- ✅ **No Quota** - Unlimited use

## 🎯 Recommended Settings

সবচেয়ে ভাল performance এর জন্য `.env` ফাইলে:
```
USE_LOCAL_LLM=true
LOCAL_LLM_TYPE=ollama
LOCAL_LLM_MODEL=llama3.2
USE_FREE_EMBEDDINGS=true
```

এখন আপনার app সম্পূর্ণ free এবং fast হবে! 🚀

