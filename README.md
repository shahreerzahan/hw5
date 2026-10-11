# Campus Customs: Multi-Agent Operations (Homework 5)

A five-agent team (Boss, Inventory, Accounting, Facilities, Customer Service) that works the Campus Customs shop's tickets:

- **MCP server** (`mcp_server/`): the agents' only access to shop data.
- **FastAPI backend** (`backend/`): runs the agents and handles human approvals.
- **React dashboard** (`frontend/`): where a person watches the agents and approves payments.

Every agent uses **gpt-6-luna** through Portkey. Agents can only *queue* payments; cash moves only when a human clicks Approve.

## Project layout

```
hw5/
├── AI_prompts.md          prompts I typed to the vibe coder, per problem
├── requirements.txt       Python dependencies
├── .env.example           copy to .env and add your Portkey key
├── .mcp.json              registers the MCP server with the vibe coder
├── data/
│   ├── campus_customs.db      original database (never modified)
│   └── campus_customs_new.db  working copy the agents and dashboard update
├── mcp_server/            FastMCP server (server.py) + README
├── backend/               FastAPI app (main.py), agent team (agents.py), data types (models.py), prompts/
├── frontend/              React + Vite + TypeScript dashboard
└── output/                harness.md, mcp_smoke.json, desk_tickets.html, design.md,
                           resolved_tickets.json, resolved_board.html, audit_trail.json, github_url.txt
```

The committed `campus_customs_new.db` is the state after my three-ticket run: all tickets resolved and checking at $152. Reset it (step 2) before your own run.

## 1. Setup (once)

Needs Python 3.12+ and Node 20+. Run from the project root (`hw5/`):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `PORTKEY_API_KEY`. Leave `MODEL_NAME=gpt-6-luna`; the backend refuses to start with any other model. Then install the dashboard:

```bash
cd frontend && npm install && cd ..
```

## 2. Reset the working database (before every full run)

Copy the original database over the working copy for a clean run (checking back to $3,400, all three tickets open):

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

The MCP server re-adds its two helper tables (`approval_queue`, `message_drafts`) the next time it starts. Once the backend is running, you can do the same reset from the dashboard (**Reset shop data**) or with:

```bash
curl -X POST http://localhost:8000/api/reset
```

**Always reset before a full three-ticket run (101, 102, 103)**, so the cash and ticket statuses start from the original values. The reset never clears `output/audit_trail.json`, which only grows.

## 3. Start the MCP server

The server works on `data/campus_customs_new.db`.

- **The agent team starts it for you.** The backend launches `mcp_server/server.py` over stdio for each run, so you don't need to start it by hand to use the app.
- **To run it on its own** (for example, to test the tools):

  ```bash
  .venv/bin/python mcp_server/server.py
  ```

- **In Claude Code,** `.mcp.json` registers it as `campus-customs`. Open the project and approve the server to call its tools directly.

See `mcp_server/README.md` for the full tool list.

## 4. Start the FastAPI backend

```bash
cd backend
../.venv/bin/uvicorn main:app --reload --port 8000
```

The API is at http://localhost:8000, with interactive docs at http://localhost:8000/docs. It allows the dashboard's origin, http://localhost:5173. The routes are listed in `output/harness.md`.

## 5. Start the React board

In a second terminal:

```bash
cd frontend
npm run dev
```

Open http://localhost:5173. Then for each ticket:

1. Pick a ticket and click **Run the team**.
2. Watch the agents work in the conversation.
3. Approve or reject anything under **Needs you**.

The checking balance in the header drops after each approved payment. Only one ticket can run at a time.

## Results and write-ups

- `output/harness.md`: tables, MCP tools, agents, routes, dashboard, safety rules and token limits.
- `output/desk_tickets.html`: expected vs actual for each ticket, the Cash tab, and my reflection. Double-click to open it.
- `output/resolved_board.html`: screenshots of the three resolved tickets.
- `output/resolved_tickets.json`: per-ticket outcomes, what each agent did, and human approvals.
- `output/audit_trail.json`: every agent step from every run.
- `output/design.md`: the dashboard design.
