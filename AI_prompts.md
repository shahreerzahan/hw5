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

> Also add a short mcp_server/README.md saying what the server is for, which database file it uses, and the three tools.
>
> Commit and push.

### What was lacking after the first prompt

The first prompt didn't ask for any documentation, so the server folder had no README explaining what the server does, which database it uses, or its tools.

## Problem 4: Add the MCP server to vibe coder and test each tool

### Prompt

> Problem 4: Add the MCP Server to Vibe Coder
>
> Add my MCP server to this project so you can call its tools. Save the connection in .mcp.json at the project root. It should run mcp_server/server.py using the Python in my .venv. Commit and push.

### Follow-up prompt

> is mcp server connected?

> Now test each of my three MCP tools by actually calling them through the MCP server:
>
> 1. check_stock for CC-TEE-WHITE size S
> 2. get_vendor_invoices for vendor 1
> 3. get_lease for lease 1
>
> Save the evidence in output/mcp_smoke.json. For each tool include: the prompt I asked, the tool name, and the tool output.
>
> Double-check that the outputs match the values in data/campus_customs_new.db.
>
> Commit and push.

### What was lacking after the first prompt

The server was saved in .mcp.json but wasn't live in the session yet, so I had to reload the session and check that the AI could actually call its tools.

## Problem 5: Build the agent team and grow the MCP tools

### Prompt

> Problem 5: Build the agent team and grow the MCP tools
>
> Build the agent team for Campus Customs using PydanticAI: Boss, Inventory, Accounting, Facilities, and Customer Service. Any agent can delegate work to any other agent (full connectivity), so give each agent a way to ask the others for help.
>
> Roles:
> - Boss: reads each ticket, decides who should work on it, and makes the final call
> - Inventory: checks stock by SKU and size, spots shortfalls, and finds which vendor can restock
> - Accounting: watches cash and invoices, checks margins, and prepares payments or purchase orders for human approval
> - Facilities: handles the shop space side, like leases and rent
> - Customer Service: drafts messages for customers (drafts only, never sent)
>
> Put one prompt file per agent in backend/prompts/: boss.md, inventory.md, accounting.md, facilities.md, customer_service.md. Make each prompt detailed: the agent's job, its scope, when to delegate, and the shop rules it needs (desk.date_today is "today" for overdue checks, vendor lead times come from vendors, a vendor won't ship while it has an open unpaid invoice, every payment needs human approval, never go below zero cash, no real emails or vendor calls).
>
> Put data types in backend/models.py and the agent code under backend/. Use my PORTKEY_API_KEY and only gpt-6-luna for every agent.
>
> The agents must get all shop data through my MCP server, not a separate database layer. Add the MCP tools they need for the tickets, like: get the desk date, get a ticket, get the cash balance, prepare a payment or purchase order (saved as waiting for approval, no cash moves yet), save a customer message draft, and mark a ticket resolved. The pay step must refuse if there isn't enough cash.
>
> Make the agents append to output/audit_trail.json for every agent step (time, agent, tool, short args and result, stop reason). Never wipe the file.
>
> In output/harness.md, list each agent and each MCP tool with the table it uses, and add a short safety section: guardrails for real customers and real money, plus limits to keep token use down (like max steps per agent and max delegation depth). Update mcp_server/README.md so the tool list matches.
>
> Test it quickly on one ticket to make sure the agents talk to each other, then reset data/campus_customs_new.db back to the original. Commit and push.

### Follow-up prompt

> Restart claude for the new tools.

### What was lacking after the first prompt

The new MCP tools were written to server.py, but the vibe coder's MCP connection was still running the old 3-tool server, so it had to be reconnected to see them.

## Problem 6: Plan the three tickets

### Prompt

> Problem 6: planning the three tickets
>
> Build 'output/desk_tickets.html', a page I can double-click, with one tab per ticket (101, 102, 103), plus empty Cash and Reflection tabs that say "coming later".
>
> On each ticket tab, add an Expected section with my plan below, and leave an empty Actual section for after I run the agents. Don't run the agents yet.
>
> Ticket 101 (customer order, white tee size S, 0 in stock):
> Boss calls Inventory first, because the problem is that we have no stock. Inventory finds Bulldog Print Co can restock (5 lead days) but sees they won't ship because invoice 501 ($840) is still unpaid, so Inventory asks Accounting for help. Accounting checks cash and prepares the $840 payment for human approval, then prepares a purchase order for the tees. Boss then asks Customer Service to draft a message to the customer with the expected delivery time. Facilities is not needed.
>
> Tools: get ticket, check_stock, get_vendor_invoices, get cash balance, prepare payment, prepare purchase order, save customer draft, mark resolved.
>
> Ticket 102 (rent notice, $2,400 to Elm City Properties, due 09-02):
> Boss calls Facilities first, because rent is a lease issue. Facilities checks the lease and compares the due date to desk.date_today to see if it's overdue, then asks Accounting to pay. Accounting checks that checking ($3,400) covers it and prepares the $2,400 payment for human approval. Inventory and Customer Service are not needed, since the landlord isn't a customer.
>
> Tools: get ticket, get desk date, get_lease, get cash balance, prepare payment, mark resolved.
>
> Ticket 103 (price override, 20 navy hoodies size M, only 8 in stock):
> Boss calls Inventory first, because we can't promise a price before knowing we can fill the order. Inventory finds we're 12 short and checks which vendor can restock. Inventory or Boss asks Accounting to check the margin on the requested discount against the $22 cost, and whether we have cash for 12 more (about $264), which may be tight after rent and the invoice. Boss makes the final call, then Customer Service drafts a reply to the customer (approve, counteroffer, or partial order of 8 now). Facilities is not needed.
>
> Tools: get ticket, check_stock, get_vendor_invoices, get cash balance, maybe prepare purchase order, save customer draft, mark resolved.
>
> Commit and push.

### Follow-up prompt

> _To be added (if needed)._

### What was lacking after the first prompt

_To be added (one sentence)._

## Problem 7: Backend routes

### Prompt

> Problem 7: Backend Routes
>
> My React dashboard (next problem) needs a backend it can call. In backend/main.py, use FastAPI and add routes that:
>
> - Return the three tickets and whether each is open or resolved
> - Take a ticket id and run the agent team on that ticket
> - Return recent agent events (what each agent said and which tools they used) so the board can refresh
> - Approve a payment or purchase after a human clicks approve. The agents only prepare the pay; this route is what actually changes cash and updates the payments, invoices, and cash_accounts tables. It must refuse if there isn't enough cash.
> - Return the current checking balance from 'cash_accounts'
> - Reset data/campus_customs_new.db back to the original values for a fresh run
>
> Make sure it starts from the backend/ folder with: uvicorn main:app --reload --port 8000
>
> In output/harness.md, list each route in one line (URL and what it does).
>
> Quickly test the routes that don't run agents (tickets, balance, reset), then commit and push.

### Follow-up prompt

> _To be added (if needed)._

### What was lacking after the first prompt

_To be added (one sentence)._

## Problem 8: Agent dashboard

### Prompt

> Problem 8: Agent Dashboard
>
> Build the dashboard in frontend/ with React + Vite + TypeScript. It should call the routes from Problem 7 at http://localhost:8000, and the backend should allow http://localhost:5173 so the browser can call it.
>
> The board should:
> - List all three tickets
> - Let me pick one ticket and start the agent team on it
> - Show each agent and what they are saying / doing while the ticket runs
> - Mark a ticket resolved when the run finishes
> - Show a short summary of what each agent did on that ticket
> - Let a human approve a pay or purchase when asked
> - Show the checking balance (it should drop after an approved pay)
>
> Design: keep the Campus Customs feel from my earlier homework (Yale blue and white), but make it minimalist with a Bauhaus and Scandinavian style:
> - Off-white background, lots of white space, a clean grid layout, thin lines, flat colors, no heavy shadows or gradients
> - A clean geometric sans-serif font, with big bold headings
> - Yale blue as the main color, plus one small warm accent (like mustard yellow) used only for things that need attention, like the Approve button
> - Each agent gets its own simple shape and color (for example Boss = blue circle, Inventory = square, Accounting = triangle, Facilities = half circle, Customer Service = rounded square), so you can tell who is talking at a glance
> - The checking balance shown as one large, simple number
> - Resolved tickets get a calm, clear "resolved" mark
> - Small, smooth animations only (like new agent messages fading in)
>
> Start it with npm run dev and show me it working with the backend.
>
> Then write output/design.md: what I chose for the layout, how agents look different, how resolved tickets and cash show up, and why. Include the creative choices that make it feel special and enjoyable to use.
>
> Commit and push.

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
