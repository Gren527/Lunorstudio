# Lunor App Studio — Final Challenge Build

**Flow:** Prompt → Understand → Plan → Build → Explain → Learn

This prototype uses **Ollama + Llama 3 locally** as the only AI provider. The frontend is React/Vite and the API is FastAPI. The generated app is a structured app definition rendered by React, which keeps the prototype reliable while allowing the AI to control screens, content and interactions.

## Local run (Windows)

### 1. Ollama
Make sure Ollama is installed and the model exists:

```powershell
ollama list
ollama run llama3:latest
```

Do **not** run `ollama serve` if Ollama is already running; the Windows app normally starts the service for you.

### 2. Backend
Use Python 3.11.

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

Set `.env` to:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3:latest
OLLAMA_TIMEOUT=300
CORS_ORIGINS=http://localhost:5173
```

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (normally `http://localhost:5173`).

## Production architecture recommended for the challenge

- **Frontend:** Vercel (React/Vite static deployment)
- **Backend:** Render Web Service (FastAPI)
- **AI:** Ollama + `llama3:latest` on a separate GPU machine/server
- Render's `OLLAMA_BASE_URL` must point to the **HTTPS-reachable Ollama gateway/server**, not `127.0.0.1`.
- Set `CORS_ORIGINS` to the exact Vercel frontend URL.

Railway/Render CPU instances should not be expected to run a production-sized local Llama model. Keep inference on a GPU server and let the FastAPI backend call it over HTTPS.

## Render backend settings

Root directory: `backend`

Build command:
`pip install -r requirements.txt`

Start command:
`uvicorn main:app --host 0.0.0.0 --port $PORT`

Environment variables:

- `AI_PROVIDER=ollama`
- `OLLAMA_BASE_URL=https://YOUR-OLLAMA-GATEWAY`
- `OLLAMA_MODEL=llama3:latest`
- `OLLAMA_TIMEOUT=300`
- `CORS_ORIGINS=https://YOUR-VERCEL-APP.vercel.app`

## Vercel frontend

Set the project root to `frontend` and add:

`VITE_API_URL=https://YOUR-RENDER-API.onrender.com`

Build command: `npm run build`

Output directory: `dist`

## Important security note

Do not expose port 11434 directly to the public internet without authentication/TLS. Put Ollama behind a private network or authenticated HTTPS gateway. The browser talks only to FastAPI; the FastAPI server talks to Ollama.

## What is genuinely AI-driven

- Understand: requirements/users/features/questions
- Plan: stack/screens/data/architecture/security/build order
- Build: complete app definition generated from the current project
- Modify: edits the current generated app and preserves unrelated parts
- Explain: project-aware architecture and screen walkthrough
- Learn: project-specific lessons/resources/practice

There is intentionally **no generic-app fallback** for AI generation. If Ollama is unavailable or returns invalid data, the API reports the failure instead of silently replacing the user's app with a canned template.
