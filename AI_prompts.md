# AI Prompts – Homework 5

Log of the prompts I typed to the AI for each problem.

## Setup

### Prompt

> I'm starting Homework 5: a Campus Customs multi-agent app with an MCP server, a FastAPI backend with a team of agents, and a React dashboard. Please set up the project environment only; no features yet.
>
> 1. Create these folders: mcp_server/, backend/prompts/, frontend/, and output/. The data/ folder is already here, don't change it.
>
> 2. Create a .gitignore that ignores .env, .venv/, node_modules/, \_\_pycache\_\_/, and .DS_Store. Do NOT ignore the data/ folder, because the database files need to be in the repo for this homework.
>
> 3. Create .env.example with PORTKEY_API_KEY=your-portkey-api-key-here and MODEL_NAME=gpt-6-luna. My real key is already in .env, please never print it.
>
> 4. Set up a Python virtual environment and install fastapi, uvicorn, pydantic-ai, portkey-ai, python-dotenv, and fastmcp. Save requirements.txt in the main folder.
>
> 5. Set up a React + Vite + TypeScript app in the frontend folder.
>
> 6. Create AI_prompts.md with a heading for each of Problems 1 to 11, and a placeholder README.md.
>
> 7. Do a quick test call to gpt-6-luna through Portkey to make sure my key works, then delete the test file. Only use gpt-6-luna.
>
> 8. Set up git, commit, and push to my repo: https://github.com/shahreerzahan/hw5.git. Show me git status so I can check .env is not included.

## Problem 1: Vibe coder prompts

### Prompt

> Problem 1: Vibe Coder Prompts.
>
> Set up 'AI_prompts.md' as the log of what I type to you.
>
> Put one section for each problem (1 to 11) with the problem number and title. In each section, leave space for: the prompt I typed, a follow-up prompt if I needed one, and one sentence on what was lacking after the first.
>
> Put my setup prompt from earlier under a "Setup" section. Commit and push.

### Follow-up prompt

> Always add prompts to AI_prompts.md whether I ask or not.

### What was lacking after the first prompt

The AI set up the log but didn't keep adding my new prompts to it unless I asked each time.

## Problem 2: Study the Campus Customs database

### Prompt

> Problem 2: Study the Campus Customs Database.
>
> Open 'data/campus_customs.db' and look through every table and its fields. Copy the original file to 'data/campus_customs_new.db', since later problems will update that working copy.
>
> Study the three open tickets (101, 102, 103) and show me how they link to the other tables.
>
> Then 'start output/harness.md'. For each table, list the fields and one short line on why that table matters for the agents.
>
> Commit and push.

### Follow-up prompt

> _None._

### What was lacking after the first prompt

_Nothing; the first prompt was sufficient._

## Problem 3: Build the MCP server

### Prompt

> Problem 3: Write the MCP server
>
> Write an MCP server in 'mcp_server/server.py' using FastMCP. It should use 'data/campus_customs_new.db'. No need to connect or run it yet.
>
> For now, write three tools I know the tickets need:
>
> 1. check_stock: takes a sku and size, returns how many are in stock plus the cost and list price (inventory + pricing). Helps ticket 101 (white tee, size S) and 103 (navy hoodie, size M).
>
> 2. get_vendor_invoices: takes a vendor id, returns the vendor's details, lead time, and any open unpaid invoices (vendors + invoices). Helps ticket 101, because Bulldog Print Co won't ship while invoice 501 is unpaid.
>
> 3. get_lease: takes a lease id, returns the landlord, rent amount, and due date (leases). Helps ticket 102, the rent notice.
>
> Keep the names clear and never make up data, only use what's in the database.
>
> In output/harness.md, list each tool with: which table it reads, which ticket it helps (101, 102, or 103), and one sentence on why it's the right tool for that ticket.

### Follow-up prompt

> _None._

### What was lacking after the first prompt

_Nothing; the first prompt was sufficient._

## Problem 4: Add the MCP server to vibe coder and test each tool

### Prompt

> _To be added._

### Follow-up prompt

> _To be added (if needed)._

### What was lacking after the first prompt

_To be added (one sentence)._

## Problem 5: Build the agent team and grow the MCP tools

### Prompt

> _To be added._

### Follow-up prompt

> _To be added (if needed)._

### What was lacking after the first prompt

_To be added (one sentence)._

## Problem 6: Plan the three tickets

### Prompt

> _To be added._

### Follow-up prompt

> _To be added (if needed)._

### What was lacking after the first prompt

_To be added (one sentence)._

## Problem 7: Backend routes

### Prompt

> _To be added._

### Follow-up prompt

> _To be added (if needed)._

### What was lacking after the first prompt

_To be added (one sentence)._

## Problem 8: Agent dashboard

### Prompt

> _To be added._

### Follow-up prompt

> _To be added (if needed)._

### What was lacking after the first prompt

_To be added (one sentence)._

## Problem 9: Resolve the tickets

### Prompt

> _To be added._

### Follow-up prompt

> _To be added (if needed)._

### What was lacking after the first prompt

_To be added (one sentence)._

## Problem 10: Reflection

### Prompt

> _To be added._

### Follow-up prompt

> _To be added (if needed)._

### What was lacking after the first prompt

_To be added (one sentence)._

## Problem 11: Submit to GitHub

### Prompt

> _To be added._

### Follow-up prompt

> _To be added (if needed)._

### What was lacking after the first prompt

_To be added (one sentence)._
