# Campus Customs — Homework 5

Multi-agent app with an MCP server, a FastAPI backend running a team of agents, and a React dashboard.

> Placeholder — details will be added as the homework progresses.

## Structure

- `data/` — SQLite database (`campus_customs.db`)
- `mcp_server/` — MCP server
- `backend/` — FastAPI backend and agents (`backend/prompts/` for agent prompts)
- `frontend/` — React + Vite + TypeScript dashboard
- `output/` — generated output

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your Portkey API key
cd frontend && npm install
```
