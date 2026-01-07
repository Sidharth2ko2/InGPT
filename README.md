InGPT: RAG-Powered Document Assistant

A Retrieval-Augmented Generation (RAG) system that allows users to chat with large documents (PDF/TXT) using local LLMs. It breaks down books into manageable chunks, indexes them, and retrieves context to provide accurate, grounded answers.

## Key Features
- **Semantic Chunking:** Automatically segments large books into context-aware snippets.
- **Local Embedding & Retrieval:** Uses `nomic-embed-text` and **ChromaDB** for fast, local vector search.
- **AI-Powered Chat:** Integrates with **Ollama (Llama 3.1)** to generate responses based on book content.
- **Context Grounding:** Prevents hallucinations by forcing the AI to use only the provided text.

## Tech Stack
- **Backend:** Python, FastAPI, ChromaDB, Ollama.
- **Frontend:** React, TypeScript, Tailwind CSS.
- **AI Models:** Llama 3.1 (Generation), Nomic-Embed-Text (Embeddings).

## Installation & Setup
1. **Ollama:** Ensure Ollama is running (`ollama run llama3.1`).
2. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload --port 8000
3. **Frontend:**
   ```Bash
   cd frontend
   npm install
   npm run dev
