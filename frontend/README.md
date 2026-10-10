# Campus Customs Agent Desk (frontend)

React + Vite + TypeScript dashboard for the Campus Customs agent team. It calls the FastAPI backend at `http://localhost:8000` (override with `VITE_API_URL`).

```bash
npm install
npm run dev     # http://localhost:5173
```

Start the backend first: `cd ../backend && ../.venv/bin/uvicorn main:app --reload --port 8000`. Design notes are in `../output/design.md`.
