
# 📚 Automated Book Publication System

This project is a complete UI-based pipeline for scraping, rewriting, reviewing, editing, storing, and searching chapters (e.g., from Wikisource) using LLMs and human feedback. It consists of three main modules:

1. `automated_writer_ui.py` — Chapter scraping, rewriting, and reviewing with LLMs  
2. `human_loop.py` — Human-in-the-loop editing and finalization interface  
3. `chapter_store_manager.py` — Finalized chapter storage and semantic search using ChromaDB

---
To run in the terminal, run main.py only.
## 📁 Project Structure

```
project-root/
├── automated_writer_ui.py
├── human_loop.py
├── chapter_store_manager.py
├── data/
│   ├── raw/
│   ├── processed/
│   │   ├── spun/
│   │   ├── reviewed/
│   │   └── final/
│   └── screenshots/
├── chroma_store/
└── README.md
```

---

## 1️⃣ `automated_writer_ui.py` - AI Writer and Reviewer

### ✅ Features

- Input Wikisource chapter URL via Streamlit
- Scrapes title and content using Playwright
- Uses Ollama LLM to:
  - Rewrite the chapter in a modern style
  - Review the rewritten chapter
- Saves original, spun, and reviewed versions
- Final reviewed JSON downloadable via UI

### 🔧 Workflow

1. Scrape chapter → `data/raw/`
2. Rewrite via LLM → `data/processed/spun/`
3. Review via LLM → `data/processed/reviewed/`
4. Download reviewed version

---

## 2️⃣ `human_loop.py` - Human-in-the-Loop Chapter Editor

### ✅ Features

- Upload reviewed JSON
- View all stages: original, spun, reviewed
- Edit reviewed text & give comments
- Mark `"final"` to save finalized version

### 🧭 Output

- Finalized JSON → `data/processed/final/`
- Edited JSON → `data/processed/reviewed/`

---

## 3️⃣ `chapter_store_manager.py` - Chapter Storage & Search

### ✅ Features

- Upload finalized JSON to ChromaDB
- Store chapter content with metadata
- Search via sentence similarity using SentenceTransformer

### 🔍 Search Results

- Title, date, comment, similarity, excerpt, URL

---

## 🛠️ Requirements

```bash
pip install streamlit playwright ollama sentence-transformers chromadb
playwright install
```

---

## 🚀 Run the Apps

Each app runs on Streamlit in a separate terminal:

```bash
streamlit run automated_writer_ui.py
streamlit run human_loop.py
streamlit run chapter_store_manager.py
```

---

## 💾 JSON Format

```json
{
  "chapter_id": "book1_ch1",
  "title": "Chapter Title",
  "url": "...",
  "original_text": "...",
  "spun_text": "...",
  "reviewed_text": "...",
  "review_notes": "...",
  "final_text": "...",
  "human_comments": "...",
  "status": "raw|spun|reviewed|final"
}
```

---

## 💡 Use Cases

- AI-assisted book rewriting
- Human-AI collaborative editing
- Semantic chapter search
- AI publishing pipeline
