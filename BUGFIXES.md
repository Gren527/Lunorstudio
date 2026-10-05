# Lunor App Studio — UI Stability Fixes

This build fixes the Plan and Learning Path black-screen issues.

## What changed
- Added defensive normalization for AI Plan output on the FastAPI backend.
- Added defensive normalization for AI Learning Path output on the FastAPI backend.
- Added frontend guards for arrays/objects returned by Llama 3.
- Learning lessons now use stable fallback IDs, so malformed/missing IDs cannot break lesson expansion.
- Topics/resources are safely rendered even when Llama returns an unexpected JSON shape.
- Added a React Error Boundary so an unexpected malformed AI response cannot blank the entire application.
- Existing localStorage project data is preserved.

## Run
Backend:
```powershell
cd backend
python -m uvicorn main:app --reload --port 8000
```

Frontend:
```powershell
cd frontend
npm install
npm run dev
```

If you already had the app open, use Ctrl+Shift+R after replacing the files.
