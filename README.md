# SupporBot

SupporBot is a full-stack AI document assistant that lets users upload PDF files and ask natural-language questions about their contents. It uses Retrieval-Augmented Generation with Google Gemini, LangChain, PostgreSQL, and pgvector to retrieve relevant document chunks and generate grounded answers with source references.

The application includes a Django REST API for PDF processing, embedding, retrieval, and agentic tool calling, plus a React/Vite frontend for uploading documents and chatting with the assistant.

## Features

- PDF upload and text extraction
- Document chunking and semantic embedding
- Vector search with PostgreSQL and pgvector
- Gemini-powered answers grounded in uploaded document content
- Tool-calling workflow for document search and document summaries
- Basic agent loop for multi-step questions
- Source chunks with page number, chunk index, score, and content preview
- Clean React chat interface with upload, loading, source, and tool-used states

## Tech Stack

### Backend

- Django
- Django REST Framework
- LangChain
- Google Gemini
- PostgreSQL
- pgvector
- pdfplumber

### Frontend

- React
- Vite
- Tailwind CSS
- lucide-react

## Project Structure

```text
support-bot-project/
├── backend/
│   ├── api/
│   │   ├── langchain_rag.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── core/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## How It Works

1. A user uploads a PDF from the frontend.
2. The backend extracts text from each PDF page.
3. Extracted text is cleaned, split into chunks, and stored with metadata.
4. Each chunk is embedded and saved in PostgreSQL with pgvector.
5. The user asks a question in the chat interface.
6. Gemini can call document tools such as:
   - `get_document_summary()` for overview questions
   - `search_document(query)` for specific document searches
7. The backend executes the requested tool and returns the result to Gemini.
8. Gemini generates a final answer using the retrieved document context.
9. The frontend displays the answer, tools used, and source chunks.

## API Endpoints

Base URL:

```text
http://localhost:8000/api
```

### Health Check

```http
GET /api/health/
```

### Upload PDF

```http
POST /api/upload/
```

Example:

```bash
curl -X POST http://localhost:8000/api/upload/ \
  -F "file=@/path/to/document.pdf"
```

### Ask Question

```http
POST /api/ask/
```

Example:

```bash
curl -X POST http://localhost:8000/api/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

Example response:

```json
{
  "question": "What is this document about?",
  "answer": "This document is a resume for a Python FullStack Developer.",
  "sources": [
    {
      "page": 1,
      "chunk_index": 0,
      "source": "resume.pdf",
      "score": 0.367,
      "content": "SUMMARY..."
    }
  ],
  "tools_used": ["get_document_summary"]
}
```

## Local Development

Start PostgreSQL with pgvector:

```bash
cd backend
docker compose up db
```

Run the backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Backend:

```text
http://localhost:8000
```

Frontend:

```text
http://localhost:5173
```

## Development Commands

Backend syntax check:

```bash
env PYTHONPYCACHEPREFIX=/tmp python3 -m py_compile backend/api/langchain_rag.py backend/api/views.py
```

Frontend lint:

```bash
cd frontend
npm run lint
```

Frontend build:

```bash
cd frontend
npm run build
```
