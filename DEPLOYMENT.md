# Deployment checklist

1. Push this folder to GitHub.
2. Deploy `frontend` to Vercel.
3. Deploy `backend` to Render as a Python Web Service.
4. Put Ollama + Llama 3 on a GPU server. Keep it behind HTTPS/authentication.
5. In Render, set `OLLAMA_BASE_URL` to the secure Ollama gateway and `CORS_ORIGINS` to the Vercel URL.
6. In Vercel, set `VITE_API_URL` to the Render URL.
7. Test `https://YOUR-RENDER-URL/api/health`; it should show `ai_enabled: true`.
8. Test the full flow: Understand → Plan → Build → Modify → Explain → Learn.
9. Submit both the public app URL and source repository URL.
